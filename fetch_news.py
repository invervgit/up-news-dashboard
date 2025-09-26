#!/usr/bin/env python3
"""
Enhanced news fetcher for the Uttar Pradesh News Dashboard.

This script downloads a list of RSS feeds covering politics, governance
and judicial matters in Uttar Pradesh.  It extracts basic fields from
each feed and attempts to fetch additional content from the linked
article when the RSS description is too terse.  A simple keyword‑based
classifier assigns each story to one of four categories defined by the
user.  A robust district mapping derived from the feed URL ensures
that every story can be filtered by district on the front‑end.  The
aggregated stories are deduplicated by URL and written to
`data/news.json`.

Key improvements over the original script:

* **Richer summaries:** When an RSS item contains only a one‑line
  description, the script fetches the article page and extracts the
  first few paragraphs.  This produces a paragraph‑length summary
  rather than a single sentence.
* **Stronger classification:** The category keywords have been
  expanded to reflect the user’s requested party mappings for
  opposition, NDA, governance and judicial cases.
* **Explicit district mapping:** A deterministic function derives a
  human‑readable district name from each feed URL.  This ensures
  consistency between the district filter and the feed list.

The script remains dependency‑free beyond `requests` and
`beautifulsoup4`, both of which are available in the default Python
environment.
"""

import json
import re
from datetime import datetime, timezone
from typing import Dict, List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


######################################################################
# Configuration
######################################################################

#: A complete list of RSS feeds to ingest.  Each entry in this list
#  corresponds to a news source or district feed that has been
#  validated to return a working RSS document.  If you add or remove
#  feeds, remember to update the FEED_DISTRICT_MAP function accordingly
#  so that districts are reported accurately.
FEEDS: List[str] = [
    "https://www.bhaskarenglish.in/rss-v1--category-16346.xml",
    "https://www.yugmarg.com/rssfeed/uttarpradesh-rss.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/rssfeed.xml",
    "https://www.bhaskar.com/rss-v1--category-2052.xml",
    "https://www.amarujala.com/rss/uttar-pradesh.xml",
    "https://www.amarujala.com/rss/gorakhpur.xml",
    "https://www.amarujala.com/rss/lucknow.xml",
    "https://www.amarujala.com/rss/amroha.xml",
    "https://www.amarujala.com/rss/amethi.xml",
    "https://www.amarujala.com/rss/ambedkar-nagar.xml",
    "https://www.amarujala.com/rss/faizabad.xml",
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
    "https://www.amarujala.com/rss/sonbhadra.xml",
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
    "https://www.amarujala.com/rss/ghaziabad.xml",
]

#: Mapping from feed URL to a human‑friendly district name.  The
#  function below attempts to infer the district name automatically.
#  However if you wish to override the inference for a particular feed,
#  add an entry here: FEED_DISTRICT_MAP[feed_url] = "District Name".
FEED_DISTRICT_MAP: Dict[str, str] = {
    # Examples:
    # "https://www.bhaskar.com/rss-v1--category-2052.xml": "Uttar Pradesh",
}


######################################################################
# Classification configuration
######################################################################

# Keyword lists used for naive text classification.  Each list should
# contain case‑insensitive tokens that, when present in a story, hint
# towards a particular category.  The script stops at the first match
# encountered when evaluating categories in the order they are defined
# below.  Stories with no keyword matches are labelled "Uncategorised".
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Opposition Activity": [
        # Parties and leaders commonly associated with the opposition
        "samajwadi", "sp", "congress", "inc", "aazad samaj", "bsp", "aimim",
        "ad(k)", "akhilesh", "mayawati", "azad", "owaisi", "rahul", "gandhi",
        "priyanka", "chalisa", "aazad samaj party", "azad samaj", "sp chief",
        "inc leader", "up congress", " विपक्ष", "विपक्ष", "सपा", "बसपा",
    ],
    "NDA Activity": [
        "bjp", "nda", "sbsp", "ad(s)", "rld", "nishad", "modi", "yogi",
        "pm modi", "amit shah", "jp nadda", "apna dal", "nath", "भाजपा", "योगी",
        "मोदी", "आदित्यनाथ",
    ],
    "Governance issues": [
        "development", "infrastructure", "scheme", "mission", "project",
        "programme", "program", "road", "bridge", "hospital", "demand",
        "protest", "demonstration", "struggle", "complaint", "scheme",
        "health", "education", "school", "college", "budget", "fund",
        "electricity", "water", "environment", "administration", "government",
        "policy", "minister", "district magistrate", "commissioner",
        "मुख्यमंत्री", "सरकार", "विकास", "योजना",
    ],
    "Judicial cases": [
        "court", "high court", "supreme court", "verdict", "judgment", "judge",
        "petition", "litigation", "lawsuit", "legal", "case", "mp mla court",
        "decision", "hearings", "bench", "arrest", "bail", "अदालत", "न्यायालय",
    ],
}


######################################################################
# Utility functions
######################################################################

def clean_text(text: str) -> str:
    """Normalize whitespace and remove HTML tags."""
    soup = BeautifulSoup(text, "html.parser")
    return re.sub(r"\s+", " ", soup.get_text(separator=" ")).strip()


def summarise(description: str, link: str, max_sentences: int = 3, max_words: int = 80) -> str:
    """
    Generate a summary for an article.  If the RSS description is
    unusually short, attempt to fetch the article page and extract the
    first few paragraphs.  The result is trimmed to a fixed number of
    sentences and words.  Any HTML tags are stripped.

    Args:
        description: The description text from the RSS feed.
        link: The URL of the full article.
        max_sentences: Maximum number of sentences to include in the summary.
        max_words: Maximum number of words to include in the summary.

    Returns:
        A cleaned, truncated summary string.
    """
    cleaned = clean_text(description or "")
    # If the description is very short (one or two sentences), fetch the article
    if len(cleaned.split()) < 30 and link:
        try:
            resp = requests.get(link, timeout=10)
            resp.raise_for_status()
            page = BeautifulSoup(resp.content, "html.parser")
            paragraphs = page.find_all('p')
            article_text = " ".join(p.get_text(separator=" ", strip=True) for p in paragraphs)
            article_text = clean_text(article_text)
            # If we found meaningful text, use it instead of the short description
            if len(article_text.split()) > len(cleaned.split()):
                cleaned = article_text
        except Exception:
            # Fall back to the original cleaned description
            pass
    # Split into sentences using punctuation (including Hindi danda)
    sentences = re.split(r"[\.\!\?\u0964\u0965]+\s*", cleaned)
    sentences = [s.strip() for s in sentences if s.strip()]
    selected = sentences[:max_sentences]
    summary = " ".join(selected)
    words = summary.split()
    summary_trimmed = " ".join(words[:max_words])
    if len(words) > max_words:
        summary_trimmed += "..."
    return summary_trimmed


def parse_pubdate(pubdate: str) -> str:
    """Parse publication date into ISO‑8601 format (UTC)."""
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


def infer_district_from_feed(url: str) -> str:
    """
    Deduce a human‑friendly district name from an RSS feed URL.

    This helper examines the path of the feed URL to extract a slug
    representing the district.  Hyphens are replaced with spaces and the
    result is title‑cased.  If no sensible district can be found the
    function falls back to "Uttar Pradesh".

    Args:
        url: The RSS feed URL.

    Returns:
        A district name suitable for display in the UI.
    """
    # Check explicit overrides first
    if url in FEED_DISTRICT_MAP:
        return FEED_DISTRICT_MAP[url]

    try:
        parsed = urlparse(url)
        path = parsed.path
        segments = [seg for seg in path.split('/') if seg]
        # Patterns to ignore when guessing the district
        ignore = set(["rssfeed.xml", "rss", "feed", "feeds", "news", "uttar-pradesh", "uttar pradesh"])
        # Look for a segment that ends in '-news' (Patrika)
        for seg in segments:
            if seg.endswith('-news'):
                district_slug = seg.rsplit('-', 1)[0]
                return district_slug.replace('-', ' ').title()
        # For Amar Ujala RSS: last segment before .xml is the district
        if segments and segments[-1].endswith('.xml'):
            district_slug = segments[-1].split('.')[0]
            if district_slug not in ignore:
                return district_slug.replace('-', ' ').title()
        # For Live Hindustan: segment after 'uttar-pradesh'
        if 'uttar-pradesh' in segments:
            idx = segments.index('uttar-pradesh')
            if idx + 1 < len(segments):
                slug = segments[idx + 1]
                if slug not in ignore:
                    return slug.replace('-', ' ').title()
    except Exception:
        pass
    # Default
    return "Uttar Pradesh"


def extract_domain(url: str) -> str:
    """Extract domain name from a URL."""
    try:
        return urlparse(url).netloc
    except Exception:
        return "Unknown"


def extract_source(domain: str) -> str:
    """Derive human‑friendly source name from the domain."""
    if not domain:
        return "Unknown"
    domain = domain.lower().replace("www.", "").split(".")[-2].replace("-", " ").title()
    return domain


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
    district = infer_district_from_feed(url)

    stories: List[Dict[str, str]] = []
    for item in items:
        try:
            title = item.find("title").get_text(strip=True)
            link = item.find("link").get_text(strip=True)
            description_tag = item.find("description")
            description = description_tag.get_text(strip=True) if description_tag else ""
            pubdate_tag = item.find("pubDate")
            pubdate = pubdate_tag.get_text(strip=True) if pubdate_tag else ""
            summary = summarise(description, link)
            category = classify(f"{title} {description} {summary}")
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
        except Exception:
            # Skip malformed items gracefully
            continue
    return stories


def aggregate_feeds() -> List[Dict[str, str]]:
    """Aggregate and deduplicate articles from all RSS feeds."""
    seen_links = set()
    aggregated: List[Dict[str, str]] = []
    for feed_url in FEEDS:
        stories = parse_feed(feed_url)
        for story in stories:
            link = story.get("link")
            if link and link not in seen_links:
                seen_links.add(link)
                aggregated.append(story)
    # Sort by publication date descending
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
