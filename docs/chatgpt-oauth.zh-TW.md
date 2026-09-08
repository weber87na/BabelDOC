# 使用 ChatGPT 帳號翻譯 PDF

此 fork 新增 `--chatgpt` 翻譯模式，透過**官方 Codex CLI 的 App Server**進行 ChatGPT OAuth 登入。模型與推理強度由登入後的模型清單取得，不需要填 OpenAI API Key。這是命令列功能；BabelDOC 本身沒有新增圖形介面。

此模式使用 ChatGPT／Codex 訂閱方案的可用額度，仍受模型權限、速率與用量限制約束。它不是把 ChatGPT 訂閱轉成 OpenAI Platform API 額度，也不保證能使用 ChatGPT 網頁中的所有模型。

## 安裝此分支

需先安裝 Git、Node.js/npm、uv 與符合 BabelDOC 要求的 Python（3.10–3.13）。在 PowerShell、Linux 或 macOS 終端機執行：

```sh
git clone --branch feat/chatgpt-oauth-translator https://github.com/weber87na/BabelDOC.git
cd BabelDOC
npm install -g @openai/codex
uv sync
```

若已複製此儲存庫，請先保留自己的未提交修改，再切換到功能分支。直接安裝 PyPI 原版 BabelDOC 不會包含此 fork 功能。

## 登入及查看模型

```sh
uv run babeldoc-chatgpt --chatgpt-login
uv run babeldoc-chatgpt --chatgpt-list-models
```

第一行會開啟瀏覽器，請用自己的 ChatGPT 帳號完成登入。第二行列出模型 ID、顯示名稱、支援的推理強度與預設強度。

也可使用 `uv run babeldoc --chatgpt-login` 和 `uv run babeldoc --chatgpt-list-models`。獨立的 `babeldoc-chatgpt` 指令不載入 PDF 處理模組，適合先檢查登入。

無法接收本機瀏覽器 callback 時，可使用官方裝置碼流程（須帳號及工作區允許）：

```sh
uv run babeldoc-chatgpt --chatgpt-login --chatgpt-device-auth
```

依終端機顯示的網址與裝置碼操作。登入必須由你本人完成；不用貼出密碼或 token。

## 翻譯

使用帳號的預設模型與預設推理強度：

```sh
uv run babeldoc --chatgpt --files "document.pdf" --lang-out zh-TW --qps 1
```

指定模型與推理強度時，將以下 `MODEL_ID` 和 `EFFORT` 替換成模型清單實際列出的值：

```sh
uv run babeldoc --chatgpt --files "document.pdf" --lang-out zh-TW --chatgpt-model MODEL_ID --chatgpt-reasoning EFFORT --qps 1
```

例如，只有在所選模型列出 `high` 時才傳入 `--chatgpt-reasoning high`。模型不存在或強度不支援時，程式會在 PDF 翻譯前報錯，不會靜默改用其他設定。

也可使用 TOML 設定檔，模型與強度欄位留白不設定即採用帳號預設值：

```toml
[babeldoc]
chatgpt = true
lang-out = "zh-TW"
qps = 1
# chatgpt-model = "請填實際模型 ID"
# chatgpt-reasoning = "請填支援的推理強度"
```

```sh
uv run babeldoc --config chatgpt.toml --files "document.pdf"
```

## 行為與限制

- 翻譯及自動術語擷取都使用同一個 ChatGPT 翻譯器，不會建立 OpenAI API 翻譯器。`--openai-term-extraction-*` 在 ChatGPT 模式不使用。
- `--chatgpt` 與 `--openai` 不能同時選擇。即使環境有 API Key，ChatGPT 子程序也會移除相關 API Key 變數；登入或額度失敗不會切換到 API 計費。
- 每次模型請求使用獨立的暫存對話及程序，完成或失敗後清理。請求採序列執行，啟動成本較高，大型 PDF 可能比直接 API 慢；目前不支援 `--enable-process-pool`。
- 翻譯快取區分服務、模型及推理強度；`--ignore-cache` 可略過快取。公式及格式標記沿用既有 OpenAI 翻譯器規則。
- `--enable-json-mode-if-requested` 會要求 JSON 並驗證回應為物件；這不是 API 的 JSON mode 保證，無效回應會報錯且不寫入快取。
- 請求或登入預設逾時為 600 秒，可用 `--chatgpt-timeout 900` 調整。額度、登入及翻譯錯誤不會無限重試；上層 PDF 管線仍可能嘗試較小翻譯區塊，請檢查輸出與錯誤紀錄。
- 登入狀態由 Codex 保存在 `~/.babeldoc/codex` 專用設定目錄，不影響一般 Codex 登入。請勿分享此目錄或將它提交到 Git。不要在此專用設定目錄加入 MCP、外掛或自訂模型供應商。
- 程式關閉網頁搜尋及 shell 工具，採唯讀沙箱，並拒絕工具／權限請求。PDF 文字仍會傳送給所登入帳號使用的模型服務。
- token 統計採 App Server 回傳的數值；不是剩餘訂閱額度或帳單金額，服務未回傳用量時記為 0。

## Windows 與疑難排解

Windows 的 npm `codex.cmd` 啟動器會解析為套件內原生 `codex.exe`。非標準安裝位置可指定：

```powershell
uv run babeldoc-chatgpt --chatgpt-login --chatgpt-codex-path "C:\tools\codex.exe"
```

翻譯時也要傳入相同的 `--chatgpt-codex-path`。找不到 Codex 時請重新安裝官方 CLI；協定方法不支援時請更新 CLI。此整合依據官方 App Server 協定，不能保證所有舊版本相容。

登出：

```sh
uv run babeldoc-chatgpt --chatgpt-logout
```

## 驗證狀態

已加入不需帳號的協定、登入狀態、模型驗證、串流、程序清理、Windows 啟動器、快取及翻譯器測試：

```sh
uv run python -m unittest discover -s tests -v
```

開發環境尚未完成真實 OAuth 登入與 PDF 翻譯端到端驗證。首次使用請先登入、列出模型，再選一份短 PDF 測試；自動化測試不會消耗帳號額度。

官方參考：[登入方式](https://developers.openai.com/codex/auth)、[App Server 協定](https://developers.openai.com/codex/app-server)。
