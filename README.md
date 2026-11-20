# sway2pngs

Take a Sway and turn it into a series of numbered 1920x1080 PNGs to put into Xibo.

## Browser screenshot workflow

This repository now includes a small Playwright-based CLI that:

- opens a Sway in a real browser
- uses a 1920x1080 viewport by default
- navigates through the Sway's numbered section menu one section at a time
  (falling back to scrolling a viewport at a time for Sways without a section menu)
- saves each view as a numbered PNG, using `Page-Title-YYYY-MM-DD-slide-001.png`
  by default
- creates a ZIP archive containing the captured PNGs in the same output directory

## Usage

Install dependencies and browser binaries:

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Capture a Sway into `./output`:

```bash
python -m sway2pngs "https://sway.cloud.microsoft/KwtjdSNJu9YoNoWc"
```

Useful options:

```bash
python -m sway2pngs "https://sway.cloud.microsoft/your-sway-id" \
  --output-dir ./pngs \
  --prefix section \
  --wait-ms 1500
```

Use `--prefix` to choose a different filename prefix; numbering is appended automatically.
The matching ZIP archive is written beside the PNGs, for example `section.zip`.

## Capture from a GitHub issue

The `Capture Sway from issue` workflow can capture a Sway and publish its ZIP
as a GitHub Release asset:

1. Create an issue containing exactly one HTTPS URL from
   `sway.cloud.microsoft`.
2. Add the `sway-capture` label to the issue.
3. When the workflow completes, find the ZIP under the repository's Releases.

The workflow creates a separate release for each run. Its release tag includes
the issue number and workflow run, so rerunning a job does not overwrite an
earlier release.

Before using the workflow, create the `sway-capture` label in the repository
and allow the workflow token to publish releases:

1. In the repository, open **Settings → Actions → General**.
2. Under **Workflow permissions**, select **Read and write permissions** and
   save. The workflow limits this to `contents: write` in the release job;
   the capture job only has `contents: read`.

Only add the label to issues you intend to process. The workflow rejects issue
bodies that do not contain exactly one URL on the Sway domain.
