# WebScraper

A multi-strategy web scraper that extracts institution names, research centre names, and director/PI names from a list of URLs. Uses Selenium for JavaScript-rendered pages, BeautifulSoup for HTML parsing, and spaCy for NLP-assisted text processing.

Built as the second stage of a lead-generation pipeline, consuming URLs from [URL Finder](https://github.com/BVarvill/URL-Finder) and outputting structured contact data for downstream enrichment.

## What it does

For each URL it:

1. Fetches the page using headless Chrome (handles JS-rendered sites)
2. Extracts the university/institution name via page title, meta tags, and text blocks
3. Extracts the research centre name using the same multi-strategy approach
4. Identifies director/PI names by searching for names near role keywords
5. Saves all results to `scraped_results.csv`

## Setup

**Install Python dependencies:**
```bash
pip install selenium webdriver-manager beautifulsoup4 spacy pandas
python -m spacy download en_core_web_lg
```

> `webdriver-manager` installs ChromeDriver automatically — no manual path configuration needed.

## Usage

Edit the `URLS` list in `webscraper.py` with your target URLs, then run:

```bash
python webscraper.py
```

Results are saved to `scraped_results.csv` with columns: `url`, `director_name`, `university`, `center`.

## Output format

| url | director_name | university | center |
|-----|--------------|------------|--------|
| https://... | Dr Jane Smith | University of Leeds | Quantum Computing Lab |

## Extraction strategy

The scraper attempts extraction in order of reliability:

1. **Page `<title>` tag** — most reliable source for institution names
2. **`<meta name="description">`** — useful fallback
3. **Anchor link text** — catches navigation links to parent institutions
4. **Heading/paragraph text** — broadest fallback using keyword matching

Director names are found by scanning the full page text for patterns like `"[Name] Director"` or `"[Name] Principal Investigator"`.

## Pipeline context

```
URL Finder  →  WebScraper  →  Lead Enrichment Pipeline
```

Output from this script feeds into the [conference-intelligence-pipeline](https://github.com/BVarvill/conference-intelligence-pipeline) for LLM-based scoring and personalised email generation.

