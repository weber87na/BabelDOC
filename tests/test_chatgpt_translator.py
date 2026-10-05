import unittest
from unittest.mock import patch

from babeldoc.translator.chatgpt import ChatGPTTranslator
from babeldoc.translator.chatgpt_client import ChatGPTError
from babeldoc.translator.translator import OpenAITranslator

CATALOG = [
    {
        "id": "test",
        "model": "test",
        "defaultReasoningEffort": "low",
        "supportedReasoningEfforts": [
            {"reasoningEffort": "low"},
            {"reasoningEffort": "high"},
        ],
    }
]


class TranslatorTests(unittest.TestCase):
    def setUp(self):
        self.cache_patch = patch("babeldoc.translator.translator.TranslationCache")
        self.cache = self.cache_patch.start().return_value
        self.cache.get.return_value = None
        self.addCleanup(self.cache_patch.stop)
        self.client_patch = patch("babeldoc.translator.chatgpt.ChatGPTClient")
        self.client = self.client_patch.start().return_value.__enter__.return_value
        self.addCleanup(self.client_patch.stop)
        self.client.models.return_value = CATALOG
        self.client.translate.return_value = (
            "譯文",
            {"totalTokens": 5, "inputTokens": 3, "outputTokens": 2},
        )
        self.rate_patch = patch(
            "babeldoc.translator.translator._translate_rate_limiter"
        )
        self.rate_patch.start()
        self.addCleanup(self.rate_patch.stop)

    def test_no_api_constructor_and_cache_parameters(self):
        with patch.object(
            OpenAITranslator, "__init__", side_effect=AssertionError("API called")
        ):
            translator = ChatGPTTranslator("en", "zh-TW", reasoning="high")
            self.assertEqual(translator.translate("Hello"), "譯文")
        params = dict(call.args for call in self.cache.add_params.call_args_list)
        self.assertEqual(params["reasoning"], "high")
        self.assertEqual(params["model"], "test")
        self.assertEqual(translator.token_count.value, 5)
        self.assertEqual(translator.prompt_token_count.value, 3)
        self.assertEqual(translator.completion_token_count.value, 2)
        self.cache.set.assert_called_once_with("Hello", "譯文")
        self.assertIn("zh-TW", self.client.translate.call_args.args[0])

    def test_cache_hit_does_not_generate(self):
        translator = ChatGPTTranslator("en", "zh-TW")
        self.cache.get.return_value = "快取"
        self.assertEqual(translator.translate("Hello"), "快取")
        self.client.translate.assert_not_called()

    def test_failure_is_not_cached_or_sent_to_api(self):
        translator = ChatGPTTranslator("en", "zh-TW")
        self.client.translate.side_effect = ChatGPTError("quota exceeded")
        with (
            patch.object(
                OpenAITranslator,
                "do_translate",
                side_effect=AssertionError("API called"),
            ),
            self.assertRaises(ChatGPTError),
        ):
            translator.translate("Hello")
        self.cache.set.assert_not_called()

    def test_json_validation_and_none_probe(self):
        translator = ChatGPTTranslator(
            "en", "zh-TW", enable_json_mode_if_requested=True
        )
        self.assertIsNone(translator.do_llm_translate(None))
        for answer in ["```json\n{}\n```", "[]", "invalid"]:
            self.client.translate.return_value = (answer, {})
            with self.assertRaises(ChatGPTError):
                translator.llm_translate(
                    "terms", rate_limit_params={"request_json_mode": True}
                )
        self.cache.set.assert_not_called()
        self.client.translate.return_value = ('{"terms": []}', {})
        self.assertEqual(
            translator.llm_translate(
                "terms", rate_limit_params={"request_json_mode": True}
            ),
            '{"terms": []}',
        )
        self.client.translate.return_value = ("normal", {})
        self.assertEqual(translator.do_llm_translate("normal", None), "normal")

    def test_placeholders_match_existing_pipeline(self):
        translator = ChatGPTTranslator("en", "zh-TW")
        self.assertEqual(translator.get_formular_placeholder(1)[0], "{v1}")
        self.assertEqual(
            translator.get_rich_text_left_placeholder(1)[0], "<style id='1'>"
        )


if __name__ == "__main__":
    unittest.main()
