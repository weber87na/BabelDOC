import argparse
import time
import unittest
from unittest.mock import patch

from babeldoc.translator.chatgpt_client import ChatGPTClient
from babeldoc.translator.chatgpt_client import ChatGPTError
from babeldoc.translator.chatgpt_client import add_arguments
from babeldoc.translator.chatgpt_client import select_model

MODELS = [
    {
        "id": "test",
        "model": "test-model",
        "displayName": "Test",
        "isDefault": True,
        "defaultReasoningEffort": "low",
        "supportedReasoningEfforts": [
            {"reasoningEffort": "low"},
            {"reasoningEffort": "high"},
        ],
    }
]


class ClientTests(unittest.TestCase):
    def test_models_validate_effort_and_alias(self):
        self.assertEqual(select_model(MODELS), ("test-model", "low"))
        self.assertEqual(select_model(MODELS, "test", "high"), ("test-model", "high"))
        for model, effort in [("missing", "low"), ("test", "max")]:
            with self.assertRaises(ChatGPTError):
                select_model(MODELS, model, effort)
        with self.assertRaises(ChatGPTError):
            select_model([])

    def test_api_auth_is_rejected(self):
        client = ChatGPTClient()
        for account in [None, {"type": "apiKey"}]:
            with patch.object(client, "request", return_value={"account": account}):
                with self.assertRaisesRegex(ChatGPTError, "API Key"):
                    client.require_chatgpt()

    def test_paginated_catalog(self):
        client = ChatGPTClient()
        with (
            patch.object(client, "require_chatgpt"),
            patch.object(
                client,
                "request",
                side_effect=[
                    {"data": MODELS, "nextCursor": "next"},
                    {"data": [], "nextCursor": None},
                ],
            ) as request,
        ):
            self.assertEqual(client.models(), MODELS)
            self.assertEqual(request.call_args.args[1]["cursor"], "next")

    def test_notifications_before_response_are_preserved(self):
        client = ChatGPTClient()
        event = {"method": "account/login/completed", "params": {"success": True}}
        client.messages.put(event)
        client.messages.put({"id": 1, "result": {"loginId": "login"}})
        with patch.object(client, "send"):
            self.assertEqual(
                client.request("account/login/start"), {"loginId": "login"}
            )
        self.assertEqual(next(client.events(time.monotonic() + 1)), event)

    def test_tool_requests_fail_closed(self):
        client = ChatGPTClient()
        client.messages.put(
            {"id": 7, "method": "item/commandExecution/requestApproval"}
        )
        with patch.object(client, "send") as send, self.assertRaises(ChatGPTError):
            client.receive(time.monotonic() + 1)
        self.assertIn("error", send.call_args.args[0])

    def test_timeout_and_crash(self):
        client = ChatGPTClient()
        with self.assertRaisesRegex(ChatGPTError, "timed out"):
            client.receive(time.monotonic() + 0.001)
        client.messages.put(ChatGPTError("crashed"))
        with self.assertRaisesRegex(ChatGPTError, "crashed"):
            client.receive(time.monotonic() + 1)

    def test_error_does_not_leak_remote_content(self):
        client = ChatGPTClient()
        client.messages.put(
            {"id": 1, "error": {"code": 401, "message": "secret document"}}
        )
        with patch.object(client, "send"), self.assertRaises(ChatGPTError) as exc:
            client.request("turn/start")
        self.assertNotIn("secret", str(exc.exception))

    def translation(self, status="completed", text="翻譯", phase="final_answer"):
        client = ChatGPTClient()
        client.workdir = argparse.Namespace(name="/fake/work")
        events = [
            {
                "method": "item/completed",
                "params": {
                    "threadId": "other",
                    "item": {"type": "agentMessage", "text": "wrong"},
                },
            },
            {
                "method": "item/completed",
                "params": {
                    "threadId": "t",
                    "turnId": "u",
                    "item": {
                        "type": "agentMessage",
                        "text": "thinking",
                        "phase": "commentary",
                    },
                },
            },
            {
                "method": "thread/tokenUsage/updated",
                "params": {
                    "threadId": "t",
                    "tokenUsage": {"total": {"totalTokens": 12}},
                },
            },
            {
                "method": "item/completed",
                "params": {
                    "threadId": "t",
                    "turnId": "u",
                    "item": {"type": "agentMessage", "text": text, "phase": phase},
                },
            },
            {
                "method": "turn/completed",
                "params": {"threadId": "t", "turn": {"id": "u", "status": status}},
            },
        ]
        with (
            patch.object(client, "require_chatgpt"),
            patch.object(
                client,
                "request",
                side_effect=[
                    {"thread": {"id": "t"}},
                    {"turn": {"id": "u"}},
                ],
            ) as request,
            patch.object(client, "events", return_value=iter(events)),
        ):
            result = client.translate("input", "test-model", "high")
            self.assertEqual(request.call_args_list[1].args[1]["effort"], "high")
            self.assertTrue(request.call_args_list[0].args[1]["ephemeral"])
            return result

    def test_translation_filters_commentary_and_collects_usage(self):
        self.assertEqual(self.translation(), ("翻譯", {"totalTokens": 12}))
        self.assertEqual(self.translation(phase=None)[0], "翻譯")

    def test_failed_and_empty_translation_not_returned(self):
        for status, text in [
            ("failed", "partial"),
            ("interrupted", "partial"),
            ("completed", ""),
        ]:
            with self.assertRaises(ChatGPTError):
                self.translation(status, text)

    def test_login_waits_for_matching_id(self):
        client = ChatGPTClient()
        client.pending = [
            {
                "method": "account/login/completed",
                "params": {"loginId": "old", "success": False},
            },
            {
                "method": "account/login/completed",
                "params": {"loginId": "new", "success": True},
            },
        ]
        with (
            patch.object(
                client,
                "request",
                return_value={
                    "loginId": "new",
                    "verificationUrl": "https://auth.openai.com/codex/device",
                    "userCode": "TEST",
                },
            ),
            patch.object(client, "require_chatgpt") as check,
            patch("builtins.print"),
        ):
            client.login(device=True)
            check.assert_called_once()

    def test_action_arguments_exclusive(self):
        parser = argparse.ArgumentParser()
        add_arguments(parser)
        with patch("sys.stderr"), self.assertRaises(SystemExit):
            parser.parse_args(["--chatgpt-login", "--chatgpt-logout"])

    def test_missing_executable_and_invalid_timeout(self):
        with patch("shutil.which", return_value=None), self.assertRaises(ChatGPTError):
            with ChatGPTClient():
                pass
        with self.assertRaises(ValueError):
            ChatGPTClient(timeout=0)


if __name__ == "__main__":
    unittest.main()
