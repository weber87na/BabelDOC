<div align="center">

<br/>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://s.immersivetranslate.com/assets/uploads/babeldoc-big-logo-darkmode-with-transparent-background-IKuNO1.svg" width="320px" alt="BabelDOC"/>
  <img src="https://s.immersivetranslate.com/assets/uploads/babeldoc-big-logo-with-transparent-background-2xweBr.svg" width="320px" alt="BabelDOC"/>
</picture>

<!-- <h2 id="title">BabelDOC</h2> -->

<p>
  <!-- PyPI -->
  <a href="https://pypi.org/project/BabelDOC/">
    <img src="https://img.shields.io/pypi/v/BabelDOC"></a>
  <a href="https://pepy.tech/projects/BabelDOC">
    <img src="https://static.pepy.tech/badge/BabelDOC"></a>
  <!-- <a href="https://github.com/funstory-ai/BabelDOC/pulls">
    <img src="https://img.shields.io/badge/contributions-welcome-green"></a> -->
  <!-- License -->
  <a href="./LICENSE">
    <img src="https://img.shields.io/github/license/funstory-ai/BabelDOC"></a>
  <a href="https://t.me/+Z9_SgnxmsmA5NzBl">
    <img src="https://img.shields.io/badge/Telegram-2CA5E0?style=flat-squeare&logo=telegram&logoColor=white"></a>
  <a href="https://deepwiki.com/funstory-ai/BabelDOC"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki"></a>
</p>

<a href="https://trendshift.io/repositories/13358" target="_blank"><img src="https://trendshift.io/api/badge/repositories/13358" alt="funstory-ai%2FBabelDOC | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

</div>

PDF scientific paper translation and bilingual comparison library.

- **Online Service**: Beta version launched [Immersive Translate - BabelDOC](https://app.immersivetranslate.com/babel-doc/) Free usage quota is available; please refer to the FAQ section on the page for details.
- **Self-deployment**: [PDFMathTranslate-next](https://github.com/PDFMathTranslate-next/PDFMathTranslate-next) support for BabelDOC, available for self-deployment + WebUI with more translation services.
- Provides a simple [command line interface](#getting-started).
- Provides a [Python API](#python-api).
- Mainly designed to be embedded into other programs, but can also be used directly for simple translation tasks.

> [!TIP]
>
> How to use BabelDOC in Zotero
>
> 1. Immersive Translate Pro members can use the [immersive-translate/zotero-immersivetranslate](https://github.com/immersive-translate/zotero-immersivetranslate) plugin
>
> 2. PDFMathTranslate self-deployed users can use the [guaguastandup/zotero-pdf2zh](https://github.com/guaguastandup/zotero-pdf2zh) plugin

[Supported Language](https://funstory-ai.github.io/BabelDOC/supported_languages/)

## Preview

<div align="center">
<img src="https://s.immersivetranslate.com/assets/r2-uploads/images/babeldoc-preview.png" width="80%"/>
</div>

## We are hiring

See details: [EN](https://github.com/funstory-ai/jobs) | [ZH](https://github.com/funstory-ai/jobs/blob/main/README_ZH.md)

## Getting Started

此 fork 的 ChatGPT 帳號登入、更新安裝及翻譯範例，請見下方 [ChatGPT OAuth 快速開始](#chatgpt-oauth)。

### Install from PyPI

We recommend using the Tool feature of [uv](https://github.com/astral-sh/uv) to install BabelDOC.

1. First, you need to refer to [uv installation](https://github.com/astral-sh/uv#installation) to install uv and set up the `PATH` environment variable as prompted.

2. Use the following command to install BabelDOC:

```bash
uv tool install --python 3.12 BabelDOC

babeldoc --help
```

3. Use the `babeldoc` command. For example:

```bash
babeldoc --openai --openai-model "gpt-4o-mini" --openai-base-url "https://api.openai.com/v1" --openai-api-key "your-api-key-here"  --files example.pdf

# multiple files
babeldoc --openai --openai-model "gpt-4o-mini" --openai-base-url "https://api.openai.com/v1" --openai-api-key "your-api-key-here"  --files example1.pdf --files example2.pdf
```

### Install from Source

We still recommend using [uv](https://github.com/astral-sh/uv) to manage virtual environments.

1. First, you need to refer to [uv installation](https://github.com/astral-sh/uv#installation) to install uv and set up the `PATH` environment variable as prompted.

2. Use the following command to install BabelDOC:

```bash
# clone the project
git clone https://github.com/funstory-ai/BabelDOC

# enter the project directory
cd BabelDOC

# install dependencies and run babeldoc
uv run babeldoc --help
```

3. Use the `uv run babeldoc` command. For example:

```bash
uv run babeldoc --files example.pdf --openai --openai-model "gpt-4o-mini" --openai-base-url "https://api.openai.com/v1" --openai-api-key "your-api-key-here"

# multiple files
uv run babeldoc --files example.pdf --files example2.pdf --openai --openai-model "gpt-4o-mini" --openai-base-url "https://api.openai.com/v1" --openai-api-key "your-api-key-here"
```

> [!TIP]
> The absolute path is recommended.

<a id="chatgpt-oauth"></a>

### ChatGPT OAuth 帳號登入與翻譯（此 fork）

此分支透過官方 Codex CLI 的 App Server 使用 ChatGPT 帳號翻譯，不需要 OpenAI API Key。使用量仍受 ChatGPT／Codex 方案額度及模型存取權限制。以下範例適用於 `uv tool` 安裝；若從原始碼執行，須先依 [操作說明](docs/chatgpt-oauth.zh-TW.md#安裝此分支) 取得此 fork 的 `feat/chatgpt-oauth-translator` 分支，再於該專案目錄內，在 `babeldoc` 或 `babeldoc-chatgpt` 指令前加上 `uv run`。

#### 1. 安裝或更新到此分支

先安裝 Git、Node.js/npm 與 uv，再執行：

```sh
# 安裝或更新官方 Codex CLI
npm install -g @openai/codex@latest

# 安裝此 fork；已安裝 BabelDOC 時會取代現有工具
uv tool install --python 3.12 --force --reinstall "git+https://github.com/weber87na/BabelDOC.git@feat/chatgpt-oauth-translator"

# 確認 Codex 與新版登入指令可執行
codex --version
babeldoc-chatgpt --help
babeldoc --help
```

`uv tool install BabelDOC` 安裝的是 PyPI 發行版。若要使用此 fork 的 OAuth 功能，請使用上面的 Git 分支網址。更新後版本號仍可能顯示 `v0.6.4`；可在 `babeldoc --help` 中確認有 `--chatgpt-login` 及 `--openai-max-completion-tokens`。

完成上述安裝後，之後更新同一分支可用：

```sh
uv tool upgrade babeldoc --reinstall
npm install -g @openai/codex@latest
```

更新程式通常不需要重新登入。

#### 2. 用瀏覽器完成 OAuth 登入

```sh
babeldoc-chatgpt --chatgpt-login
```

依終端機顯示的網址在瀏覽器登入自己的 ChatGPT 帳號，等待終端機顯示「ChatGPT 登入成功」。若瀏覽器未自動開啟，可自行開啟終端機提供的網址。

無法接收本機瀏覽器 callback 時，可改用裝置碼登入（需帳號及工作區允許）：

```sh
babeldoc-chatgpt --chatgpt-login --chatgpt-device-auth
```

依終端機顯示的驗證網址與裝置碼完成登入。也可使用 `babeldoc --chatgpt-login` 或 `babeldoc --chatgpt-login --chatgpt-device-auth`；`babeldoc-chatgpt` 適合先登入，因為它不載入 PDF 處理模組。

#### 3. 查看模型與推理強度

```sh
babeldoc-chatgpt --chatgpt-list-models
```

輸出包含模型 ID、顯示名稱、支援的推理強度及預設強度。指定模型時請使用清單中的 ID，實際存取權及剩餘額度以翻譯請求結果為準。省略 `--chatgpt-model` 和 `--chatgpt-reasoning` 時，採用模型清單提供的預設值。

#### 4. 翻譯 PDF 範例

先使用預設模型翻譯英文 PDF 為繁體中文：

```sh
babeldoc --chatgpt --files "document.pdf" --lang-in en --lang-out zh-TW --qps 1
```

只有在模型清單列出 `gpt-6-luna` 時，才使用此範例：

```sh
babeldoc --chatgpt --chatgpt-model gpt-6-luna --files "document.pdf" --lang-out zh-TW --qps 1
```

若該模型也列出 `low` 推理強度，可明確指定：

```sh
babeldoc --chatgpt --chatgpt-model gpt-6-luna --chatgpt-reasoning low --files "document.pdf" --lang-out zh-TW --qps 1
```

更換其他模型時，將 `MODEL_ID` 和 `EFFORT` 換成清單實際列出的模型與強度；以下同時示範翻譯多個檔案：

```sh
babeldoc --chatgpt --chatgpt-model MODEL_ID --chatgpt-reasoning EFFORT --files "paper one.pdf" --files "paper two.pdf" --lang-out zh-TW --qps 1
```

#### 5. 登出、切換帳號或重新登入

需要切換帳號或重新登入時，分別執行：

```sh
babeldoc-chatgpt --chatgpt-logout
babeldoc-chatgpt --chatgpt-login
babeldoc-chatgpt --chatgpt-list-models
```

BabelDOC 將登入狀態存放在獨立的 `~/.babeldoc/codex` 目錄，與一般 Codex 登入分開管理；請使用上面的 BabelDOC 登入指令。

#### 模式與選項對照

| 翻譯模式 | 模型選項 | 推理強度選項 | 登入方式 |
| --- | --- | --- | --- |
| ChatGPT OAuth：`--chatgpt` | `--chatgpt-model` | `--chatgpt-reasoning` | `babeldoc-chatgpt --chatgpt-login` |
| OpenAI API：`--openai` | `--openai-model` | `--openai-reasoning` | `--openai-api-key` |

`--chatgpt` 與 `--openai` 只能選一個；OAuth 範例不需要加入 API Key。登入、額度或模型請求失敗時，此模式不會自動切換到 API 計費。首次使用可先挑一份短 PDF 驗證。

更多設定與 Windows 操作請見 [繁體中文操作說明](docs/chatgpt-oauth.zh-TW.md)。官方參考：[Codex CLI](https://learn.chatgpt.com/docs/codex/cli)、[登入方式](https://learn.chatgpt.com/docs/auth)及 [uv 工具更新](https://docs.astral.sh/uv/concepts/tools/#upgrading-tools)。

## Advanced Options

> [!NOTE]
> This CLI is mainly for debugging purposes. Although end users can use this CLI to translate files, we do not provide any technical support for this purpose.
>
> End users should directly use **Online Service**: Beta version launched [Immersive Translate - BabelDOC](https://app.immersivetranslate.com/babel-doc/) 1000 free pages per month.
>
> End users who need self-deployment should use [PDFMathTranslate 2.0](https://github.com/PDFMathTranslate/PDFMathTranslate-next)
> 
> If you find that an option is not listed below, it means that this option is a debugging option for maintainers. Please do not use these options.


### Language Options

- `--lang-in`, `-li`: Source language code (default: en)
- `--lang-out`, `-lo`: Target language code (default: zh)

> [!TIP]
> Currently, this project mainly focuses on English-to-Chinese translation, and other scenarios have not been tested yet.
> 
> (2025.3.1 update): Basic English target language support has been added, primarily to minimize line breaks within words([0-9A-Za-z]+).
> 
> [HELP WANTED: Collecting word regular expressions for more languages](https://github.com/funstory-ai/BabelDOC/issues/129)

### PDF Processing Options

- `--files`: One or more file paths to input PDF documents.
- `--pages`, `-p`: Specify pages to translate (e.g., "1,2,1-,-3,3-5"). If not set, translate all pages
- `--split-short-lines`: Force split short lines into different paragraphs (may cause poor typesetting & bugs)
- `--short-line-split-factor`: Split threshold factor (default: 0.8). The actual threshold is the median length of all lines on the current page \* this factor
- `--skip-clean`: Skip PDF cleaning step
- `--dual-translate-first`: Put translated pages first in dual PDF mode (default: original pages first)
- `--disable-rich-text-translate`: Disable rich text translation (may help improve compatibility with some PDFs)
- `--enhance-compatibility`: Enable all compatibility enhancement options (equivalent to --skip-clean --dual-translate-first --disable-rich-text-translate)
- `--use-alternating-pages-dual`: Use alternating pages mode for dual PDF. When enabled, original and translated pages are arranged in alternate order. When disabled (default), original and translated pages are shown side by side on the same page.
- `--watermark-output-mode`: Control watermark output mode: 'watermarked' (default) adds watermark to translated PDF, 'no_watermark' doesn't add watermark, 'both' outputs both versions.
- `--max-pages-per-part`: Maximum number of pages per part for split translation. If not set, no splitting will be performed.
- `--no-watermark`: [DEPRECATED] Use --watermark-output-mode=no_watermark instead.
- `--translate-table-text`: Translate table text (experimental, default: False)
- `--formular-font-pattern`: Font pattern to identify formula text (default: None)
- `--formular-char-pattern`: Character pattern to identify formula text (default: None)
- `--show-char-box`: Show character bounding boxes (debug only, default: False)
- `--skip-scanned-detection`: Skip scanned document detection (default: False). When using split translation, only the first part performs detection if not skipped.
- `--ocr-workaround`: Use OCR workaround (default: False). Only suitable for documents with black text on white background. When enabled, white rectangular blocks will be added below the translation to cover the original text content, and all text will be forced to black color.
- `--auto-enable-ocr-workaround`: Enable automatic OCR workaround (default: False). If a document is detected as heavily scanned, this will attempt to enable OCR processing and skip further scan detection. See "Important Interaction Note" below for crucial details on how this interacts with `--ocr-workaround` and `--skip-scanned-detection`.
- `--primary-font-family`: Override primary font family for translated text. Choices: 'serif' for serif fonts, 'sans-serif' for sans-serif fonts, 'script' for script/italic fonts. If not specified, uses automatic font selection based on original text properties.
- `--only-include-translated-page`: Only include translated pages in the output PDF. This option is only effective when `--pages` is used. (default: False)
- `--merge-alternating-line-numbers`: Enable post-processing to merge alternating line-number layouts (keep the number paragraph as an independent paragraph b; merge adjacent text paragraphs a and c across it when `layout_id` and `xobj_id` match, digits are ASCII and spaces only). Default: off.
- `--skip-form-render`: Skip form rendering (default: False). When enabled, PDF forms will not be rendered in the output.
- `--skip-curve-render`: Skip curve rendering (default: False). When enabled, PDF curves will not be rendered in the output.
- `--only-parse-generate-pdf`: Only parse PDF and generate output PDF without translation (default: False). This skips all translation-related processing including layout analysis, paragraph finding, style processing, and translation itself. Useful for testing PDF parsing and reconstruction functionality.
- `--remove-non-formula-lines`: Remove non-formula lines from paragraph areas (default: False). This removes decorative lines that are not part of formulas, while protecting lines in figure/table areas. Useful for cleaning up documents with decorative elements that interfere with text flow.
- `--non-formula-line-iou-threshold`: IoU threshold for detecting paragraph overlap when removing non-formula lines (default: 0.9). Higher values are more conservative and will remove fewer lines.
- `--figure-table-protection-threshold`: IoU threshold for protecting lines in figure/table areas when removing non-formula lines (default: 0.9). Higher values provide more protection for structural elements in figures and tables.

- `--rpc-doclayout`: RPC service host address for document layout analysis (default: None)
- `--working-dir`: Working directory for translation. If not set, use temp directory.
- `--no-auto-extract-glossary`: Disable automatic term extraction. If this flag is present, the step is skipped. Defaults to enabled.
- `--save-auto-extracted-glossary`: Save automatically extracted glossary to the specified file. If not set, the glossary will not be saved.

> [!TIP]
> - Both `--skip-clean` and `--dual-translate-first` may help improve compatibility with some PDF readers
> - `--disable-rich-text-translate` can also help with compatibility by simplifying translation input
> - However, using `--skip-clean` will result in larger file sizes
> - If you encounter any compatibility issues, try using `--enhance-compatibility` first
> - Use `--max-pages-per-part` for large documents to split them into smaller parts for translation and automatically merge them back.
> - Use `--skip-scanned-detection` to speed up processing when you know your document is not a scanned PDF.
> - Use `--ocr-workaround` to fill background for scanned PDF. (Current assumption: background is pure white, text is pure black, this option will also auto enable `--skip-scanned-detection`)

### Translation Service Options

- `--qps`: QPS (Queries Per Second) limit for translation service (default: 4)
- `--ignore-cache`: Ignore translation cache and force retranslation
- `--no-dual`: Do not output bilingual PDF files
- `--no-mono`: Do not output monolingual PDF files
- `--min-text-length`: Minimum text length to translate (default: 5)
- `--openai`: Use OpenAI for translation (default: False)
- `--custom-system-prompt`: Custom system prompt for translation.
- `--add-formula-placehold-hint`: Add formula placeholder hint for translation. (Currently not recommended, it may affect translation quality, default: False)
- `--disable-same-text-fallback`: Disable fallback translation when LLM output matches input text. (default: False)
- `--pool-max-workers`: Maximum number of worker threads for internal task processing pools. If not specified, defaults to QPS value. This parameter directly sets the worker count, replacing previous QPS-based dynamic calculations.
- `--no-auto-extract-glossary`: Disable automatic term extraction. If this flag is present, the step is skipped. Defaults to enabled.

> [!TIP]
>
> 1. Currently, only OpenAI-compatible LLM is supported. For more translator support, please use [PDFMathTranslate 2.0](https://github.com/PDFMathTranslate/PDFMathTranslate-next).
> 2. It is recommended to use models with strong compatibility with OpenAI, such as: `glm-4-flash`, `deepseek-chat`, etc.
> 3. Currently, it has not been optimized for traditional translation engines like Bing/Google, it is recommended to use LLMs.
> 4. You can use [litellm](https://github.com/BerriAI/litellm) to access multiple models.
> 5. `--custom-system-prompt`: It is mainly used to add the `/no_think` instruction of Qwen 3 in the prompt. For example: `--custom-system-prompt "/no_think You are a professional, authentic machine translation engine."`

### OpenAI Specific Options

- `--openai-model`: OpenAI model to use (default: gpt-4o-mini)
- `--openai-base-url`: Base URL for OpenAI API
- `--openai-api-key`: API key for OpenAI service
- `--openai-reasoning`: Optional reasoning effort. OpenAI models use the Chat Completions `reasoning_effort` field; third-party models retain `reasoning.effort`. If unset, the model's default effort is used.
- `--openai-term-extraction-reasoning`: Optional effort for a separate term extraction translator, including when no separate model is specified.
- `--openai-max-completion-tokens`: Optional positive token budget for translation and term extraction, including reasoning tokens. LLM requests default to 16384 for known OpenAI reasoning models and 2048 for other models. An explicit budget also applies to paragraph fallback requests.
- `--no-send-temperature`: Omit the temperature parameter. Known OpenAI reasoning models automatically omit it.
- `--enable-json-mode-if-requested`: Enable JSON mode for OpenAI requests (default: False)
- `--term-pool-max-workers`: Maximum number of worker threads dedicated to automatic term extraction. If not specified, this defaults to the value of `--pool-max-workers`, which itself defaults to the QPS value when unset.

> [!TIP]
>
> 1. This tool supports any OpenAI-compatible API endpoints. Just set the correct base URL and API key. (e.g. `https://xxx.custom.xxx/v1`)
> 2. For local models like Ollama, you can use any value as the API key (e.g. `--openai-api-key a`).

For `gpt-6-luna`, use the existing OpenAI API mode:

```bash
babeldoc --openai --openai-model gpt-6-luna --openai-api-key "your-api-key-here" --files example.pdf
```

The translator uses `max_completion_tokens` for known OpenAI reasoning models and keeps the legacy `max_tokens` field for other models unless an explicit budget is set for an OpenAI model. Empty, refused, or truncated responses are rejected before caching. If the completion budget is exhausted, increase `--openai-max-completion-tokens` or reduce the model's reasoning effort with `--openai-reasoning` (for example, `low`). The 16384-token default is a configurable starting budget, not a guarantee for every document. See the official [model migration guidance](https://developers.openai.com/api/docs/guides/latest-model) and [Chat Completions parameter reference](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create).

### Glossary Options

- `--glossary-files`: Comma-separated paths to glossary CSV files.
  - Each CSV file should have the columns: `source`, `target`, and an optional `tgt_lng`.
  - The `source` column contains the term in the original language.
  - The `target` column contains the term in the target language.
  - The `tgt_lng` column (optional) specifies the target language for that specific entry (e.g., "zh-CN", "en-US").
    - If `tgt_lng` is provided for an entry, that entry will only be loaded and used if its (normalized) `tgt_lng` matches the (normalized) overall target language specified by `--lang-out`. Normalization involves lowercasing and replacing hyphens (`-`) with underscores (`_`).
    - If `tgt_lng` is omitted for an entry, that entry is considered applicable for any `--lang-out`.
  - The name of each glossary (used in LLM prompts) is derived from its filename (without the .csv extension).
  - During translation, the system will check the input text against the loaded glossaries. If terms from a glossary are found in the current text segment, that glossary (with the relevant terms) will be included in the prompt to the language model, along with an instruction to adhere to it.

### Output Control

- `--output`, `-o`: Output directory for translated files. If not set, use current working directory.
- `--debug`: Enable debug logging level and export detailed intermediate results in `~/.cache/babeldoc/working`.
- `--report-interval`: Progress report interval in seconds (default: 0.1).

### General Options

- `--warmup`: Only download and verify required assets then exit (default: False)

### Offline Assets Management

- `--generate-offline-assets`: Generate an offline assets package in the specified directory. This creates a zip file containing all required models and fonts.
- `--restore-offline-assets`: Restore an offline assets package from the specified file. This extracts models and fonts from a previously generated package.

> [!TIP]
> 
> 1. Offline assets packages are useful for environments without internet access or to speed up installation on multiple machines.
> 2. Generate a package once with `babeldoc --generate-offline-assets /path/to/output/dir` and then distribute it.
> 3. Restore the package on target machines with `babeldoc --restore-offline-assets /path/to/offline_assets_*.zip`.
> 4. The offline assets package name cannot be modified because the file list hash is encoded in the name.
> 5. If you provide a directory path to `--restore-offline-assets`, the tool will automatically look for the correct offline assets package file in that directory.
> 6. The package contains all necessary fonts and models required for document processing, ensuring consistent results across different environments.
> 7. The integrity of all assets is verified using SHA3-256 hashes during both packaging and restoration.
> 8. If you're deploying in an air-gapped environment, make sure to generate the package on a machine with internet access first.

### Configuration File

- `--config`, `-c`: Configuration file path. Use the TOML format.

Example Configuration:

```toml
[babeldoc]
# Basic settings
debug = true
lang-in = "en-US"
lang-out = "zh-CN"
qps = 10
output = "/path/to/output/dir"

# PDF processing options
split-short-lines = false
short-line-split-factor = 0.8
skip-clean = false
dual-translate-first = false
disable-rich-text-translate = false
use-alternating-pages-dual = false
watermark-output-mode = "watermarked"  # Choices: "watermarked", "no_watermark", "both"
max-pages-per-part = 50  # Automatically split the document for translation and merge it back.
only_include_translated_page = false # Only include translated pages in the output PDF. Effective only when `pages` is used.
# no-watermark = false  # DEPRECATED: Use watermark-output-mode instead
skip-scanned-detection = false  # Skip scanned document detection for faster processing
auto_extract_glossary = true # Set to false to disable automatic term extraction
formular_font_pattern = "" # Font pattern for formula text
formular_char_pattern = "" # Character pattern for formula text
show_char_box = false # Show character bounding boxes (debug)
ocr_workaround = false # Use OCR workaround for scanned PDFs
rpc_doclayout = "" # RPC service host for document layout analysis
working_dir = "" # Working directory for translation
auto_enable_ocr_workaround = false # Enable automatic OCR workaround for scanned PDFs. See docs for interaction with ocr_workaround and skip_scanned_detection.
skip_form_render = false # Skip form rendering (default: False)
skip_curve_render = false # Skip curve rendering (default: False)
only_parse_generate_pdf = false # Only parse PDF and generate output PDF without translation (default: False)
remove_non_formula_lines = false # Remove non-formula lines from paragraph areas (default: False)
non_formula_line_iou_threshold = 0.2 # IoU threshold for paragraph overlap detection (default: 0.2)
figure_table_protection_threshold = 0.3 # IoU threshold for figure/table protection (default: 0.3)

# Translation service
openai = true
openai-model = "gpt-4o-mini"
openai-base-url = "https://api.openai.com/v1"
openai-api-key = "your-api-key-here"
enable-json-mode-if-requested = false  # Enable JSON mode when requested (default: false)
disable_same_text_fallback = false # Disable fallback translation when LLM output matches input text (default: false)
pool-max-workers = 8  # Maximum worker threads for task processing (defaults to QPS value if not set)

# Glossary Options (Optional)
# glossary-files = "/path/to/glossary1.csv,/path/to/glossary2.csv"

# Output control
no-dual = false
no-mono = false
min-text-length = 5
report-interval = 0.5

# Offline assets management
# Uncomment one of these options as needed:
# generate-offline-assets = "/path/to/output/dir"
# restore-offline-assets = "/path/to/offline_assets_package.zip"
```

## Python API

The current recommended way to call BabelDOC in Python is to call the `high_level.do_translate_async_stream` function of [pdf2zh next](https://pdf2zh-next.com/).

> [!WARNING]
> **All APIs of BabelDOC should be considered as internal APIs, and any direct use of BabelDOC is not supported.**

## Background

There are a lot projects and teams working on to make document editing and translating easier like:

- [mathpix](https://mathpix.com/)
- [Doc2X](https://doc2x.noedgeai.com/)
- [minerU](https://github.com/opendatalab/MinerU)
- [PDFMathTranslate](https://github.com/PDFMathTranslate/PDFMathTranslate)

There are also some solutions to solve specific parts of the problem like:

- [layoutreader](https://github.com/microsoft/unilm/tree/master/layoutreader): the read order of the text block in a pdf
- [Surya](https://github.com/surya-is/surya): the structure of the pdf

This project hopes to promote a standard pipeline and interface to solve the problem.

In fact, there are two main stages of a PDF parser or translator:

- **Parsing**: A stage of parsing means to get the structure of the pdf such as text blocks, images, tables, etc.
- **Rendering**: A stage of rendering means to render the structure into a new pdf or other format.

For a service like mathpix, it will parse the pdf into a structure may be in a XML format, and then render them using a single column reader order as [layoutreader](https://github.com/microsoft/unilm/tree/master/layoutreader) does. The bad news is that the original structure lost.

Some people will use Adobe PDF Parser because it will generate a Word document and it keeps the original structure. But it is somewhat expensive.
And you know, a pdf or word document is not a good format for reading in mobile devices.

We offer an intermediate representation of the results from parser and can be rendered into a new pdf or other format. The pipeline is also a plugin-based system which everybody can add their new model, ocr, renderer, etc.

## Roadmap

- [ ] Add line support
- [ ] Add table support
- [ ] Add cross-page/cross-column paragraph support
- [ ] More advanced typesetting features
- [ ] Outline support
- [ ] ...

Our first 1.0 version goal is to finish a translation from [PDF Reference, Version 1.7](https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/pdfreference1.7old.pdf) to the following language version:

- Simplified Chinese
- Traditional Chinese
- Japanese
- Spanish

And meet the following requirements:

- layout error less than 1%
- content loss less than 1%

## Version Number Explanation

This project uses a combination of [Semantic Versioning](https://semver.org/) and [Pride Versioning](https://pridever.org/). The version number format is: "0.MAJOR.MINOR".

> [!NOTE]
>
> The API compatibility here mainly refers to the compatibility with [pdf2zh_next](https://pdf2zh-next.com/).


- MAJOR: Incremented by 1 when API incompatible changes are made or when proud improvements are implemented.

- MINOR: Incremented by 1 when any API compatible changes are made.

## Known Issues

1. Parsing errors in the author and reference sections; they get merged into one paragraph after translation.
2. Lines are not supported.
3. Does not support drop caps.
4. Large pages will be skipped.

## How to Contribute

BabelDOC is currently developed in a maintainer-led mode. Bug reports,
reproducible PDFs, documentation fixes, and small compatibility fixes are
welcome. For changes to parsing, rendering, translation, or service integration
behavior, please open an issue for discussion before submitting a pull request.

Everyone interacting in BabelDOC and its sub-projects' codebases, issue trackers, chat rooms, and mailing lists is expected to follow the BabelDOC [Code of Conduct](https://github.com/funstory-ai/BabelDOC/blob/main/docs/CODE_OF_CONDUCT.md).

[Immersive Translation](https://immersivetranslate.com) sponsors monthly Pro membership redemption codes for active contributors to this project, see details at: [CONTRIBUTOR_REWARD.md](https://github.com/funstory-ai/BabelDOC/blob/main/docs/CONTRIBUTOR_REWARD.md)

## Acknowledgements

BabelDOC is still at an early stage of development, and many parts are not as
polished as we would like yet. We sincerely appreciate every bug report,
criticism, suggestion, reproducible PDF, downstream integration experience, and
contribution from people working on BabelDOC and related upstream/downstream
projects. We will keep iterating on BabelDOC, fixing bugs, and making it better
step by step.

- [PDFMathTranslate](https://github.com/PDFMathTranslate/PDFMathTranslate)
- [DocLayout-YOLO](https://github.com/opendatalab/DocLayout-YOLO)
- [pdfminer](https://github.com/pdfminer/pdfminer.six)
- [PyMuPDF](https://github.com/pymupdf/PyMuPDF)
- [Asynchronize](https://github.com/multimeric/Asynchronize/tree/master?tab=readme-ov-file)
- [PriorityThreadPoolExecutor](https://github.com/oleglpts/PriorityThreadPoolExecutor)

<h2 id="star_hist">Star History</h2>

<a href="https://star-history.com/#funstory-ai/babeldoc&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=funstory-ai/babeldoc&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=funstory-ai/babeldoc&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=funstory-ai/babeldoc&type=Date"/>
 </picture>
</a>

> [!WARNING]
> **Important Interaction Note for `--auto-enable-ocr-workaround`:**
>
> When `--auto-enable-ocr-workaround` is set to `true` (either via command line or config file):
>
> 1.  During the initial setup, the values for `ocr_workaround` and `skip_scanned_detection` will be forced to `false` by `TranslationConfig`, regardless of whether you also set `--ocr-workaround` or `--skip-scanned-detection` flags.
> 2.  Then, during the scanned document detection phase (`DetectScannedFile` stage):
>     *   If the document is identified as heavily scanned (e.g., >80% scanned pages) AND `auto_enable_ocr_workaround` is `true` (i.e., `translation_config.auto_enable_ocr_workaround` is true), the system will then attempt to set both `ocr_workaround` to `true` and `skip_scanned_detection` to `true`.
>
> This means that `--auto-enable-ocr-workaround` effectively gives the system control to enable OCR processing for scanned documents, potentially overriding manual settings for `--ocr-workaround` and `--skip_scanned_detection` based on its detection results. If the document is *not* detected as heavily scanned, then the initial `false` values for `ocr_workaround` and `skip_scanned_detection` (forced by `--auto-enable-ocr-workaround` at the `TranslationConfig` initialization stage) will remain in effect unless changed by other logic.
