import json
import unittest
from unittest.mock import patch

import httpx
import openai
from babeldoc.babeldoc_exception.BabelDOCException import ContentFilterError
from babeldoc.translator.translator import OpenAITranslator


class OpenAITranslatorTests(unittest.TestCase):
    """Exercise the actual SDK serialization without sending network requests."""

    def setUp(self):
        cache_patch = patch("babeldoc.translator.translator.TranslationCache")
        self.cache = cache_patch.start().return_value
        self.cache.get.return_value = None
        self.addCleanup(cache_patch.stop)
        rate_patch = patch("babeldoc.translator.translator._translate_rate_limiter")
        rate_patch.start()
        self.addCleanup(rate_patch.stop)
        self.requests = []
        self.response_status = 200
        self.response = self.completion()

    @staticmethod
    def completion(content=" 譯文 ", finish_reason="stop", refusal=None):
        return {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 0,
            "model": "test",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": finish_reason,
                    "message": {
                        "role": "assistant",
                        "content": content,
                        "refusal": refusal,
                    },
                },
            ],
            "usage": {
                "prompt_tokens": 3,
                "completion_tokens": 2,
                "total_tokens": 5,
            },
        }

    def make_translator(self, model="gpt-6-luna", **kwargs):
        def respond(request):
            self.requests.append(json.loads(request.content))
            return httpx.Response(self.response_status, json=self.response)

        http_client = httpx.Client(
            transport=httpx.MockTransport(respond),
            trust_env=False,
        )
        client = openai.OpenAI(
            api_key="test-key",
            base_url="https://translator.invalid/v1",
            http_client=http_client,
        )
        self.addCleanup(client.close)
        with (
            patch(
                "babeldoc.translator.translator.httpx.Client", return_value=http_client
            ),
            patch("babeldoc.translator.translator.openai.OpenAI", return_value=client),
        ):
            translator = OpenAITranslator(
                "en",
                "zh-TW",
                model,
                api_key="test-key",
                **kwargs,
            )
        return translator

    def test_reasoning_models_omit_temperature_in_both_paths(self):
        for model in (
            "o1",
            "o1-mini",
            "o3",
            "o3-pro",
            "o4-mini",
            "gpt-5",
            "gpt-5.1",
            "gpt-5.2",
            "gpt-6",
            "gpt-6-luna",
        ):
            for method in ("translate", "llm_translate"):
                with self.subTest(model=model, method=method):
                    translator = self.make_translator(model)
                    self.assertEqual(getattr(translator, method)("Hello"), "譯文")
                    self.assertNotIn("temperature", self.requests[-1])
                    self.assertEqual(self.requests[-1]["model"], model)

    def test_legacy_chat_and_unrelated_models_keep_temperature(self):
        for model in (
            "gpt-4o-mini",
            "gpt-5-chat-latest",
            "gpt-6-chat-latest",
            "deepseek-chat",
            "custom-gpt-5",
            "gpt-50",
            "o10",
        ):
            for method in ("translate", "llm_translate"):
                with self.subTest(model=model, method=method):
                    translator = self.make_translator(model)
                    getattr(translator, method)("Hello")
                    self.assertEqual(self.requests[-1]["temperature"], 0)

    def test_no_temperature_option_still_works_for_legacy_models(self):
        translator = self.make_translator("gpt-4o-mini", send_temperature=False)
        for method in ("translate", "llm_translate"):
            getattr(translator, method)("Hello")
            self.assertNotIn("temperature", self.requests[-1])

    def test_default_llm_budgets_include_reasoning_tokens(self):
        for model in ("gpt-6-luna", "gpt-5.1", "o3", "o4-mini"):
            with self.subTest(model=model):
                translator = self.make_translator(model)
                translator.llm_translate("Hello")
                self.assertEqual(self.requests[-1]["max_completion_tokens"], 16384)
                self.assertNotIn("max_tokens", self.requests[-1])
        for model in ("gpt-4o-mini", "gpt-5-chat-latest", "deepseek-chat"):
            with self.subTest(model=model):
                translator = self.make_translator(model)
                translator.llm_translate("Hello")
                self.assertEqual(self.requests[-1]["max_tokens"], 2048)
                self.assertNotIn("max_completion_tokens", self.requests[-1])

    def test_plain_translation_preserves_unlimited_default_budget(self):
        for model in ("gpt-6-luna", "gpt-4o-mini", "deepseek-chat"):
            with self.subTest(model=model):
                translator = self.make_translator(model)
                translator.translate("Hello")
                self.assertNotIn("max_tokens", self.requests[-1])
                self.assertNotIn("max_completion_tokens", self.requests[-1])

    def test_explicit_budget_is_shared_by_both_translation_paths(self):
        for model, field in (
            ("gpt-6-luna", "max_completion_tokens"),
            ("gpt-4o-mini", "max_completion_tokens"),
            ("o3-mini", "max_completion_tokens"),
            ("deepseek-chat", "max_tokens"),
        ):
            for method in ("translate", "llm_translate"):
                with self.subTest(model=model, method=method):
                    translator = self.make_translator(model, max_completion_tokens=8192)
                    getattr(translator, method)("Hello")
                    self.assertEqual(self.requests[-1][field], 8192)
                    other_field = (
                        "max_tokens"
                        if field == "max_completion_tokens"
                        else "max_completion_tokens"
                    )
                    self.assertNotIn(other_field, self.requests[-1])

    def test_nonpositive_budget_is_rejected_before_client_creation(self):
        with (
            patch("babeldoc.translator.translator.openai.OpenAI") as client_factory,
            patch("babeldoc.translator.translator.httpx.Client") as http_factory,
        ):
            for budget in (0, -1):
                with self.subTest(budget=budget), self.assertRaises(ValueError):
                    OpenAITranslator(
                        "en",
                        "zh-TW",
                        "gpt-6-luna",
                        api_key="test-key",
                        max_completion_tokens=budget,
                    )
            client_factory.assert_not_called()
            http_factory.assert_not_called()

    def test_effective_completion_budget_distinguishes_cache_entries(self):
        for model, budget, expected in (
            ("gpt-6-luna", None, 16384),
            ("gpt-6-luna", 32768, 32768),
            ("gpt-4o-mini", 8192, 8192),
            ("deepseek-chat", 8192, 8192),
        ):
            with self.subTest(model=model, budget=budget):
                self.cache.add_params.reset_mock()
                self.make_translator(model, max_completion_tokens=budget)
                params = dict(
                    call.args for call in self.cache.add_params.call_args_list
                )
                self.assertEqual(params["max_completion_tokens"], expected)
        self.cache.add_params.reset_mock()
        self.make_translator("gpt-4o-mini")
        params = dict(call.args for call in self.cache.add_params.call_args_list)
        self.assertNotIn("max_completion_tokens", params)

    def test_openai_reasoning_effort_uses_top_level_api_field(self):
        for model in ("gpt-6-luna", "gpt-5.1", "gpt-4o-mini", "o3-mini"):
            for method in ("translate", "llm_translate"):
                with self.subTest(model=model, method=method):
                    translator = self.make_translator(model, reasoning="low")
                    getattr(translator, method)("Hello")
                    self.assertEqual(self.requests[-1]["reasoning_effort"], "low")
                    self.assertNotIn("reasoning", self.requests[-1])

    def test_third_party_reasoning_and_thinking_payloads_are_preserved(self):
        translator = self.make_translator(
            "deepseek-chat",
            reasoning="high",
            thinking="enabled",
        )
        for method in ("translate", "llm_translate"):
            getattr(translator, method)("Hello")
            self.assertEqual(self.requests[-1]["reasoning"], {"effort": "high"})
            self.assertEqual(self.requests[-1]["thinking"], {"type": "enabled"})
            self.assertNotIn("reasoning_effort", self.requests[-1])

    def test_json_mode_allows_missing_rate_parameters(self):
        translator = self.make_translator(enable_json_mode_if_requested=True)
        self.assertEqual(
            translator.llm_translate("Hello", rate_limit_params=None), "譯文"
        )
        self.assertNotIn("response_format", self.requests[-1])
        self.response = self.completion('{"translation": "譯文"}')
        self.assertEqual(
            translator.llm_translate(
                "JSON request",
                rate_limit_params={"request_json_mode": True},
            ),
            '{"translation": "譯文"}',
        )
        self.assertEqual(self.requests[-1]["response_format"], {"type": "json_object"})

    def test_none_probe_does_not_send_request(self):
        translator = self.make_translator(enable_json_mode_if_requested=True)
        self.assertIsNone(translator.do_llm_translate(None))
        self.assertEqual(self.requests, [])

    def test_valid_translation_is_trimmed_counted_and_cached(self):
        for method in ("translate", "llm_translate"):
            with self.subTest(method=method):
                self.cache.set.reset_mock()
                translator = self.make_translator()
                self.assertEqual(getattr(translator, method)("Hello"), "譯文")
                self.cache.set.assert_called_once_with("Hello", "譯文")
                self.assertEqual(translator.token_count.value, 5)
                self.assertEqual(translator.prompt_token_count.value, 3)
                self.assertEqual(translator.completion_token_count.value, 2)

    def test_missing_and_empty_outputs_are_rejected_without_cache(self):
        responses = [
            self.completion(None),
            self.completion(""),
            self.completion(" \n "),
        ]
        missing_content = self.completion()
        del missing_content["choices"][0]["message"]["content"]
        responses.append(missing_content)
        missing_choices = self.completion()
        missing_choices["choices"] = []
        responses.append(missing_choices)
        for method in ("translate", "llm_translate"):
            for response in responses:
                with self.subTest(method=method, response=response):
                    self.cache.set.reset_mock()
                    self.response = response
                    translator = self.make_translator()
                    with self.assertRaises(ValueError):
                        getattr(translator, method)("Hello")
                    self.cache.set.assert_not_called()

    def test_truncated_translation_is_rejected_without_cache(self):
        self.response = self.completion(
            "Incomplete translation", finish_reason="length"
        )
        for method in ("translate", "llm_translate"):
            with self.subTest(method=method):
                translator = self.make_translator()
                with self.assertRaises(ValueError):
                    getattr(translator, method)("Hello")
                self.cache.set.assert_not_called()
                self.assertEqual(translator.token_count.value, 5)

    def test_filtered_or_refused_translation_is_rejected_without_cache(self):
        for response in (
            self.completion(None, finish_reason="content_filter"),
            self.completion("Partial translation", refusal="Cannot fulfill request"),
        ):
            for method in ("translate", "llm_translate"):
                with self.subTest(method=method, response=response):
                    self.response = response
                    translator = self.make_translator()
                    with self.assertRaises(ContentFilterError):
                        getattr(translator, method)("Hello")
                    self.cache.set.assert_not_called()

    def test_unsupported_parameters_fail_once_without_rate_limit_retries(self):
        self.response_status = 400
        self.response = {
            "error": {
                "message": "Unsupported parameter: temperature",
                "type": "invalid_request_error",
                "param": "temperature",
                "code": "unsupported_parameter",
            },
        }
        for method in ("translate", "llm_translate"):
            with self.subTest(method=method):
                self.requests.clear()
                translator = self.make_translator()
                with self.assertRaises(openai.BadRequestError):
                    getattr(translator, method)("Hello")
                self.assertEqual(len(self.requests), 1)
                self.cache.set.assert_not_called()


if __name__ == "__main__":
    unittest.main()
