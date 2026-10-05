"""BabelDOC translator using ChatGPT subscription authentication."""

import json
import threading

from babeldoc.translator.chatgpt_client import ChatGPTClient
from babeldoc.translator.chatgpt_client import ChatGPTError
from babeldoc.translator.chatgpt_client import select_model
from babeldoc.translator.translator import BaseTranslator
from babeldoc.translator.translator import OpenAITranslator
from babeldoc.utils.atomic_integer import AtomicInteger


class ChatGPTTranslator(OpenAITranslator):
    # Reuse prompt/placeholder conventions, never the API constructor or requests.
    name = "chatgpt-codex"

    def __init__(
        self,
        lang_in,
        lang_out,
        model=None,
        reasoning=None,
        ignore_cache=False,
        codex_path="codex",
        timeout=600,
        enable_json_mode_if_requested=False,
    ):
        BaseTranslator.__init__(self, lang_in, lang_out, ignore_cache)
        self.codex_path = codex_path
        self.timeout = timeout
        self.enable_json_mode_if_requested = enable_json_mode_if_requested
        self.lock = threading.Lock()
        with ChatGPTClient(codex_path, timeout) as client:
            self.model, self.reasoning = select_model(client.models(), model, reasoning)
        for name in (
            "token_count",
            "prompt_token_count",
            "completion_token_count",
            "cache_hit_prompt_token_count",
        ):
            setattr(self, name, AtomicInteger())
        self.add_cache_impact_parameters("model", self.model)
        self.add_cache_impact_parameters("reasoning", self.reasoning)
        self.add_cache_impact_parameters("prompt", self.prompt(""))
        self.add_cache_impact_parameters("json_mode", enable_json_mode_if_requested)
        self.add_cache_impact_parameters("adapter_version", 1)

    def _generate(self, text, json_mode=False):
        if json_mode:
            text += "\nReturn one valid JSON object only, without Markdown fences."
        # Serialize requests: document workers must not flood subscription limits.
        # Each child has one ephemeral thread and is closed even on timeout/error.
        with self.lock, ChatGPTClient(self.codex_path, self.timeout) as client:
            answer, usage = client.translate(text, self.model, self.reasoning)
        for attribute, key in (
            ("token_count", "totalTokens"),
            ("prompt_token_count", "inputTokens"),
            ("completion_token_count", "outputTokens"),
            ("cache_hit_prompt_token_count", "cachedInputTokens"),
        ):
            getattr(self, attribute).inc(usage.get(key, 0))
        if json_mode:
            try:
                value = json.loads(answer)
            except ValueError as exc:
                raise ChatGPTError(
                    "ChatGPT returned invalid JSON; response was not cached"
                ) from exc
            if not isinstance(value, dict):
                raise ChatGPTError("ChatGPT must return a JSON object")
        return answer

    def do_translate(self, text, rate_limit_params=None):
        return self._generate(
            "\n\n".join(message["content"] for message in self.prompt(text))
        )

    def do_llm_translate(self, text, rate_limit_params=None):
        if text is None:
            return None
        return self._generate(
            text,
            self.enable_json_mode_if_requested
            and (rate_limit_params or {}).get("request_json_mode", False),
        )
