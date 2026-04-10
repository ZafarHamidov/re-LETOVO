# Zafar Academic Portfolio

This project turns the evidence files in this folder into a clean, static academic portfolio dashboard for Zafar. It is designed for two use cases:

- a motivating personal dashboard for day-to-day focus and progress
- a serious public-facing portfolio page for mentors, counselors, and admissions support

## Project structure

```text
re-LETOVO/
  index.html
  styles.css
  script.js
  source-materials/
    ...original evidence folders and prompt files
  data/
    profile.json
  docs/
    inventory.json
    extracted_data.json
    normalized_profile.json
    evidence-index.json
    readiness_methodology.md
  scripts/
    build_profile.py
```

## How to refresh the data

1. Drop new source documents into `source-materials/`.
2. Run:

```powershell
python .\scripts\build_profile.py
```

## Run locally

Because the site fetches JSON, open it through a local server instead of double-clicking `index.html`.

```powershell
python -m http.server 8000
```

Then open `http://localhost:8000`.

## Publish with GitHub Pages

1. Push this folder to a GitHub repository.
2. In GitHub, open `Settings` -> `Pages`.
3. Set `Build and deployment` to `GitHub Actions`.
4. Push to `main`; the workflow in `.github/workflows/pages.yml` will rebuild the profile and deploy the site.
5. Rebuild locally before each push when new evidence is added so you can review the generated output first.

## Privacy guidance

Use two modes:

- Public showcase: high-level summaries, selected achievements, safe certificates, project overviews
- Private evidence version: detailed school reports, internal commentary, sensitive PDFs, contracts, identifiers

Before publishing, manually review birth dates, IDs, candidate numbers, internal school comments, and any contract or portal export that should stay private.

## Suggested organization

- Keep the website and generated artifacts at the repo root.
- Keep all original source evidence inside `source-materials/`.
- Re-run the build script after moving or adding evidence so all relative links stay current.
