"""
WebScraper
----------
Given a list of URLs, extracts institution names, research centre names,
and director/PI names using BeautifulSoup (HTML parsing) and spaCy (NLP).

Outputs results to scraped_results.csv.

Usage:
    python webscraper.py

Requirements:
    pip install selenium webdriver-manager beautifulsoup4 spacy pandas
    python -m spacy download en_core_web_lg
"""

import re
import time

import pandas as pd
import spacy
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

nlp = spacy.load("en_core_web_lg")

UNIVERSITY_KEYWORDS = ["university", "college", "institute", "academy", "school", "campus", "faculty"]
CENTER_KEYWORDS = ["center", "centre", "lab", "institute", "department", "group"]
DIRECTOR_KEYWORDS = ["director", "head of", "program manager", "lead researcher", "principal investigator"]


def fetch_dynamic_page(url: str) -> str | None:
    """Fetch a JavaScript-rendered page using headless Chrome."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        time.sleep(3)
        return driver.page_source
    except Exception as e:
        print(f"  Failed to fetch {url}: {e}")
        return None
    finally:
        driver.quit()


def parse_page(html: str) -> list[str]:
    """Extract visible text blocks from heading and paragraph tags."""
    soup = BeautifulSoup(html, "html.parser")
    return [tag.get_text().strip() for tag in soup.find_all(["h1", "h2", "h3", "p"])]


def extract_university_and_center(html: str) -> dict:
    """
    Attempt to identify university and centre names from the page.

    Strategy (in order of preference):
      1. Parse <title> tag and split on delimiters
      2. Check <meta name="description">
      3. Scan anchor link text
      4. Scan heading/paragraph text blocks
    """
    soup = BeautifulSoup(html, "html.parser")
    university, center = None, None

    # 1. Try page title
    title_tag = soup.find("title")
    if title_tag:
        for part in re.split(r"[:|\-]", title_tag.get_text()):
            part = part.strip()
            if not university and any(kw in part.lower() for kw in UNIVERSITY_KEYWORDS):
                university = part
            if not center and any(kw in part.lower() for kw in CENTER_KEYWORDS):
                center = part
        if university or center:
            return {"university": university, "center": center}

    # 2. Try meta description
    meta = soup.find("meta", attrs={"name": "description"})
    if meta:
        meta_text = meta.get("content", "").lower()
        if any(kw in meta_text for kw in UNIVERSITY_KEYWORDS):
            university = meta_text
        if any(kw in meta_text for kw in CENTER_KEYWORDS):
            center = meta_text
        if university or center:
            return {"university": university, "center": center}

    # 3. Scan anchor links
    for link in soup.find_all("a", href=True):
        link_text = link.get_text().lower()
        if not university and any(kw in link_text for kw in UNIVERSITY_KEYWORDS):
            university = link_text.strip()
            break

    # 4. Scan text blocks
    for tag in soup.find_all(["h1", "h2", "h3", "p"]):
        text = tag.get_text().strip().lower()
        if not university and any(kw in text for kw in UNIVERSITY_KEYWORDS):
            university = text.capitalize()
        if not center and any(kw in text for kw in CENTER_KEYWORDS):
            center = text.capitalize()

    return {"university": university, "center": center}


def extract_director_name(html: str) -> str | None:
    """
    Search the page text for a name appearing near a director/PI keyword.
    Uses a simple regex rather than NER for speed.
    """
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()

    for keyword in DIRECTOR_KEYWORDS:
        pattern = re.compile(rf"([A-Za-z\s]{{3,40}?)\s*{re.escape(keyword)}", re.IGNORECASE)
        matches = pattern.findall(text)
        if matches:
            return matches[0].strip()

    return None


def scrape_url(url: str) -> dict:
    """Fetch a single URL and return extracted fields."""
    print(f"Processing: {url}")
    html = fetch_dynamic_page(url)
    if html is None:
        return {"url": url, "error": "Failed to fetch page"}

    info = extract_university_and_center(html)
    director = extract_director_name(html)

    return {
        "url": url,
        "director_name": director,
        "university": info.get("university"),
        "center": info.get("center"),
    }


def scrape_multiple_sites(urls: list[str]) -> list[dict]:
    """Scrape a list of URLs and return results."""
    return [scrape_url(url) for url in urls]


# ── Example URLs ───────────────────────────────────────────────────────────────
URLS = [
    "https://www.nqcc.ac.uk/updates/ukri-appoints-national-quantum-computing-centre-director/",
    "https://www.tii.ae/quantum",
    "https://www.kcl.ac.uk/nmes/research/kings-quantum",
    "https://www.ucl.ac.uk/quantum/about",
    "https://www.sussex.ac.uk/research/centres/sussex-centre-for-quantum-technologies/people",
    "https://www.gla.ac.uk/research/az/quantumtechnology/about/",
]

if __name__ == "__main__":
    results = scrape_multiple_sites(URLS)
    df = pd.DataFrame(results)
    df.to_csv("scraped_results.csv", index=False)
    print(f"\nDone. {len(df)} results saved to scraped_results.csv")
    print(df.to_string())
