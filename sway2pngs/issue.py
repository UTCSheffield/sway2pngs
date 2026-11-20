from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import urlsplit

ISSUE_URL_PATTERN = re.compile(r"https?://[^\s<>]+")
TRAILING_URL_PUNCTUATION = ".,;:!?)]}"


def extract_sway_url(issue_body: str) -> str:
    urls = [
        match.rstrip(TRAILING_URL_PUNCTUATION)
        for match in ISSUE_URL_PATTERN.findall(issue_body)
    ]
    if len(urls) != 1:
        raise ValueError("Issue body must contain exactly one Sway URL.")

    url = urls[0]
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as error:
        raise ValueError("Issue body contains an invalid Sway URL.") from error

    if (
        parsed.scheme != "https"
        or parsed.hostname != "sway.cloud.microsoft"
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
        or parsed.path in ("", "/")
        or "\\" in url
    ):
        raise ValueError(
            "URL must be an HTTPS link to a Sway at sway.cloud.microsoft."
        )

    return url


def main() -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        raise RuntimeError("GITHUB_OUTPUT is required.")

    issue_body = os.environ.get("ISSUE_BODY", "")
    sway_url = extract_sway_url(issue_body)
    with Path(output_path).open("a", encoding="utf-8") as output:
        output.write(f"url={sway_url}\n")


if __name__ == "__main__":
    main()
