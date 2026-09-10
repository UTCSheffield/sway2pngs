import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sway2pngs.cli import (
    build_capture_positions,
    build_default_prefix,
    capture_page_screenshots,
    main,
)


class FakePage:
    def __init__(self, total_height: int, viewport_height: int) -> None:
        self.total_height = total_height
        self.viewport_height = viewport_height
        self.scrolls: list[int] = []
        self.waits: list[int] = []
        self.screenshots: list[Path] = []

    def evaluate(self, script: str, value: int | None = None) -> int | None:
        if script == "() => document.documentElement.scrollHeight":
            return self.total_height
        if script == "() => window.innerHeight":
            return self.viewport_height
        if script == "(value) => window.scrollTo(0, value)":
            self.scrolls.append(value if value is not None else 0)
            return None
        raise AssertionError(f"Unexpected script: {script}")

    def wait_for_timeout(self, wait_ms: int) -> None:
        self.waits.append(wait_ms)

    def screenshot(self, path: str) -> None:
        screenshot_path = Path(path)
        screenshot_path.write_bytes(b"png")
        self.screenshots.append(screenshot_path)


class BuildCapturePositionsTests(unittest.TestCase):
    def test_returns_single_capture_for_short_pages(self) -> None:
        self.assertEqual(build_capture_positions(800, 1080), [0])

    def test_steps_by_viewport_and_includes_last_partial_screen(self) -> None:
        self.assertEqual(build_capture_positions(2500, 1080), [0, 1080, 1420])


class DefaultPrefixTests(unittest.TestCase):
    def test_builds_safe_title_date_and_slide_prefix(self) -> None:
        class Page:
            def title(self) -> str:
                return "Opportunities: Bulletin / 2026"

        prefix = build_default_prefix(Page())

        self.assertRegex(prefix, r"^Opportunities-Bulletin-2026-\d{4}-\d{2}-\d{2}-slide$")


class CapturePageScreenshotsTests(unittest.TestCase):
    def test_captures_numbered_pngs_for_each_scroll_position(self) -> None:
        page = FakePage(total_height=2500, viewport_height=1080)

        with tempfile.TemporaryDirectory() as tmpdir:
            captures = capture_page_screenshots(
                page=page,
                output_dir=Path(tmpdir),
                prefix="sway",
                wait_ms=250,
            )

            self.assertEqual(page.scrolls, [0, 1080, 1420])
            self.assertEqual(page.waits, [250, 250, 250])
            self.assertEqual(
                [path.name for path in captures],
                ["sway-001.png", "sway-002.png", "sway-003.png"],
            )
            self.assertTrue(all(path.exists() for path in captures))


class MainTests(unittest.TestCase):
    def test_parses_cli_arguments_and_prints_paths(self) -> None:
        capture_paths = [
            Path("/tmp/output/slide-001.png"),
            Path("/tmp/output/slide-002.png"),
        ]

        with patch("sway2pngs.cli.run_capture", return_value=capture_paths) as run_capture:
            with patch("builtins.print") as print_mock:
                exit_code = main(
                    [
                        "https://example.com",
                        "--output-dir",
                        "/tmp/output",
                        "--wait-ms",
                        "0",
                    ]
                )

        self.assertEqual(exit_code, 0)
        run_capture.assert_called_once()
        args = run_capture.call_args.args[0]
        self.assertEqual(args.url, "https://example.com")
        self.assertEqual(args.output_dir, Path("/tmp/output"))
        self.assertEqual(args.wait_ms, 0)
        print_mock.assert_any_call(Path("/tmp/output/slide-001.png"))
        print_mock.assert_any_call(Path("/tmp/output/slide-002.png"))


if __name__ == "__main__":
    unittest.main()
