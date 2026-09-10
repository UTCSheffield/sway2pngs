# sway2pngs

Take a Sway and turn it into a series of numbered 1920x1080 PNGs to put into Xibo.

## Browser screenshot workflow

This repository now includes a small Playwright-based CLI that:

- opens a Sway in a real browser
- uses a 1920x1080 viewport by default
- scrolls through the page a viewport at a time
- saves each view as a numbered PNG

## Usage

Install dependencies and browser binaries:

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Capture a Sway into `./output`:

```bash
python -m sway2pngs "https://sway.cloud.microsoft/your-sway-id"
```

Useful options:

```bash
python -m sway2pngs "https://sway.cloud.microsoft/your-sway-id" \
  --output-dir ./pngs \
  --prefix section \
  --wait-ms 1500
```
