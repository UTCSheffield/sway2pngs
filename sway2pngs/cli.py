from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Sequence

DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080
DEFAULT_WAIT_MS = 1500
DEFAULT_TIMEOUT_MS = 30000

# Some Sways navigate via a numbered section menu (a carousel) rather than a
# scrollable page. The toggle opens a panel of "Section N of TOTAL" links.
SECTION_NAV_TOGGLE_SELECTOR = '[aria-label="Navigate to different sections in this Sway"]'
SECTION_LABEL_PATTERN = re.compile(r"^Section \d+ of (\d+)$")


def build_capture_positions(total_height: int, viewport_height: int) -> list[int]:
    if viewport_height <= 0:
        raise ValueError("viewport_height must be greater than zero")

    max_scroll = max(total_height - viewport_height, 0)
    positions = [0]

    while positions[-1] < max_scroll:
        positions.append(min(positions[-1] + viewport_height, max_scroll))

    return positions


def _count_sway_sections(page) -> int | None:
    nav_toggle = page.query_selector(SECTION_NAV_TOGGLE_SELECTOR)
    if nav_toggle is None:
        return None

    nav_toggle.click()
    page.wait_for_timeout(300)

    for section in page.query_selector_all('[aria-label^="Section "]'):
        match = SECTION_LABEL_PATTERN.match(section.get_attribute("aria-label") or "")
        if match:
            return int(match.group(1))

    return None


def _capture_by_section(
    page, output_dir: Path, prefix: str, wait_ms: int, section_count: int
) -> list[Path]:
    captures: list[Path] = []

    for index in range(1, section_count + 1):
        section_selector = f'[aria-label="Section {index} of {section_count}"]'
        section_link = page.query_selector(section_selector)
        if section_link is None or not section_link.is_visible():
            # Clicking a section closes the nav panel, so reopen it for the next one.
            nav_toggle = page.query_selector(SECTION_NAV_TOGGLE_SELECTOR)
            if nav_toggle is not None:
                nav_toggle.click()
                page.wait_for_timeout(300)
            section_link = page.query_selector(section_selector)

        section_link.click()
        if wait_ms:
            page.wait_for_timeout(wait_ms)

        output_path = output_dir / f"{prefix}-{index:03d}.png"
        page.screenshot(path=str(output_path))
        captures.append(output_path)

    return captures


def _capture_by_scroll(page, output_dir: Path, prefix: str, wait_ms: int) -> list[Path]:
    viewport_height = int(page.evaluate("() => window.innerHeight"))

    captures: list[Path] = []
    scroll_y = 0
    index = 1
    while True:
        page.evaluate("(value) => window.scrollTo(0, value)", scroll_y)
        if wait_ms:
            page.wait_for_timeout(wait_ms)

        # Re-measured each step since Sway lazy-loads more content as you scroll down.
        total_height = int(page.evaluate("() => document.documentElement.scrollHeight"))

        output_path = output_dir / f"{prefix}-{index:03d}.png"
        page.screenshot(path=str(output_path))
        captures.append(output_path)

        max_scroll = max(total_height - viewport_height, 0)
        if scroll_y >= max_scroll:
            break

        scroll_y = min(scroll_y + viewport_height, max_scroll)
        index += 1

    return captures


def capture_page_screenshots(page, output_dir: Path, prefix: str, wait_ms: int) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    if hasattr(page, "query_selector"):
        section_count = _count_sway_sections(page)
        if section_count:
            return _capture_by_section(page, output_dir, prefix, wait_ms, section_count)

    return _capture_by_scroll(page, output_dir, prefix, wait_ms)


def run_capture(args: argparse.Namespace) -> list[Path]:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
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
            try:
                page.wait_for_load_state("networkidle", timeout=args.timeout_ms)
            except PlaywrightTimeoutError:
                pass

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
