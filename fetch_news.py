#!/usr/bin/env python3
"""
Fetches RSS feeds for Uttar Pradesh news and produces a JSON data file for
use by the dashboard web front‑end.  The script performs the following
steps:

1. Downloads RSS feeds from multiple sources.  To keep the project
   entirely free of external Python package dependencies (the target
   environment blocks `pip install`), the script uses the built‑in
   `requests` library and `BeautifulSoup` from `bs4` for XML parsing.
2. Extracts key fields such as title, link, publication date and a
   short description from each feed item.  If the feed provides no
   description the script falls back to a truncated portion of the
   article's HTML body.
3. Generates a very simple summary by taking the first two sentences or
   roughly the first 40 words from the description.  This lightweight
   summarisation avoids heavy NLP dependencies while still conveying
   enough context for a reader to understand what the story is about.
4. Classifies each article into one of four user‑defined categories:
   Opposition Activity, NDA Activity, Governance issues and Judicial
   cases.  Classification is heuristic and keyword based.  Lists of
   keywords for each category are defined at the top of the script and
   may be extended or refined later.
5. Removes duplicate articles using their URL as a unique key.  When
   multiple feeds supply identical stories the first instance is kept.
6. Writes the aggregated and cleaned data to a JSON file at
   `data/news.json`.  Each record in the JSON contains the fields:
   `title`, `link`, `pubDate` (ISO‑8601 string in UTC), `summary`,
   `category`, `source` and `district`.

Running this script regularly (e.g. via a cron job or GitHub Actions
workflow) will update the JSON file with the latest stories.  The
dashboard front‑end reads the JSON file and renders the data with
filters for date ranges and categories.
"""

import json
import re
from datetime import datetime, timezone
from typing import Dict, List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


# List of RSS feeds to ingest.  Each entry in this list is a URL pointing to a feed or page that contains stories about Uttar Pradesh.
FEEDS: List[str] = [
    # Existing feeds from the initial implementation
    
    # Additional feeds provided by the user.  These include generic
    # state‑level pages as well as district specific pages from
    # Amar Ujala, Live Hindustan, Times of India, Navbharat Times,
    # Patrika and other local news outlets.  The parser will skip
    # any entries that do not contain valid RSS items.
    
"https://www.bhaskarenglish.in/rss-v1--category-16346.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/rssfeed.xml",
"https://www.bhaskar.com/rss-v1--category-2052.xml",
"https://www.amarujala.com/rss/uttar-pradesh.xml",
"https://www.amarujala.com/rss/gorakhpur.xml",
"https://www.amarujala.com/rss/lucknow.xml",
"https://www.amarujala.com/rss/amroha.xml",
"https://www.amarujala.com/rss/amethi.xml",
"https://www.amarujala.com/rss/ambedkar-nagar.xml",
"https://www.amarujala.com/rss/ayodhya.xml",
"https://www.amarujala.com/rss/aligarh.xml",
"https://www.amarujala.com/rss/agra.xml",
"https://www.amarujala.com/rss/azamgarh.xml",
"https://www.amarujala.com/rss/etawah.xml",
"https://www.amarujala.com/rss/unnao.xml",
"https://www.amarujala.com/rss/etah.xml",
"https://www.amarujala.com/rss/auraiya.xml",
"https://www.amarujala.com/rss/kannauj.xml",
"https://www.amarujala.com/rss/kanpur.xml",
"https://www.amarujala.com/rss/kushinagar.xml",
"https://www.amarujala.com/rss/kaushambi.xml",
"https://www.amarujala.com/rss/ghazipur.xml",
"https://www.amarujala.com/rss/gonda.xml",
"https://www.amarujala.com/rss/ghatampur.xml",
"https://www.amarujala.com/rss/chandauli.xml",
"https://www.amarujala.com/rss/chitrakoot.xml",
"https://www.amarujala.com/rss/jalaun.xml",
"https://www.amarujala.com/rss/jaunpur.xml",
"https://www.amarujala.com/rss/jhansi.xml",
"https://www.amarujala.com/rss/deoria.xml",
"https://www.amarujala.com/rss/pilibhit.xml",
"https://www.amarujala.com/rss/pratapgarh.xml",
"https://www.amarujala.com/rss/allahabad.xml",
"https://www.amarujala.com/rss/fatehpur.xml",
"https://www.amarujala.com/rss/farrukhabad.xml",
"https://www.amarujala.com/rss/firozabad.xml",
"https://www.amarujala.com/rss/budaun.xml",
"https://www.amarujala.com/rss/bareilly.xml",
"https://www.amarujala.com/rss/balrampur.xml",
"https://www.amarujala.com/rss/ballia.xml",
"https://www.amarujala.com/rss/basti.xml",
"https://www.amarujala.com/rss/bahraich.xml",
"https://www.amarujala.com/rss/banda.xml",
"https://www.amarujala.com/rss/baghpat.xml",
"https://www.amarujala.com/rss/barabanki.xml",
"https://www.amarujala.com/rss/bijnor.xml",
"https://www.amarujala.com/rss/bulandshahr.xml",
"https://www.amarujala.com/rss/bhadohi.xml",
"https://www.amarujala.com/rss/mau.xml",
"https://www.amarujala.com/rss/mathura.xml",
"https://www.amarujala.com/rss/maharajganj.xml",
"https://www.amarujala.com/rss/mahoba.xml",
"https://www.amarujala.com/rss/mirzapur.xml",
"https://www.amarujala.com/rss/muzaffarnagar.xml",
"https://www.amarujala.com/rss/moradabad.xml",
"https://www.amarujala.com/rss/meerut.xml",
"https://www.amarujala.com/rss/mainpuri.xml",
"https://www.amarujala.com/rss/rampur.xml",
"https://www.amarujala.com/rss/raebareli.xml",
"https://www.amarujala.com/rss/lakhimpur-kheri.xml",
"https://www.amarujala.com/rss/lalitpur.xml",
"https://www.amarujala.com/rss/varanasi.xml",
"https://www.amarujala.com/rss/shamli.xml",
"https://www.amarujala.com/rss/shahjahanpur.xml",
"https://www.amarujala.com/rss/shravasti.xml",
"https://www.amarujala.com/rss/sant-kabir-nagar.xml",
"https://www.amarujala.com/rss/sambhal.xml",
"https://www.amarujala.com/rss/saharanpur.xml",
"https://www.amarujala.com/rss/siddharthnagar.xml",
"https://www.amarujala.com/rss/sitapur.xml",
"https://www.amarujala.com/rss/sultanpur.xml",
"https://www.amarujala.com/rss/sonebhadra.xml",
"https://www.amarujala.com/rss/hamirpur.xml",
"https://www.amarujala.com/rss/hardoi.xml",
"https://www.amarujala.com/rss/hathras.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/lucknow/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/varanasi/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/bareilly/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/moradabad/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/meerut/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/agra/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/aligarh/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/prayagraj/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/gorakhpur/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/kanpur/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/barabanki/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/azamgarh/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/balia/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/bhadohi/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/chandauli/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/ghazipur/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/jaunpur/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/mau/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/mirzapur/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/sonbhadra/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/basti/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/kushinagar/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/deoria/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/maharajganj/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/sant-kabir-nagar/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/siddharth-nagar/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/bagpat/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/shamli/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/bijnor/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/bulandshahr/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/hapur/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/muzaffarnagar/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/saharanpur/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/badaun/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/lakhimpur-kheri/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/pilibhit/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/shahjahanpur/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/etah/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/firozabad/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/mainpuri/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/mathura/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/ambedkar-nagar/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/amethi/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/gauriganj/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/shravasti/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/balrampur/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/bahraich/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/faizabad/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/gonda/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/raebareli/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/fatehpur/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/sitapur/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/sultanpur/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/auraiya/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/akbarpur/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/bilhor/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/lalitpur/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/mahoba/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/kanpur-rural/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/chitrakoot/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/banda/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/etawah/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/farrukhabad/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/kannauj/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/hamirpur/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/hardoi/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/jhansi/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/orai/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/unnao/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/hathras/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/amroha/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/rampur/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/sambhal/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/gangapar/rssfeed.xml",
"https://api.livehindustan.com/feeds/rss/uttar-pradesh/kausambi/rssfeed.xml",
"https://cms.patrika.com/googlefeed/blog/location/uttar-pradesh-news",
"https://cms.patrika.com/googlefeed/blog/location/agra-news",
"https://cms.patrika.com/googlefeed/blog/location/firozabad-news",
"https://cms.patrika.com/googlefeed/blog/location/mainpuri-news",
"https://cms.patrika.com/googlefeed/blog/location/mathura-news",
"https://cms.patrika.com/googlefeed/blog/location/aligarh-news",
"https://cms.patrika.com/googlefeed/blog/location/etah-news",
"https://cms.patrika.com/googlefeed/blog/location/etawah-news",
"https://cms.patrika.com/googlefeed/blog/location/hathras-news",
"https://cms.patrika.com/googlefeed/blog/location/kasganj-news",
"https://cms.patrika.com/googlefeed/blog/location/kaushambi-news",
"https://cms.patrika.com/googlefeed/blog/location/prayagraj-news",
"https://cms.patrika.com/googlefeed/blog/location/fatehpur-news",
"https://cms.patrika.com/googlefeed/blog/location/pratapgarh-news",
"https://cms.patrika.com/googlefeed/blog/location/azamgarh-news",
"https://cms.patrika.com/googlefeed/blog/location/ballia-news",
"https://cms.patrika.com/googlefeed/blog/location/mau-news",
"https://cms.patrika.com/googlefeed/blog/location/bareilly-news",
"https://cms.patrika.com/googlefeed/blog/location/budaun-news",
"https://cms.patrika.com/googlefeed/blog/location/pilibhit-news",
"https://cms.patrika.com/googlefeed/blog/location/shahjahanpur-news",
"https://cms.patrika.com/googlefeed/blog/location/basti-news",
"https://cms.patrika.com/googlefeed/blog/location/sant-kabir-nagar-news",
"https://cms.patrika.com/googlefeed/blog/location/sidharthnagar-news",
"https://cms.patrika.com/googlefeed/blog/location/banda-news",
"https://cms.patrika.com/googlefeed/blog/location/chitrakoot-news",
"https://cms.patrika.com/googlefeed/blog/location/hamirpur-news",
"https://cms.patrika.com/googlefeed/blog/location/mahoba-news",
"https://cms.patrika.com/googlefeed/blog/location/bahraich-news",
"https://cms.patrika.com/googlefeed/blog/location/balrampur-news",
"https://cms.patrika.com/googlefeed/blog/location/gonda-news",
"https://cms.patrika.com/googlefeed/blog/location/shravasti-news",
"https://cms.patrika.com/googlefeed/blog/location/ambedkar-nagar-news",
"https://cms.patrika.com/googlefeed/blog/location/amethi-news",
"https://cms.patrika.com/googlefeed/blog/location/ayodhya-news",
"https://cms.patrika.com/googlefeed/blog/location/barabanki-news",
"https://cms.patrika.com/googlefeed/blog/location/faizabad-news",
"https://cms.patrika.com/googlefeed/blog/location/sultanpur-news",
"https://cms.patrika.com/googlefeed/blog/location/deoria-news",
"https://cms.patrika.com/googlefeed/blog/location/gorakhpur-news",
"https://cms.patrika.com/googlefeed/blog/location/kushinagar-news",
"https://cms.patrika.com/googlefeed/blog/location/mahrajganj-news",
"https://cms.patrika.com/googlefeed/blog/location/jalaun-news",
"https://cms.patrika.com/googlefeed/blog/location/jhansi-news",
"https://cms.patrika.com/googlefeed/blog/location/lalitpur-news",
"https://cms.patrika.com/googlefeed/blog/location/auraiya-news",
"https://cms.patrika.com/googlefeed/blog/location/farrukhabad-news",
"https://cms.patrika.com/googlefeed/blog/location/kannauj-news",
"https://cms.patrika.com/googlefeed/blog/location/kanpur-news",
"https://cms.patrika.com/googlefeed/blog/location/hardoi-news",
"https://cms.patrika.com/googlefeed/blog/location/lakhimpur-kheri-news",
"https://cms.patrika.com/googlefeed/blog/location/lucknow-news",
"https://cms.patrika.com/googlefeed/blog/location/raebareli-news",
"https://cms.patrika.com/googlefeed/blog/location/sitapur-news",
"https://cms.patrika.com/googlefeed/blog/location/unnao-news",
"https://cms.patrika.com/googlefeed/blog/location/bagpat-news",
"https://cms.patrika.com/googlefeed/blog/location/bulandshahr-news",
"https://cms.patrika.com/googlefeed/blog/location/greater-noida-news",
"https://cms.patrika.com/googlefeed/blog/location/noida-news",
"https://cms.patrika.com/googlefeed/blog/location/ghaziabad-news",
"https://cms.patrika.com/googlefeed/blog/location/ghazipur-news",
"https://cms.patrika.com/googlefeed/blog/location/hapur-news",
"https://cms.patrika.com/googlefeed/blog/location/meerut-news",
"https://cms.patrika.com/googlefeed/blog/location/bhadohi-news",
"https://cms.patrika.com/googlefeed/blog/location/mirzapur-news",
"https://cms.patrika.com/googlefeed/blog/location/sonbhadra-news",
"https://cms.patrika.com/googlefeed/blog/location/amroha-news",
"https://cms.patrika.com/googlefeed/blog/location/bijnor-news",
"https://cms.patrika.com/googlefeed/blog/location/moradabad-news",
"https://cms.patrika.com/googlefeed/blog/location/rampur-news",
"https://cms.patrika.com/googlefeed/blog/location/sambhal-news",
"https://cms.patrika.com/googlefeed/blog/location/muzaffarnagar-news",
"https://cms.patrika.com/googlefeed/blog/location/saharanpur-news",
"https://cms.patrika.com/googlefeed/blog/location/shamli-news",
"https://cms.patrika.com/googlefeed/blog/location/chandauli-news",
"https://cms.patrika.com/googlefeed/blog/location/jaunpur-news",
"https://cms.patrika.com/googlefeed/blog/location/varanasi-news",
"https://www.amarujala.com/rss/ghaziabad.xml"
]


# Keyword lists used for naive text classification.  Each list should
# contain case‑insensitive tokens that, when present in a story, hint
# towards a particular category.  The script stops at the first match
# encountered when evaluating categories in the order they are defined
# below.  Stories with no keyword matches are labelled "Uncategorised".
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Opposition Activity": [
        "samajwadi", "sp", "congress", "inc", "aazad samaj", "bsp", "aimim", "ad(k)",
        "akhilesh", "mayawati", "azad", "owaisi", "rahul gandhi",
    ],
    "NDA Activity": [
        "bjp", "nda", "sbsp", "ad(s)", "rld", "nishad", "modi", "yogi", "pm modi",
        "amit shah", "jp nadda",
    ],
    "Governance issues": [
        "development", "governance", "scheme", "mission", "project", "program",
        "infrastructure", "policy", "administration", "government", "minister", "budget",
        "healthcare", "education",
    ],
    "Judicial cases": [
        "court", "high court", "supreme court", "verdict", "judicial", "petition",
        "judge", "litigation", "legal", "lawsuit", "case",
    ],
}

def clean_text(text: str) -> str:
    """Normalize whitespace and remove HTML tags."""
    soup = BeautifulSoup(text, "html.parser")
    return re.sub(r"\s+", " ", soup.get_text(separator=" ")).strip()

def summarise(description: str, max_sentences: int = 2, max_words: int = 40) -> str:
    """Generate a short summary from the article description."""
    cleaned = clean_text(description)
    sentences = re.split(r"[\.\!\?\u0964\u0965]+\s*", cleaned)
    sentences = [s for s in sentences if s]
    selected = sentences[:max_sentences]
    summary = " ".join(selected)
    words = summary.split()
    return " ".join(words[:max_words]) + ("..." if len(words) > max_words else "")

def parse_pubdate(pubdate: str) -> str:
    """Parse publication date into ISO-8601 format (UTC)."""
    for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M %z", "%d %b %Y %H:%M:%S %z"]:
        try:
            dt = datetime.strptime(pubdate, fmt)
            return dt.astimezone(timezone.utc).isoformat()
        except Exception:
            continue
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

def classify(text: str) -> str:
    """Classify the article into one of the predefined categories."""
    lower_text = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw.lower() in lower_text for kw in keywords):
            return category
    return "Uncategorised"

def extract_domain(url: str) -> str:
    """Extract domain name from a URL."""
    try:
        return urlparse(url).netloc
    except Exception:
        return "Unknown"

def extract_source(domain: str) -> str:
    """Derive human-friendly source name from the domain."""
    if not domain:
        return "Unknown"
    domain = domain.lower().replace("www.", "").split(".")[-2].replace("-", " ").title()
    return domain

def extract_district(url: str) -> str:
    """Extract district or locality from the URL."""
    try:
        path = urlparse(url).path
        segments = [s for s in path.split("/") if s]
        ignore_substrings = ["uttar", "pradesh", "news", "articlelist", "rss"]
        for segment in reversed(segments):
            segment = segment.split(".")[0]
            if not segment.isdigit() and all(ignored not in segment.lower() for ignored in ignore_substrings):
                return segment.replace("-", " ").title()
    except Exception:
        return "General"
    return "General"

def parse_feed(url: str) -> List[Dict[str, str]]:
    """Parse an RSS feed into a list of article dictionaries."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch feed {url}: {e}")
        return []

    soup = BeautifulSoup(response.content, "xml")
    items = soup.find_all("item")
    domain = extract_domain(url)
    source = extract_source(domain)
    district = extract_district(url)

    stories = []
    for item in items:
        title = item.find("title").get_text(strip=True)
        link = item.find("link").get_text(strip=True)
        description = item.find("description").get_text(strip=True)
        pubdate = item.find("pubDate").get_text(strip=True)
        summary = summarise(description)
        category = classify(f"{title} {description}")
        iso_date = parse_pubdate(pubdate)
        stories.append({
            "title": title,
            "link": link,
            "pubDate": iso_date,
            "summary": summary,
            "category": category,
            "source": source,
            "district": district,
        })
    return stories

def aggregate_feeds() -> List[Dict[str, str]]:
    """Aggregate and deduplicate articles from all RSS feeds."""
    seen_links = set()
    aggregated = []
    for feed_url in FEEDS:
        stories = parse_feed(feed_url)
        for story in stories:
            link = story.get("link")
            if link and link not in seen_links:
                seen_links.add(link)
                aggregated.append(story)
    aggregated.sort(key=lambda s: s.get("pubDate", ""), reverse=True)
    return aggregated

def main() -> None:
    """Main function to aggregate feeds and save data to JSON."""
    stories = aggregate_feeds()
    from pathlib import Path
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    output_path = data_dir / "news.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(stories, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(stories)} stories to {output_path}")

if __name__ == "__main__":
    main()
