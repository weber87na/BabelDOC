"""Exercise JSONL pipes and process cleanup without any account/network access."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from babeldoc.translator.chatgpt_client import ChatGPTClient
from babeldoc.translator.chatgpt_client import ChatGPTError
from babeldoc.translator.chatgpt_client import resolve_executable

SERVER = """
import json, sys
for line in sys.stdin:
    message = json.loads(line)
    if "id" not in message:
        continue
    result = {}
    if message["method"] == "account/read":
        result = {"account": {"type": "chatgpt"}}
    print(json.dumps({"id": message["id"], "result": result}), flush=True)
"""


class ProcessTests(unittest.TestCase):
    def test_pipe_handshake_auth_environment_and_cleanup(self):
        popen = subprocess.Popen
        calls = []
        with tempfile.TemporaryDirectory() as directory:

            def spawn(command, **kwargs):
                calls.append((command, kwargs.copy()))
                return popen([sys.executable, "-u", "-c", SERVER], **kwargs)

            with (
                patch(
                    "babeldoc.translator.chatgpt_client.resolve_executable",
                    return_value=sys.executable,
                ),
                patch("pathlib.Path.home", return_value=Path(directory)),
                patch("subprocess.Popen", side_effect=spawn),
                patch.dict(
                    "os.environ",
                    {
                        "OPENAI_API_KEY": "test-only",
                        "OPENAI_BASE_URL": "https://invalid.example",
                    },
                ),
            ):
                with ChatGPTClient(timeout=5) as client:
                    self.assertEqual(client.require_chatgpt()["type"], "chatgpt")
                    workdir = client.workdir.name
                    self.assertNotIn("OPENAI_API_KEY", calls[0][1]["env"])
                    self.assertNotIn("OPENAI_BASE_URL", calls[0][1]["env"])
                    self.assertEqual(
                        calls[0][1]["env"]["CODEX_HOME"],
                        str(Path(directory) / ".babeldoc" / "codex"),
                    )
                self.assertIsNotNone(client.process.poll())
                self.assertFalse(Path(workdir).exists())

    def test_failed_initialization_cleans_up_process(self):
        popen = subprocess.Popen
        children = []
        with tempfile.TemporaryDirectory() as directory:

            def spawn(_command, **kwargs):
                child = popen(
                    [sys.executable, "-u", "-c", "print('not json', flush=True)"],
                    **kwargs,
                )
                children.append(child)
                return child

            with (
                patch(
                    "babeldoc.translator.chatgpt_client.resolve_executable",
                    return_value=sys.executable,
                ),
                patch("pathlib.Path.home", return_value=Path(directory)),
                patch("subprocess.Popen", side_effect=spawn),
            ):
                with self.assertRaises(ChatGPTError):
                    with ChatGPTClient(timeout=5):
                        pass
                self.assertIsNotNone(children[0].poll())

    def test_windows_npm_shim_resolves_native_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            native = (
                root
                / "node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe"
            )
            native.parent.mkdir(parents=True)
            native.touch()
            with (
                patch("shutil.which", return_value=str(root / "codex.cmd")),
                patch("platform.machine", return_value="AMD64"),
            ):
                self.assertEqual(resolve_executable("codex"), str(native))
            native.unlink()
            with (
                patch("shutil.which", return_value=str(root / "codex.cmd")),
                self.assertRaises(ChatGPTError),
            ):
                resolve_executable("codex")


if __name__ == "__main__":
    unittest.main()
