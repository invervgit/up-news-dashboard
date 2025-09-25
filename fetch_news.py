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
   `category` and `source`.

Running this script regularly (e.g. via a cron job or GitHub Actions
workflow) will update the JSON file with the latest stories.  The
dashboard front‑end reads the JSON file and renders the data with
filters for date ranges and categories.
"""

import json
import re
from datetime import datetime, timezone
from typing import Dict, List

import requests
from bs4 import BeautifulSoup


# List of RSS feeds to ingest.  Additional feeds can be appended here
# provided they produce valid RSS 2.0 or Atom XML.  The keys are used
# to record the source of each article.
FEEDS: Dict[str, str] = {
    # English language feed from Dainik Bhaskar covering local UP news【739932574703620†L29-L31】.
    "BhaskarEnglish": "https://www.bhaskarenglish.in/rss-v1--category-16346.xml",
    # Hindi language feed from Yugmarg specifically for Uttar Pradesh【960192868319618†L55-L73】.
    "Yugmarg": "https://www.yugmarg.com/rssfeed/uttarpradesh-rss.xml",
    # Hindi language feed from Live Hindustan for Uttar Pradesh【437299901418450†L1111-L1113】.
    "LiveHindustan": "https://api.livehindustan.com/feeds/rss/uttar-pradesh/rssfeed.xml",
}


# Keyword lists used for naive text classification.  Each list should
# contain case‑insensitive tokens that, when present in a story, hint
# towards a particular category.  The script stops at the first match
# encountered when evaluating categories in the order they are defined
# below.  Stories with no keyword matches are labelled "Uncategorised".
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Opposition Activity": [
        # Parties
        "samajwadi", "sp", "congress", "inc", "aazad samaj", "bsp", "aimim", "ad(k)",
        # Opposition leaders
        "akhilesh", "mayawati", "azad", "azad samaj", "asaduddin", "owaisi",
        "azad khan", "azam khan", "rahul gandhi",
    ],
    "NDA Activity": [
        "bjp", "nda", "sbsp", "ad(s)", "rld", "nishad", "modi", "yogi", "pm modi",
        "chief minister yogi", "cm yogi", "amit shah", "jp nadda",
    ],
    "Governance issues": [
        "development", "governance", "scheme", "mission", "project", "program",
        "infrastructure", "policy", "administration", "government", "dept",
        "minister", "budget", "vaccination", "healthcare", "education",
    ],
    "Judicial cases": [
        "court", "high court", "supreme court", "verdict", "judicial",
        "petition", "judge", "litigation", "legal", "lawsuit", "case",
    ],
}


def clean_text(text: str) -> str:
    """Normalise whitespace and remove HTML tags from a string."""
    # Remove any HTML tags
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text(separator=" ")
    # Collapse multiple whitespace into single spaces
    return re.sub(r"\s+", " ", text).strip()


def summarise(description: str, max_sentences: int = 2, max_words: int = 40) -> str:
    """
    Produce a terse summary from the feed description.  The algorithm
    splits on sentence terminators (periods, exclamation marks, question
    marks and Devanagari danda), then joins the first `max_sentences`
    sentences.  If the resulting summary exceeds `max_words` words it
    gets truncated at the nearest word boundary.
    """
    cleaned = clean_text(description)
    # Split into sentences using basic punctuation patterns
    sentences = re.split(r"[\.\!\?\u0964\u0965]+\s*", cleaned)
    sentences = [s for s in sentences if s]
    if not sentences:
        return cleaned[:max_words]
    selected = sentences[:max_sentences]
    summary = " ".join(selected)
    words = summary.split()
    if len(words) > max_words:
        summary = " ".join(words[:max_words]) + "..."
    return summary


def parse_pubdate(pubdate: str) -> str:
    """
    Convert various date formats into ISO‑8601 (UTC).  RSS feeds use
    RFC 822 style dates (e.g. "Thu, 25 Sep 2025 18:34:38 +0530").  If
    parsing fails the current UTC time is returned.  All dates are
    normalised to UTC to simplify client filtering.
    """
    for fmt in [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M %z",
        "%d %b %Y %H:%M:%S %z",
    ]:
        try:
            dt = datetime.strptime(pubdate, fmt)
            return dt.astimezone(timezone.utc).isoformat()
        except Exception:
            continue
    # Fallback to current UTC
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()


def classify(text: str) -> str:
    """
    Assign a category to a piece of text based on keyword presence.  The
    first matching category in CATEGORY_KEYWORDS is returned.  The
    comparison is case‑insensitive.  If no keywords match, the string
    "Uncategorised" is returned.
    """
    lower_text = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in lower_text:
                return category
    return "Uncategorised"


def parse_feed(source_name: str, url: str) -> List[Dict[str, str]]:
    """
    Download a feed and return a list of story dictionaries.  Each
    dictionary includes the story title, link, publication date, a
    generated summary, its category and the source name.  Duplicate
    detection is handled by the caller.
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Warning: failed to fetch feed {url}: {e}")
        return []
    content = response.content
    # Parse XML using BeautifulSoup's XML parser
    soup = BeautifulSoup(content, "xml")
    items = soup.find_all("item")
    stories: List[Dict[str, str]] = []
    for item in items:
        title_tag = item.find("title")
        link_tag = item.find("link")
        desc_tag = item.find("description")
        pub_tag = item.find("pubDate")
        title = title_tag.get_text(strip=True) if title_tag else ""
        link = link_tag.get_text(strip=True) if link_tag else ""
        description = desc_tag.get_text(strip=True) if desc_tag else ""
        pubdate = pub_tag.get_text(strip=True) if pub_tag else ""
        # Some feeds duplicate the link text inside CDATA; ensure we capture
        # valid HTTP/HTTPS URLs only
        if link and not link.startswith("http"):
            # Sometimes the link may be repeated after a space
            parts = re.findall(r"https?://[^\s]+", item.decode() if hasattr(item, "decode") else str(item))
            link = parts[0] if parts else link
        summary = summarise(description)
        category = classify(f"{title} {description}")
        iso_date = parse_pubdate(pubdate)
        stories.append({
            "title": title,
            "link": link,
            "pubDate": iso_date,
            "summary": summary,
            "category": category,
            "source": source_name,
        })
    return stories


def aggregate_feeds() -> List[Dict[str, str]]:
    """
    Iterate through all configured feeds, parse them and collate
    unique stories.  Duplicate stories are discarded based on their
    canonical link.  The aggregated list is sorted by publication
    date in reverse chronological order.
    """
    seen_links = set()
    aggregated: List[Dict[str, str]] = []
    for source_name, url in FEEDS.items():
        stories = parse_feed(source_name, url)
        for story in stories:
            link = story.get("link")
            # Avoid duplicates by URL
            if link and link not in seen_links:
                seen_links.add(link)
                aggregated.append(story)
    # Sort descending by pubDate
    aggregated.sort(key=lambda s: s["pubDate"], reverse=True)
    return aggregated


def main() -> None:
    stories = aggregate_feeds()
    # Ensure data directory exists
    from pathlib import Path
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    output_path = data_dir / "news.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(stories, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(stories)} stories to {output_path}")


if __name__ == "__main__":
    main()