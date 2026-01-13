#!/usr/bin/env python3
"""
PoliticalIntel Backend - v2.0
Features:
- National (English First, then Hindi)
- International (English Only)
- UP Focus (Strict Filtering, Top 50)
- Robust Deduplication & cleanup
"""

import json
import re
import hashlib
from datetime import datetime
from urllib.parse import urlparse
from email.utils import parsedate_to_datetime
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---

# 1. INTERNATIONAL FEEDS (English Only)
INTERNATIONAL_FEEDS = [
    {"url": "https://www.thehindu.com/news/international/feeder/default.rss", "source": "The Hindu"},
    {"url": "http://feeds.bbci.co.uk/news/world/rss.xml", "source": "BBC World"},
    {"url": "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms", "source": "TOI World"},
    {"url": "https://www.indiatoday.in/rss/1206577", "source": "India Today"},
]

# 2. NATIONAL FEEDS (Mixed - Will be sorted English First)
NATIONAL_FEEDS = [
    {"url": "https://www.thehindu.com/news/national/feeder/default.rss", "source": "The Hindu", "lang": "en"},
    {"url": "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms", "source": "TOI India", "lang": "en"},
    {"url": "https://timesofindia.indiatimes.com/rssfeedmostrecent.cms", "source": "TOI Latest", "lang": "en"},
    {"url": "https://www.livehindustan.com/rss/national/rssfeed.xml", "source": "Live Hindustan", "lang": "hi"},
    {"url": "https://www.amarujala.com/rss/india-news.xml", "source": "Amar Ujala", "lang": "hi"},
    {"url": "https://www.jagran.com/rss/news-national-rss.xml", "source": "Dainik Jagran", "lang": "hi"},
]

# 3. UP STATE & DISTRICT FEEDS (Strict Filter)
UP_FEEDS = [
    # State Level
    {"url": "https://www.bhaskarenglish.in/rss-v1--category-16346.xml", "district": "Uttar Pradesh", "source": "Bhaskar English"},
    {"url": "https://www.amarujala.com/rss/uttar-pradesh.xml", "district": "Uttar Pradesh", "source": "Amar Ujala"},
    {"url": "https://api.livehindustan.com/feeds/rss/uttar-pradesh/rssfeed.xml", "district": "Uttar Pradesh", "source": "Live Hindustan"},
    
    # Key Districts (Add more as needed from your list)
    {"url": "https://cms.patrika.com/googlefeed/blog/location/lucknow-news", "district": "Lucknow", "source": "Patrika"},
    {"url": "https://www.amarujala.com/rss/lucknow.xml", "district": "Lucknow", "source": "Amar Ujala"},
    {"url": "https://www.amarujala.com/rss/kanpur.xml", "district": "Kanpur", "source": "Amar Ujala"},
    {"url": "https://www.amarujala.com/rss/varanasi.xml", "district": "Varanasi", "source": "Amar Ujala"},
    {"url": "https://www.amarujala.com/rss/gorakhpur.xml", "district": "Gorakhpur", "source": "Amar Ujala"},
    {"url": "https://cms.patrika.com/googlefeed/blog/location/noida-news", "district": "Noida", "source": "Patrika"},
    {"url": "https://www.amarujala.com/rss/noida.xml", "district": "Noida", "source": "Amar Ujala"},
    {"url": "https://www.amarujala.com/rss/ayodhya.xml", "district": "Ayodhya", "source": "Amar Ujala"},
]

# --- FILTERING LOGIC ---

POSITIVE_KEYWORDS = [
    "dm", "ssp", "commissioner", "high court", "supreme court", "verdict", "bail", 
    "yojana", "scheme", "project", "inauguration", "protest", "dharna", "mla", "mp", 
    "minister", "election", "vote", "development", "budget", "policy", "governance",
    "cm office", "pm office", "municipality", "nagarnigam", "politics", "congress", "bjp", "sp",
    "मुख्यमंत्री", "प्रधानमंत्री", "सांसद", "विधायक", "मंत्री", "योजना", "परियोजना",
    "अदालत", "कोर्ट", "जज", "फैसला", "जमानत", "धरना", "प्रदर्शन", "ज्ञापन", 
    "अधिकारी", "डीएम", "एसएसपी", "विकास", "बजट", "घोटाला", "जांच"
]

NEGATIVE_KEYWORDS = [
    "shameful", "obscene", "nude", "video", "viral", "reels", "affair", "lover",
    "suicide", "murder", "killed", "died", "collision", "theft", "robbery", 
    "rape", "molestation", "dowry", "hanging", "poison", "dead body", "corpse",
    "husband", "wife", "boyfriend", "girlfriend", "marriage", "wedding",
    "शर्मसार", "अश्लील", "वीडियो", "वायरल", "प्रेमी", "प्रेमिका", "आत्महत्या", 
    "फंदे", "लटका", "शव", "लाश", "हत्या", "मर्डर", "रेप", "दुष्कर्म", "चोरी", "लूट", 
    "हादसा", "टक्कर", "मौत", "शादी", "विवाह", "दहेज"
]

def aggressive_clean(text: str) -> str:
    if not text: return ""
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    patterns = [
        r"Link Copied", r"Also Read", r"Read More", r"Click Here",
        r"Download.*App", r"Follow us on", r"Subscribe to",
        r"मेरा शहर", r"My City", r"WhatsApp Channel", r"Next Article", 
        r"Please wait", r"Share this", r"Live Updates", r"Watch Video", 
        r"विज्ञापन", r"Get all India News.*", r"Log in.*"
    ]
    for p in patterns:
        text = re.sub(p, "", text, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', text).strip()

def is_relevant(title: str, summary: str) -> bool:
    blob = (title + " " + summary).lower()
    has_pos = any(k in blob for k in POSITIVE_KEYWORDS)
    has_neg = any(k in blob for k in NEGATIVE_KEYWORDS)
    if has_neg and not has_pos: return False
    return True

def get_category(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["court", "bail", "verdict", "hc", "sc", "अदालत", "कोर्ट"]): return "Judicial"
    if any(k in t for k in ["yojana", "project", "highway", "water", "supply", "योजना", "विकास"]): return "Governance"
    if any(k in t for k in ["protest", "strike", "sp", "congress", "bsp", "akhilesh", "rahul", "धरना", "सपा", "विपक्ष"]): return "Opposition"
    if any(k in t for k in ["bjp", "nda", "yogi", "modi", "minister", "dm", "admin", "योगी", "मोदी", "प्रशासन"]): return "Government"
    return "General"

def parse_date(date_str: str) -> str:
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.isoformat()
    except:
        return datetime.now().isoformat()

def fetch_rss(feed_config, scope):
    stories = []
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(feed_config['url'], headers=headers, timeout=10)
        if resp.status_code != 200: return []
        soup = BeautifulSoup(resp.content, "xml")
        items = soup.find_all("item")
        
        for item in items:
            title = aggressive_clean(item.find("title").get_text())
            link = item.find("link").get_text()
            desc = item.find("description").get_text() if item.find("description") else ""
            summary = aggressive_clean(desc)
            pub_date = item.find("pubDate").get_text() if item.find("pubDate") else ""
            
            # Filters
            if scope == "state" and not is_relevant(title, summary): continue
            
            # Simple International Check (exclude India specific news from International tab if mixed)
            if scope == "international" and "india" in title.lower() and "cricket" in title.lower():
                continue

            stories.append({
                "title": title,
                "link": link,
                "summary": summary[:220] + "..." if len(summary) > 220 else summary,
                "pubDate": parse_date(pub_date),
                "scope": scope,
                "district": feed_config.get('district', 'General'),
                "source": feed_config.get('source', 'Unknown'),
                "category": get_category(title + " " + summary),
                "lang": feed_config.get('lang', 'en') # Default to en
            })
    except Exception as e:
        print(f"Skipping {feed_config['url']}: {e}")
    return stories

def main():
    final_data = []
    seen_titles = set()

    def add_stories(stories):
        for s in stories:
            # Fuzzy Deduplication
            simple_title = re.sub(r'[^\w\s]', '', s['title'].lower())
            if simple_title not in seen_titles:
                seen_titles.add(simple_title)
                final_data.append(s)

    # 1. International (English)
    print("Fetching International...")
    intl_stories = []
    for feed in INTERNATIONAL_FEEDS:
        intl_stories.extend(fetch_rss(feed, "international"))
    intl_stories.sort(key=lambda x: x['pubDate'], reverse=True)
    add_stories(intl_stories)

    # 2. National (English First, Then Hindi)
    print("Fetching National...")
    nat_en = []
    nat_hi = []
    for feed in NATIONAL_FEEDS:
        stories = fetch_rss(feed, "national")
        if feed.get('lang') == 'en':
            nat_en.extend(stories)
        else:
            nat_hi.extend(stories)
            
    # Sort independently by date
    nat_en.sort(key=lambda x: x['pubDate'], reverse=True)
    nat_hi.sort(key=lambda x: x['pubDate'], reverse=True)
    
    # Merge: English first
    add_stories(nat_en)
    add_stories(nat_hi)

    # 3. UP Focus
    print("Fetching UP State...")
    up_stories = []
    for feed in UP_FEEDS:
        up_stories.extend(fetch_rss(feed, "state"))
    up_stories.sort(key=lambda x: x['pubDate'], reverse=True)
    add_stories(up_stories)

    # Save
    with open("data/news.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    print(f"Done. {len(final_data)} stories saved.")

if __name__ == "__main__":
    main()
