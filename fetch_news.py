#!/usr/bin/env python3
"""
Production Grade News Aggregator for UP Dashboard.
Features:
- Strict Political/Governance Filtering (Anti-Crime/Anti-Junk).
- Fuzzy Deduplication (Removes similar headlines).
- Robust Date Parsing.
- Distinct National vs State streams.
"""

import json
import re
import hashlib
from datetime import datetime
from difflib import SequenceMatcher
from urllib.parse import urlparse
from email.utils import parsedate_to_datetime
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---

# 1. NATIONAL FEEDS
NATIONAL_FEEDS = [
    {"url": "https://www.amarujala.com/rss/india-news.xml", "source": "Amar Ujala"},
    {"url": "https://www.livehindustan.com/rss/national/rssfeed.xml", "source": "Live Hindustan"},
    {"url": "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms", "source": "TOI"},
    {"url": "https://www.jagran.com/rss/news-national-rss.xml", "source": "Dainik Jagran"},
]

# 2. UP DISTRICT & STATE FEEDS
# Mapped explicitly to ensure correct tagging
UP_FEEDS = [
    # State Level
    {"url": "https://www.amarujala.com/rss/uttar-pradesh.xml", "district": "Uttar Pradesh", "source": "Amar Ujala"},
    {"url": "https://api.livehindustan.com/feeds/rss/uttar-pradesh/rssfeed.xml", "district": "Uttar Pradesh", "source": "Live Hindustan"},
    {"url": "https://www.bhaskar.com/rss-v1--category-2052.xml", "district": "Uttar Pradesh", "source": "Dainik Bhaskar"},
    
    # Major Districts (NCR & Capitals)
    {"url": "https://cms.patrika.com/googlefeed/blog/location/noida-news", "district": "Noida", "source": "Patrika"},
    {"url": "https://cms.patrika.com/googlefeed/blog/location/greater-noida-news", "district": "Noida", "source": "Patrika"},
    {"url": "https://www.amarujala.com/rss/noida.xml", "district": "Noida", "source": "Amar Ujala"},
    {"url": "https://www.amarujala.com/rss/ghaziabad.xml", "district": "Ghaziabad", "source": "Amar Ujala"},
    {"url": "https://www.amarujala.com/rss/lucknow.xml", "district": "Lucknow", "source": "Amar Ujala"},
    {"url": "https://api.livehindustan.com/feeds/rss/uttar-pradesh/lucknow/rssfeed.xml", "district": "Lucknow", "source": "Live Hindustan"},
    
    # Eastern UP
    {"url": "https://www.amarujala.com/rss/varanasi.xml", "district": "Varanasi", "source": "Amar Ujala"},
    {"url": "https://www.amarujala.com/rss/gorakhpur.xml", "district": "Gorakhpur", "source": "Amar Ujala"},
    {"url": "https://www.amarujala.com/rss/prayagraj.xml", "district": "Prayagraj", "source": "Amar Ujala"},
    {"url": "https://cms.patrika.com/googlefeed/blog/location/ayodhya-news", "district": "Ayodhya", "source": "Patrika"},
    
    # Central/Western UP
    {"url": "https://www.amarujala.com/rss/kanpur.xml", "district": "Kanpur", "source": "Amar Ujala"},
    {"url": "https://www.amarujala.com/rss/meerut.xml", "district": "Meerut", "source": "Amar Ujala"},
    {"url": "https://www.amarujala.com/rss/agra.xml", "district": "Agra", "source": "Amar Ujala"},
    {"url": "https://www.amarujala.com/rss/bareilly.xml", "district": "Bareilly", "source": "Amar Ujala"},
    {"url": "https://www.amarujala.com/rss/aligarh.xml", "district": "Aligarh", "source": "Amar Ujala"},
    
    # Political Hotspots
    {"url": "https://www.amarujala.com/rss/amethi.xml", "district": "Amethi", "source": "Amar Ujala"},
    {"url": "https://www.amarujala.com/rss/raebareli.xml", "district": "Raebareli", "source": "Amar Ujala"},
    {"url": "https://www.amarujala.com/rss/mainpuri.xml", "district": "Mainpuri", "source": "Amar Ujala"},
]

# --- FILTERING LOGIC ---

POSITIVE_KEYWORDS = [
    "dm", "ssp", "commissioner", "high court", "supreme court", "verdict", "bail", 
    "yojana", "scheme", "project", "inauguration", "foundation stone", "inspect",
    "protest", "dharna", "memorandum", "vidhan sabha", "loksabha", "mla", "mp", 
    "minister", "election", "vote", "development", "budget", "policy", "governance",
    "cm office", "pm office", "municipality", "nagarnigam", "tender",
    "मुख्यमंत्री", "प्रधानमंत्री", "सांसद", "विधायक", "मंत्री", "योजना", "परियोजना",
    "अदालत", "कोर्ट", "जज", "फैसला", "जमानत", "धरना", "प्रदर्शन", "ज्ञापन", 
    "अधिकारी", "डीएम", "एसएसपी", "विकास", "बजट", "घोटाला", "जांच", "लोकार्पण"
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
    """Removes boilerplate text."""
    if not text: return ""
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    
    # Regex to remove junk
    patterns = [
        r"Link Copied", r"Also Read", r"Read More", r"Click Here",
        r"Download.*App", r"Follow us on", r"Subscribe to",
        r"मेरा शहर", r"My City", r"WhatsApp Channel", 
        r"Next Article", r"Please wait", r"Share this",
        r"Live Updates", r"Watch Video", r"विज्ञापन",
        r"Get all India News.*", r".*posted by.*"
    ]
    for p in patterns:
        text = re.sub(p, "", text, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', text).strip()

def is_relevant(title: str, summary: str) -> bool:
    """
    Returns TRUE if the story is Politically/Administratively relevant.
    Returns FALSE if it is generic crime/junk.
    """
    blob = (title + " " + summary).lower()
    
    has_pos = any(k in blob for k in POSITIVE_KEYWORDS)
    has_neg = any(k in blob for k in NEGATIVE_KEYWORDS)
    
    # 1. Pure Junk (Negative without Positive context) -> REJECT
    if has_neg and not has_pos:
        return False
        
    # 2. Political Crime (Negative + Positive) -> KEEP
    # Example: "MLA involved in murder case" (Murder + MLA)
    if has_neg and has_pos:
        return True
        
    # 3. Neutral/Positive -> KEEP
    return True

def get_category(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["court", "bail", "verdict", "hc", "sc", "अदालत", "कोर्ट"]): return "Judicial"
    if any(k in t for k in ["yojana", "project", "highway", "water", "supply", "योजना", "विकास"]): return "Governance"
    if any(k in t for k in ["protest", "strike", "sp", "congress", "bsp", "akhilesh", "rahul", "धरना", "सपा", "विपक्ष"]): return "Opposition"
    if any(k in t for k in ["bjp", "nda", "yogi", "modi", "minister", "dm", "admin", "योगी", "मोदी", "प्रशासन"]): return "Government"
    return "General"

def parse_date(date_str: str) -> str:
    """Robust date parser for different RSS formats."""
    try:
        # Try RFC 822 (Standard RSS)
        dt = parsedate_to_datetime(date_str)
        return dt.isoformat()
    except:
        # Fallback to current time if parsing fails
        return datetime.now().isoformat()

def is_duplicate(title, seen_titles):
    """Fuzzy matching to detect duplicate stories with slightly different titles."""
    norm_title = re.sub(r'[^\w\s]', '', title.lower())
    
    for seen in seen_titles:
        # If similarity > 85%, consider it a duplicate
        if SequenceMatcher(None, norm_title, seen).ratio() > 0.85:
            return True
    return False

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
            
            # --- FILTERING ---
            if scope == "state" and not is_relevant(title, summary):
                continue
            # -----------------
            
            stories.append({
                "title": title,
                "link": link,
                "summary": summary[:200] + "..." if len(summary) > 200 else summary,
                "pubDate": parse_date(pub_date),
                "scope": scope,
                "district": feed_config.get('district', 'India'),
                "source": feed_config.get('source', 'Unknown'),
                "category": get_category(title + " " + summary)
            })
            
    except Exception as e:
        print(f"Skipping {feed_config['url']}: {e}")
        
    return stories

def main():
    final_data = []
    seen_titles = set()
    
    # 1. Fetch National
    print("Fetching National News...")
    for feed in NATIONAL_FEEDS:
        news = fetch_rss(feed, "national")
        for n in news:
            if not is_duplicate(n['title'], seen_titles):
                seen_titles.add(re.sub(r'[^\w\s]', '', n['title'].lower()))
                final_data.append(n)

    # 2. Fetch UP
    print("Fetching UP News...")
    for feed in UP_FEEDS:
        news = fetch_rss(feed, "state")
        for n in news:
            if not is_duplicate(n['title'], seen_titles):
                seen_titles.add(re.sub(r'[^\w\s]', '', n['title'].lower()))
                final_data.append(n)

    # 3. Sort by Date
    final_data.sort(key=lambda x: x['pubDate'], reverse=True)
    
    # 4. Save
    with open("data/news.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f"Update Complete. Total Stories: {len(final_data)}")

if __name__ == "__main__":
    main()
