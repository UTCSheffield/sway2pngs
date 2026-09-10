from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080
DEFAULT_WAIT_MS = 1000
DEFAULT_TIMEOUT_MS = 30000


def build_capture_positions(total_height: int, viewport_height: int) -> list[int]:
    if viewport_height <= 0:
        raise ValueError("viewport_height must be greater than zero")

    max_scroll = max(total_height - viewport_height, 0)
    positions = [0]

    while positions[-1] < max_scroll:
        positions.append(min(positions[-1] + viewport_height, max_scroll))

    return positions


def capture_page_screenshots(page, output_dir: Path, prefix: str, wait_ms: int) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    total_height = int(page.evaluate("() => document.documentElement.scrollHeight"))
    viewport_height = int(page.evaluate("() => window.innerHeight"))

    captures: list[Path] = []
    for index, scroll_y in enumerate(
        build_capture_positions(total_height, viewport_height),
        start=1,
    ):
        page.evaluate("(value) => window.scrollTo(0, value)", scroll_y)
        if wait_ms:
            page.wait_for_timeout(wait_ms)

        output_path = output_dir / f"{prefix}-{index:03d}.png"
        page.screenshot(path=str(output_path))
        captures.append(output_path)

    return captures


def run_capture(args: argparse.Namespace) -> list[Path]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser_launcher = getattr(playwright, args.browser)
        browser = browser_launcher.launch(headless=args.headless)

        try:
            page = browser.new_page(
                viewport={"width": args.width, "height": args.height},
                device_scale_factor=1,
            )
            page.emulate_media(media="screen")
            page.goto(args.url, wait_until="load", timeout=args.timeout_ms)

            return capture_page_screenshots(
                page=page,
                output_dir=args.output_dir,
                prefix=args.prefix,
                wait_ms=args.wait_ms,
            )
        finally:
            browser.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture 1920x1080 PNG screenshots from a Sway URL.",
    )
    parser.add_argument("url", help="Public Sway URL to capture")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory to write PNG files into",
    )
    parser.add_argument(
        "--prefix",
        default="slide",
        help="Filename prefix for each captured image",
    )
    parser.add_argument(
        "--browser",
        choices=("chromium", "firefox", "webkit"),
        default="chromium",
        help="Browser engine to use for the capture session",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=DEFAULT_WIDTH,
        help="Viewport width in pixels",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=DEFAULT_HEIGHT,
        help="Viewport height in pixels",
    )
    parser.add_argument(
        "--wait-ms",
        type=int,
        default=DEFAULT_WAIT_MS,
        help="Delay after page load and each scroll before capturing",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=DEFAULT_TIMEOUT_MS,
        help="Navigation timeout in milliseconds",
    )
    parser.add_argument(
        "--headed",
        dest="headless",
        action="store_false",
        help="Show the browser window during capture",
    )
    parser.set_defaults(headless=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    captures = run_capture(args)

    for capture in captures:
        print(capture)

    return 0
