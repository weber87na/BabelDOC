"""ChatGPT subscription access through the official Codex app-server protocol.

Only this module manages the child process; OAuth tokens remain owned by Codex.
It intentionally has no PDF or OpenAI SDK dependencies.
"""

import argparse
import contextlib
import json
import os
import platform
import queue
import shutil
import subprocess
import tempfile
import threading
import time
import webbrowser
from pathlib import Path


class ChatGPTError(RuntimeError):
    pass


def resolve_executable(command):
    executable = shutil.which(command)
    if not executable:
        raise ChatGPTError("找不到 Codex CLI，請先執行 npm install -g @openai/codex")
    path = Path(executable).resolve()
    if path.suffix.lower() in (".cmd", ".bat", ".ps1"):
        # Windows npm shims are scripts, not CreateProcess executables. Locate
        # the package's native binary instead of invoking a command shell.
        arch = (
            "aarch64"
            if platform.machine().lower() in ("arm64", "aarch64")
            else "x86_64"
        )
        package_arch = "arm64" if arch == "aarch64" else "x64"
        roots = [
            path.parent / "node_modules" / "@openai",
            path.parent.parent / "@openai",
        ]
        for root in roots:
            for package in (f"codex-win32-{package_arch}", "codex"):
                for folder in ("bin", "codex"):
                    native = (
                        root
                        / package
                        / "vendor"
                        / f"{arch}-pc-windows-msvc"
                        / folder
                        / "codex.exe"
                    )
                    if native.is_file():
                        return str(native)
        raise ChatGPTError(
            "無法解析 Windows Codex 啟動器；請以 --chatgpt-codex-path 指定原生 codex.exe"
        )
    return str(path)


class ChatGPTClient:
    def __init__(self, executable="codex", timeout=600):
        if timeout <= 0:
            raise ValueError("ChatGPT timeout must be positive")
        self.executable = executable
        self.timeout = timeout
        self.process = None
        self.workdir = None
        self.messages = queue.Queue()
        self.pending = []
        self.request_id = 0

    def __enter__(self):
        executable = resolve_executable(self.executable)
        # A dedicated Codex profile avoids inheriting API auth, MCP servers, skills,
        # or project configuration from the user's coding sessions.
        profile = Path.home() / ".babeldoc" / "codex"
        profile.mkdir(parents=True, exist_ok=True, mode=0o700)
        env = os.environ.copy()
        env["CODEX_HOME"] = str(profile)
        for key in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "CODEX_API_KEY"):
            env.pop(key, None)
        self.workdir = tempfile.TemporaryDirectory(prefix="babeldoc-chatgpt-")
        try:
            self.process = subprocess.Popen(  # noqa: S603
                [
                    executable,
                    "app-server",
                    "-c",
                    'forced_login_method="chatgpt"',
                    "-c",
                    'model_provider="openai"',
                    "-c",
                    'web_search="disabled"',
                    "-c",
                    "features.shell_tool=false",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                cwd=self.workdir.name,
                env=env,
            )
            self.reader = threading.Thread(target=self._read, daemon=True)
            self.reader.start()
            self.request(
                "initialize",
                {
                    "clientInfo": {
                        "name": "babeldoc",
                        "title": "BabelDOC",
                        "version": "0.6.4",
                    }
                },
            )
            self.send({"method": "initialized"})
            return self
        except BaseException:
            self.close()
            raise

    def __exit__(self, *_):
        self.close()

    def close(self):
        if self.process:
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=5)
            if hasattr(self, "reader"):
                self.reader.join(timeout=2)
            for stream in (self.process.stdin, self.process.stdout):
                if stream:
                    stream.close()
        if self.workdir:
            self.workdir.cleanup()

    def _read(self):
        try:
            for line in self.process.stdout:
                try:
                    self.messages.put(json.loads(line))
                except ValueError:
                    self.messages.put(ChatGPTError("Codex returned invalid JSON"))
                    return
        finally:
            self.messages.put(
                ChatGPTError("Codex app-server 已停止，請檢查 CLI 版本與登入狀態")
            )

    def send(self, message):
        try:
            self.process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
            self.process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise ChatGPTError("Codex app-server connection closed") from exc

    def receive(self, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ChatGPTError("ChatGPT request timed out; no API fallback was used")
        try:
            message = self.messages.get(timeout=remaining)
        except queue.Empty as exc:
            raise ChatGPTError(
                "ChatGPT request timed out; no API fallback was used"
            ) from exc
        if isinstance(message, Exception):
            raise message
        if "method" in message and "id" in message:
            self.send(
                {
                    "id": message["id"],
                    "error": {
                        "code": -32601,
                        "message": "BabelDOC does not execute tools or approve actions",
                    },
                }
            )
            raise ChatGPTError(
                "Unexpected Codex tool/approval request; translation stopped"
            )
        return message

    def request(self, method, params=None):
        self.request_id += 1
        request_id = self.request_id
        self.send({"id": request_id, "method": method, "params": params or {}})
        deadline = time.monotonic() + self.timeout
        while True:
            message = self.receive(deadline)
            if message.get("id") == request_id:
                if "error" in message:
                    # Do not expose remote errors which could echo document/auth data.
                    raise ChatGPTError(
                        f"Codex {method} failed (code {message['error'].get('code')}); check login, quota and CLI version"
                    )
                return message["result"]
            self.pending.append(message)

    def events(self, deadline):
        while True:
            yield self.pending.pop(0) if self.pending else self.receive(deadline)

    def require_chatgpt(self):
        account = self.request("account/read", {"refreshToken": True}).get("account")
        if not account or account.get("type") != "chatgpt":
            raise ChatGPTError(
                "請先執行 babeldoc --chatgpt-login；此模式只接受 ChatGPT 登入，不使用 API Key"
            )
        return account

    def login(self, device=False):
        result = self.request(
            "account/login/start",
            {
                "type": "chatgptDeviceCode" if device else "chatgpt",
            },
        )
        if device:
            print(
                f"開啟 {result['verificationUrl']} 並輸入 {result['userCode']}",
                flush=True,
            )
        else:
            print(f"請在瀏覽器登入：{result['authUrl']}", flush=True)
            webbrowser.open(result["authUrl"])
        try:
            for message in self.events(time.monotonic() + self.timeout):
                params = message.get("params", {})
                if (
                    message.get("method") == "account/login/completed"
                    and params.get("loginId") == result["loginId"]
                ):
                    if not params.get("success"):
                        raise ChatGPTError("ChatGPT 登入未完成，請重試")
                    self.require_chatgpt()
                    print("ChatGPT 登入成功。", flush=True)
                    return
        except BaseException:
            with contextlib.suppress(Exception):
                self.request("account/login/cancel", {"loginId": result["loginId"]})
            raise

    def models(self):
        self.require_chatgpt()
        models = []
        cursor = None
        while True:
            page = self.request(
                "model/list", {"limit": 100, "cursor": cursor, "includeHidden": False}
            )
            models.extend(page["data"])
            cursor = page.get("nextCursor")
            if not cursor:
                return models

    def translate(self, text, model, effort):
        self.require_chatgpt()
        thread = self.request(
            "thread/start",
            {
                "model": model,
                "modelProvider": "openai",
                "ephemeral": True,
                "cwd": self.workdir.name,
                "approvalPolicy": "never",
                "sandbox": "read-only",
                "developerInstructions": "You are a document translation engine. Follow the translation or term extraction request. Preserve all placeholders. Return only the requested result. Never use tools, read files, run commands, or browse the web.",
            },
        )
        thread_id = thread["thread"]["id"]
        turn = self.request(
            "turn/start",
            {
                "threadId": thread_id,
                "model": model,
                "effort": effort,
                "input": [{"type": "text", "text": text}],
            },
        )
        turn_id = turn["turn"]["id"]
        answers = []
        usage = {}
        for message in self.events(time.monotonic() + self.timeout):
            params = message.get("params", {})
            if params.get("threadId") != thread_id:
                continue
            method = message.get("method")
            if method == "thread/tokenUsage/updated":
                usage = params.get("tokenUsage", {}).get("total", {})
            if params.get("turnId", turn_id) != turn_id:
                continue
            if method == "item/completed":
                item = params["item"]
                if item["type"] == "agentMessage" and item.get("phase") in (
                    None,
                    "final_answer",
                ):
                    answers.append(item["text"])
            if method == "turn/completed" and params["turn"]["id"] == turn_id:
                if params["turn"]["status"] != "completed":
                    raise ChatGPTError(
                        "ChatGPT 翻譯失敗或中斷；請檢查方案額度、模型存取權及連線"
                    )
                answer = "\n".join(answers).strip()
                if not answer:
                    raise ChatGPTError("ChatGPT returned an empty translation")
                return answer, usage


def select_model(models, model=None, effort=None):
    if not models:
        raise ChatGPTError("此帳號目前沒有可用模型")
    if model is None:
        selected = next((m for m in models if m.get("isDefault")), models[0])
    else:
        selected = next((m for m in models if model in (m["id"], m["model"])), None)
        if selected is None:
            raise ChatGPTError("模型不可用，請執行 --chatgpt-list-models 查看可用選項")
    supported = [e["reasoningEffort"] for e in selected["supportedReasoningEfforts"]]
    effort = effort or selected["defaultReasoningEffort"]
    if effort not in supported:
        raise ChatGPTError(
            f"此模型不支援推理強度 {effort}；可選：{', '.join(supported)}"
        )
    return selected["model"], effort


def add_arguments(parser):
    group = parser.add_argument_group("ChatGPT subscription (Codex OAuth)")
    group.add_argument(
        "--chatgpt",
        action="store_true",
        help="Translate using ChatGPT subscription access",
    )
    actions = group.add_mutually_exclusive_group()
    actions.add_argument(
        "--chatgpt-login", action="store_true", help="Sign in with ChatGPT"
    )
    actions.add_argument(
        "--chatgpt-logout",
        action="store_true",
        help="Sign out of BabelDOC's Codex profile",
    )
    actions.add_argument(
        "--chatgpt-list-models",
        action="store_true",
        help="List available models and reasoning efforts",
    )
    group.add_argument(
        "--chatgpt-device-auth",
        action="store_true",
        help="Use device-code login (with --chatgpt-login)",
    )
    group.add_argument(
        "--chatgpt-model",
        help="Model ID from --chatgpt-list-models; defaults to account default",
    )
    group.add_argument(
        "--chatgpt-reasoning", help="Reasoning effort supported by the selected model"
    )
    group.add_argument(
        "--chatgpt-codex-path", default="codex", help="Path to Codex CLI executable"
    )
    group.add_argument(
        "--chatgpt-timeout",
        type=float,
        default=600,
        help="Request/login timeout in seconds",
    )


def handle_action(args):
    if not any((args.chatgpt_login, args.chatgpt_logout, args.chatgpt_list_models)):
        return False
    with ChatGPTClient(args.chatgpt_codex_path, args.chatgpt_timeout) as client:
        if args.chatgpt_login:
            client.login(args.chatgpt_device_auth)
        elif args.chatgpt_logout:
            client.request("account/logout")
            print("已登出 BabelDOC 的 ChatGPT 帳號。")
        else:
            for model in client.models():
                efforts = ", ".join(
                    e["reasoningEffort"] for e in model["supportedReasoningEfforts"]
                )
                print(
                    f"{model['model']} | {model['displayName']} | {efforts} | default={model['defaultReasoningEffort']}"
                )
    return True


def cli():
    parser = argparse.ArgumentParser(
        description="BabelDOC ChatGPT authentication and model discovery"
    )
    add_arguments(parser)
    args = parser.parse_args()
    try:
        if not handle_action(args):
            parser.error(
                "請選擇 --chatgpt-login、--chatgpt-logout 或 --chatgpt-list-models"
            )
    except (ChatGPTError, ValueError, OSError) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    cli()
