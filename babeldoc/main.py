import asyncio
import logging
import multiprocessing as mp
import queue
import random
import sys
from pathlib import Path
from typing import Any

import configargparse
import tqdm
from rich.progress import BarColumn
from rich.progress import MofNCompleteColumn
from rich.progress import Progress
from rich.progress import TextColumn
from rich.progress import TimeElapsedColumn
from rich.progress import TimeRemainingColumn

import babeldoc.assets.assets
import babeldoc.format.pdf.high_level
from babeldoc.const import enable_process_pool
from babeldoc.format.pdf.translation_config import TranslationConfig
from babeldoc.format.pdf.translation_config import WatermarkOutputMode
from babeldoc.glossary import Glossary
from babeldoc.translator.translator import OpenAITranslator
from babeldoc.translator.translator import set_translate_rate_limiter

logger = logging.getLogger(__name__)
__version__ = "0.6.4"


def create_parser():
    parser = configargparse.ArgParser(
        config_file_parser_class=configargparse.TomlConfigParser(["babeldoc"]),
    )
    parser.add_argument(
        "-c",
        "--config",
        is_config_file=True,
        help="config file path",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--files",
        action="append",
        help="One or more paths to PDF files.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Use debug logging level.",
    )
    parser.add_argument(
        "--warmup",
        action="store_true",
        help="Only download and verify required assets then exit.",
    )
    parser.add_argument(
        "--rpc-doclayout",
        help="RPC service host address for document layout analysis",
    )
    parser.add_argument(
        "--rpc-doclayout2",
        help="RPC service host address for document layout analysis",
    )
    parser.add_argument(
        "--rpc-doclayout3",
        help="RPC service host address for document layout analysis",
    )
    parser.add_argument(
        "--rpc-doclayout4",
        help="RPC service host address for document layout analysis",
    )
    parser.add_argument(
        "--rpc-doclayout5",
        help="RPC service host address for document layout analysis",
    )
    parser.add_argument(
        "--rpc-doclayout6",
        help="RPC service host address for document layout analysis",
    )
    parser.add_argument(
        "--rpc-doclayout7",
        help="RPC service host address for document layout analysis",
    )
    parser.add_argument(
        "--generate-offline-assets",
        default=None,
        help="Generate offline assets package in the specified directory",
    )
    parser.add_argument(
        "--restore-offline-assets",
        default=None,
        help="Restore offline assets package from the specified file",
    )
    parser.add_argument(
        "--working-dir",
        default=None,
        help="Working directory for translation. If not set, use temp directory.",
    )
    parser.add_argument(
        "--metadata-extra-data",
        default=None,
        help="Extra data for metadata",
    )
    parser.add_argument(
        "--enable-process-pool",
        action="store_true",
        help="DEBUG ONLY",
    )
    # translation option argument group
    translation_group = parser.add_argument_group(
        "Translation",
        description="Used during translation",
    )
    translation_group.add_argument(
        "--pages",
        "-p",
        help="Pages to translate. If not set, translate all pages. like: 1,2,1-,-3,3-5",
    )
    translation_group.add_argument(
        "--min-text-length",
        type=int,
        default=5,
        help="Minimum text length to translate (default: 5)",
    )
    translation_group.add_argument(
        "--lang-in",
        "-li",
        default="en",
        help="The code of source language.",
    )
    translation_group.add_argument(
        "--lang-out",
        "-lo",
        default="zh",
        help="The code of target language.",
    )
    translation_group.add_argument(
        "--output",
        "-o",
        help="Output directory for files. if not set, use same as input.",
    )
    translation_group.add_argument(
        "--qps",
        "-q",
        type=int,
        default=4,
        help="QPS limit of translation service",
    )
    translation_group.add_argument(
        "--ignore-cache",
        action="store_true",
        help="Ignore translation cache.",
    )
    translation_group.add_argument(
        "--no-dual",
        action="store_true",
        help="Do not output bilingual PDF files",
    )
    translation_group.add_argument(
        "--no-mono",
        action="store_true",
        help="Do not output monolingual PDF files",
    )
    translation_group.add_argument(
        "--formular-font-pattern",
        help="Font pattern to identify formula text",
    )
    translation_group.add_argument(
        "--formular-char-pattern",
        help="Character pattern to identify formula text",
    )
    translation_group.add_argument(
        "--split-short-lines",
        action="store_true",
        help="Force split short lines into different paragraphs (may cause poor typesetting & bugs)",
    )
    translation_group.add_argument(
        "--short-line-split-factor",
        type=float,
        default=0.8,
        help="Split threshold factor. The actual threshold is the median length of all lines on the current page * this factor",
    )
    translation_group.add_argument(
        "--skip-clean",
        action="store_true",
        help="Skip PDF cleaning step",
    )
    translation_group.add_argument(
        "--dual-translate-first",
        action="store_true",
        help="Put translated pages first in dual PDF mode",
    )
    translation_group.add_argument(
        "--disable-rich-text-translate",
        action="store_true",
        help="Disable rich text translation (may help improve compatibility with some PDFs)",
    )
    translation_group.add_argument(
        "--enhance-compatibility",
        action="store_true",
        help="Enable all compatibility enhancement options (equivalent to --skip-clean --dual-translate-first --disable-rich-text-translate)",
    )
    translation_group.add_argument(
        "--use-alternating-pages-dual",
        action="store_true",
        help="Use alternating pages mode for dual PDF. When enabled, original and translated pages are arranged in alternate order.",
    )
    translation_group.add_argument(
        "--watermark-output-mode",
        type=str,
        choices=["watermarked", "no_watermark", "both"],
        default="watermarked",
        help="Control watermark output mode: 'watermarked' (default) adds watermark to translated PDF, 'no_watermark' doesn't add watermark, 'both' outputs both versions.",
    )
    translation_group.add_argument(
        "--max-pages-per-part",
        type=int,
        help="Maximum number of pages per part for split translation. If not set, no splitting will be performed.",
    )
    translation_group.add_argument(
        "--no-watermark",
        action="store_true",
        help="[DEPRECATED] Use --watermark-output-mode=no_watermark instead. Do not add watermark to the translated PDF.",
    )
    translation_group.add_argument(
        "--report-interval",
        type=float,
        default=0.1,
        help="Progress report interval in seconds (default: 0.1)",
    )
    translation_group.add_argument(
        "--translate-table-text",
        action="store_true",
        default=False,
        help="Translate table text (experimental)",
    )
    translation_group.add_argument(
        "--show-char-box",
        action="store_true",
        default=False,
        help="Show character box (debug only)",
    )
    translation_group.add_argument(
        "--skip-scanned-detection",
        action="store_true",
        default=False,
        help="Skip scanned document detection (speeds up processing for non-scanned documents)",
    )
    translation_group.add_argument(
        "--ocr-workaround",
        action="store_true",
        default=False,
        help="Add text fill background (experimental)",
    )
    translation_group.add_argument(
        "--custom-system-prompt",
        help="Custom system prompt for translation.",
        default=None,
    )
    translation_group.add_argument(
        "--add-formula-placehold-hint",
        action="store_true",
        default=False,
        help="Add formula placeholder hint for translation. (Currently not recommended, it may affect translation quality, default: False)",
    )
    translation_group.add_argument(
        "--disable-same-text-fallback",
        action="store_true",
        default=False,
        help="Disable fallback translation when LLM output matches input text. (default: False)",
    )
    translation_group.add_argument(
        "--glossary-files",
        type=str,
        default=None,
        help="Comma-separated paths to glossary CSV files.",
    )
    translation_group.add_argument(
        "--pool-max-workers",
        type=int,
        help="Maximum number of worker threads for internal task processing pools. If not specified, defaults to QPS value. This parameter directly sets the worker count, replacing previous QPS-based dynamic calculations.",
    )
    translation_group.add_argument(
        "--term-pool-max-workers",
        type=int,
        help="Maximum number of worker threads dedicated to automatic term extraction. If not specified, defaults to --pool-max-workers (or QPS value when unset).",
    )
    translation_group.add_argument(
        "--no-auto-extract-glossary",
        action="store_false",
        dest="auto_extract_glossary",
        default=True,
        help="Disable automatic term extraction. (Config file: set auto_extract_glossary = false)",
    )
    translation_group.add_argument(
        "--auto-enable-ocr-workaround",
        action="store_true",
        default=False,
        help="Enable automatic OCR workaround. If a document is detected as heavily scanned, this will attempt to enable OCR processing and skip further scan detection. Note: This option interacts with `--ocr-workaround` and `--skip-scanned-detection`. See documentation for details. (default: False)",
    )
    translation_group.add_argument(
        "--primary-font-family",
        type=str,
        choices=["serif", "sans-serif", "script"],
        default=None,
        help="Override primary font family for translated text. Choices: 'serif' for serif fonts, 'sans-serif' for sans-serif fonts, 'script' for script/italic fonts. If not specified, uses automatic font selection based on original text properties.",
    )
    translation_group.add_argument(
        "--only-include-translated-page",
        action="store_true",
        default=False,
        help="Only include translated pages in the output PDF. Effective only when --pages is used.",
    )
    translation_group.add_argument(
        "--save-auto-extracted-glossary",
        action="store_true",
        default=False,
        help="Save automatically extracted glossary terms to a CSV file in the output directory.",
    )
    translation_group.add_argument(
        "--disable-graphic-element-process",
        action="store_true",
        default=False,
        help="Disable graphic element process. (default: False)",
    )
    translation_group.add_argument(
        "--no-merge-alternating-line-numbers",
        action="store_false",
        dest="merge_alternating_line_numbers",
        default=True,
        help="Disable post-processing that merges alternating line-number layouts (by default this feature is enabled).",
    )
    translation_group.add_argument(
        "--skip-translation",
        action="store_true",
        default=False,
        help="Skip translation step. (default: False)",
    )
    translation_group.add_argument(
        "--skip-form-render",
        action="store_true",
        default=False,
        help="Skip form rendering. (default: False)",
    )
    translation_group.add_argument(
        "--skip-curve-render",
        action="store_true",
        default=False,
        help="Skip curve rendering. (default: False)",
    )
    translation_group.add_argument(
        "--only-parse-generate-pdf",
        action="store_true",
        default=False,
        help="Only parse PDF and generate output PDF without translation (default: False). This skips all translation-related processing including layout analysis, paragraph finding, style processing, and translation itself.",
    )
    translation_group.add_argument(
        "--remove-non-formula-lines",
        action="store_true",
        default=False,
        help="Remove non-formula lines from paragraph areas. This removes decorative lines that are not part of formulas, while protecting lines in figure/table areas. (default: False)",
    )
    translation_group.add_argument(
        "--non-formula-line-iou-threshold",
        type=float,
        default=0.9,
        help="IoU threshold for detecting paragraph overlap when removing non-formula lines. Higher values are more conservative. (default: 0.9)",
    )
    translation_group.add_argument(
        "--figure-table-protection-threshold",
        type=float,
        default=0.9,
        help="IoU threshold for protecting lines in figure/table areas when removing non-formula lines. Higher values provide more protection. (default: 0.9)",
    )
    translation_group.add_argument(
        "--skip-formula-offset-calculation",
        action="store_true",
        default=False,
        help="Skip formula offset calculation (default: False)",
    )
    # service option argument group
    service_group = translation_group.add_mutually_exclusive_group()
    service_group.add_argument(
        "--openai",
        action="store_true",
        help="Use OpenAI translator.",
    )
    service_group = parser.add_argument_group(
        "Translation - OpenAI Options",
        description="OpenAI specific options",
    )
    service_group.add_argument(
        "--openai-model",
        default="gpt-4o-mini",
        help="The OpenAI model to use for translation.",
    )
    service_group.add_argument(
        "--openai-base-url",
        help="The base URL for the OpenAI API.",
    )
    service_group.add_argument(
        "--openai-api-key",
        "-k",
        help="The API key for the OpenAI API.",
    )
    service_group.add_argument(
        "--openai-term-extraction-model",
        default=None,
        help="OpenAI model to use for automatic term extraction. Defaults to --openai-model when unset.",
    )
    service_group.add_argument(
        "--openai-term-extraction-base-url",
        default=None,
        help="Base URL for the OpenAI API used during automatic term extraction. Falls back to --openai-base-url when unset.",
    )
    service_group.add_argument(
        "--openai-term-extraction-api-key",
        default=None,
        help="API key for the OpenAI API used during automatic term extraction. Falls back to --openai-api-key when unset.",
    )
    service_group.add_argument(
        "--enable-json-mode-if-requested",
        action="store_true",
        default=False,
        help="Enable JSON mode for OpenAI requests.",
    )
    service_group.add_argument(
        "--send-dashscope-header",
        action="store_true",
        default=False,
        help="Send DashScope data inspection header to disable input/output inspection.",
    )
    service_group.add_argument(
        "--no-send-temperature",
        action="store_true",
        default=False,
        help="Do not send temperature parameter to OpenAI API (default: send temperature).",
    )
    service_group.add_argument(
        "--openai-reasoning",
        type=str,
        default=None,
        help="Reasoning string to send in the OpenAI request body 'reasoning' field. If not set, the field is not sent.",
    )
    service_group.add_argument(
        "--openai-thinking",
        type=str,
        choices=["enabled", "disabled"],
        default=None,
        help="DeepSeek-style thinking switch sent as request body 'thinking': {'type': ...}. If not set, the field is not sent.",
    )
    service_group.add_argument(
        "--openai-term-extraction-reasoning",
        type=str,
        default=None,
        help="Reasoning string for the OpenAI term extraction translator. If not set, no reasoning field is sent for term extraction requests.",
    )

    from babeldoc.translator.chatgpt_client import add_arguments

    add_arguments(parser)
    return parser


async def main():
    parser = create_parser()
    args: Any = parser.parse_args()

    from babeldoc.translator.chatgpt_client import ChatGPTError
    from babeldoc.translator.chatgpt_client import handle_action

    if args.chatgpt_device_auth and not args.chatgpt_login:
        parser.error("--chatgpt-device-auth 必須搭配 --chatgpt-login")
    if args.chatgpt and args.openai:
        parser.error("--chatgpt 與 --openai 只能選一個")
    try:
        if handle_action(args):
            return
    except (ChatGPTError, ValueError, OSError) as exc:
        parser.error(str(exc))

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.generate_offline_assets:
        babeldoc.assets.assets.generate_offline_assets_package(
            Path(args.generate_offline_assets)
        )
        logger.info("Offline assets package generated, exiting...")
        return

    if args.restore_offline_assets:
        babeldoc.assets.assets.restore_offline_assets_package(
            Path(args.restore_offline_assets)
        )
        logger.info("Offline assets package restored, exiting...")
        return

    if args.warmup:
        babeldoc.assets.assets.warmup()
        logger.info("Warmup completed, exiting...")
        return

    # 验证翻译服务选择
    if not (args.openai or args.chatgpt):
        parser.error("必須選擇一個翻譯服務：--openai 或 --chatgpt")
    if not args.files:
        parser.error("請使用 --files 指定 PDF 檔案")
    if args.chatgpt and args.enable_process_pool:
        parser.error("--chatgpt 目前不支援 --enable-process-pool；請使用預設執行模式")

    # 验证 OpenAI 参数
    if args.openai and not args.openai_api_key:
        parser.error("使用 OpenAI 服务时必须提供 API key")

    if args.enable_process_pool:
        enable_process_pool()

    # 实例化翻译器
    if args.chatgpt:
        from babeldoc.translator.chatgpt import ChatGPTTranslator

        try:
            translator = ChatGPTTranslator(
                lang_in=args.lang_in, lang_out=args.lang_out,
                model=args.chatgpt_model, reasoning=args.chatgpt_reasoning,
                codex_path=args.chatgpt_codex_path, timeout=args.chatgpt_timeout,
                ignore_cache=args.ignore_cache,
                enable_json_mode_if_requested=args.enable_json_mode_if_requested,
            )
        except (ChatGPTError, ValueError, OSError) as exc:
            parser.error(str(exc))
        term_extraction_translator = translator
        logger.info("ChatGPT subscription: model=%s reasoning=%s (no API fallback)",
                    translator.model, translator.reasoning)
    elif args.openai:
        translator_kwargs: dict[str, Any] = {}
        if args.openai_reasoning is not None:
            translator_kwargs["reasoning"] = args.openai_reasoning
        if args.openai_thinking is not None:
            translator_kwargs["thinking"] = args.openai_thinking
        translator = OpenAITranslator(
            lang_in=args.lang_in,
            lang_out=args.lang_out,
            model=args.openai_model,
            base_url=args.openai_base_url,
            api_key=args.openai_api_key,
            ignore_cache=args.ignore_cache,
            enable_json_mode_if_requested=args.enable_json_mode_if_requested,
            send_dashscope_header=args.send_dashscope_header,
            send_temperature=not args.no_send_temperature,
            **translator_kwargs,
        )
        term_extraction_translator = translator
        if (
            args.openai_term_extraction_model
            or args.openai_term_extraction_base_url
            or args.openai_term_extraction_api_key
        ):
            term_translator_kwargs: dict[str, Any] = {}
            if args.openai_term_extraction_reasoning is not None:
                term_translator_kwargs["reasoning"] = (
                    args.openai_term_extraction_reasoning
                )
            term_extraction_translator = OpenAITranslator(
                lang_in=args.lang_in,
                lang_out=args.lang_out,
                model=args.openai_term_extraction_model or args.openai_model,
                base_url=(args.openai_term_extraction_base_url or args.openai_ba…3556 tokens truncated…n
        return progress, progress_handler
    else:
        pbar = tqdm.tqdm(total=100, desc="translate")

        def progress_handler(event):
            if event["type"] == "progress_update":
                pbar.update(event["overall_progress"] - pbar.n)
                pbar.set_description(
                    f"{event['stage']} ({event['stage_current']}/{event['stage_total']})",
                )
            elif event["type"] == "progress_end":
                pbar.set_description(f"{event['stage']} (Complete)")
                pbar.refresh()

        return pbar, progress_handler


# for backward compatibility
def create_cache_folder():
    return babeldoc.format.pdf.high_level.create_cache_folder()


# for backward compatibility
def download_font_assets():
    return babeldoc.format.pdf.high_level.download_font_assets()


class EvictQueue(queue.Queue):
    def __init__(self, maxsize):
        self.discarded = 0
        super().__init__(maxsize)

    def put(self, item, block=False, timeout=None):
        while True:
            try:
                super().put(item, block=False)
                break
            except queue.Full:
                try:
                    self.get_nowait()
                    self.discarded += 1
                except queue.Empty:
                    pass


def speed_up_logs():
    import logging.handlers

    root_logger = logging.getLogger()
    log_que = EvictQueue(1000)
    queue_handler = logging.handlers.QueueHandler(log_que)
    queue_listener = logging.handlers.QueueListener(log_que, *root_logger.handlers)
    queue_listener.start()
    root_logger.handlers = [queue_handler]


def cli():
    """Command line interface entry point."""
    from rich.logging import RichHandler

    logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])

    logging.getLogger("httpx").setLevel("CRITICAL")
    logging.getLogger("httpx").propagate = False
    logging.getLogger("openai").setLevel("CRITICAL")
    logging.getLogger("openai").propagate = False
    logging.getLogger("httpcore").setLevel("CRITICAL")
    logging.getLogger("httpcore").propagate = False
    logging.getLogger("http11").setLevel("CRITICAL")
    logging.getLogger("http11").propagate = False
    for v in logging.Logger.manager.loggerDict.values():
        if getattr(v, "name", None) is None:
            continue
        if (
            v.name.startswith("pdfminer")
            or v.name.startswith("peewee")
            or v.name.startswith("httpx")
            or "http11" in v.name
            or "openai" in v.name
            or "pdfminer" in v.name
        ):
            v.disabled = True
            v.propagate = False

    speed_up_logs()
    babeldoc.format.pdf.high_level.init()
    asyncio.run(main())


if __name__ == "__main__":
    if sys.platform == "darwin" or sys.platform == "win32":
        mp.set_start_method("spawn")
    else:
        mp.set_start_method("forkserver")
    cli()
