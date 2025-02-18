# WebScraper

```python
import spacy
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time

nlp = spacy.load("en_core_web_lg")

def fetch_dynamic_page(url):
    driver_path = r"/Users/benvarvill/Downloads/chromedriver-mac-arm64/chromedriver"
    service = Service(driver_path)
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        time.sleep(3)
        html = driver.page_source
    except Exception as e:
        html = None
    finally:
        driver.quit()
    return html

def parse_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    return [tag.get_text().strip() for tag in soup.find_all(['h1', 'h2', 'h3', 'p'])]

university_keywords = ['university', 'college', 'institute', 'academy', 'school', 'campus', 'faculty']
center_keywords = ['center', 'centre', 'lab', 'institute', 'department', 'group']

def extract_university_and_center(html):
    soup = BeautifulSoup(html, 'html.parser')

    title_tag = soup.find("title")
    if title_tag:
        title_text = title_tag.get_text()
        parts = re.split(r"[:|\-]", title_text)

        university, center = None, None
        for part in parts:
            part = part.strip()
            if any(keyword in part.lower() for keyword in university_keywords):
                university = part
            if any(keyword in part.lower() for keyword in center_keywords):
                center = part
        
        if university or center:
            return {"university": university, "center": center}

    meta_description = soup.find("meta", attrs={"name": "description"})
    if meta_description:
        meta_text = meta_description.get("content", "").lower()
        for keyword in university_keywords:
            if keyword in meta_text:
                university = meta_text
                break
        for keyword in center_keywords:
            if keyword in meta_text:
                center = meta_text
                break

        if university or center:
            return {"university": university, "center": center}

    for link in soup.find_all('a', href=True):
        link_text = link.get_text().lower()
        if any(keyword in link_text for keyword in university_keywords):
            university = link_text.strip()
            break

    text_blocks = soup.find_all(['h1', 'h2', 'h3', 'p'])
    for tag in text_blocks:
        text = tag.get_text().strip().lower()
        if not university and any(keyword in text for keyword in university_keywords):
            university = text.capitalize()
        if not center and any(keyword in text for keyword in center_keywords):
            center = text.capitalize()

    return {"university": university, "center": center}
    
def extract_director_name(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    director_keywords = ['director', 'head of', 'program manager', 'lead researcher', 'principal investigator']
    text = soup.get_text().lower()
    
    for keyword in director_keywords:
        director_pattern = re.compile(rf'([A-Za-z\s]+?)(\s*{keyword}\s*[\w\s]+)', re.IGNORECASE)
        matches = director_pattern.findall(text)
        
        if matches:
            return matches[0][0].strip()
    
    return None

def extract_info(sections, html):
    director_name = extract_director_name(html)
    info = extract_university_and_center(html)
    university_name = info.get("university", None)
    center_name = info.get("center", None)

    return {
        "director_name": director_name,
        "university": university_name,
        "center": center_name
    }

def scrape_multiple_sites(urls):
    results = []
    for url in urls:
        print(f"Processing: {url}")
        try:
            html = fetch_dynamic_page(url)
            if html is None:
                raise Exception("Failed to fetch the page.")
            sections = parse_page(html)
            info = extract_info(sections, html)
            results.append({"url": url, **info})
        except Exception as e:
            results.append({"url": url, "error": str(e)})
    return results

urls = [
    "https://www.nqcc.ac.uk/updates/ukri-appoints-national-quantum-computing-centre-director/",
    "https://www.tii.ae/quantum",
    "https://www.kcl.ac.uk/nmes/research/kings-quantum",
    "https://ae.linkedin.com/in/jamesagrieve",
    "https://www.kcl.ac.uk/news/kings-launches-new-quantum-research-centre",
    "https://www.ucl.ac.uk/quantum/about",
    "https://www.sussex.ac.uk/research/centres/sussex-centre-for-quantum-technologies/people",
    "https://www.ucl.ac.uk/news/2024/dec/quantum-research-hub-healthcare-launched",
    "https://www.gla.ac.uk/research/az/quantumtechnology/about/",
    "https://www.researchprofessionalnews.com/rr-news-uk-research-councils-2021-3-national-quantum-computing-centre-gets-new-director/"
]

results = scrape_multiple_sites(urls)

df = pd.DataFrame(results)
df.to_csv("scraped_results.csv", index=False)

print("Results saved to scraped_results.csv")
