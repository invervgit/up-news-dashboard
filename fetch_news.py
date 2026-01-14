#!/usr/bin/env python3
"""
PoliticalIntel Backend v3.7 - High Success Rate
Features:
- Real Browser User-Agent (Fixes 403 Forbidden).
- Dual Parser Strategy (XML + HTML Fallback).
- Detailed Error Logging.
"""

import json
import hashlib
import os
import time
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---

INTERNATIONAL_FEEDS = [
    {"url": "https://www.thehindu.com/news/international/feeder/default.rss", "source": "The Hindu"},
    {"url": "http://feeds.bbci.co.uk/news/world/rss.xml", "source": "BBC World"},
    {"url": "https://www.aljazeera.com/xml/rss/all.xml", "source": "Al Jazeera"},
    {"url": "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms", "source": "TOI World"},
]

NATIONAL_FEEDS = [
    {"url": "https://www.thehindu.com/news/national/feeder/default.rss", "source": "The Hindu", "lang": "en"},
    {"url": "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms", "source": "TOI India", "lang": "en"},
    {"url": "https://www.livehindustan.com/rss/national/rssfeed.xml", "source": "Live Hindustan", "lang": "hi"},
    {"url": "https://www.amarujala.com/rss/india-news.xml", "source": "Amar Ujala", "lang": "hi"},
    {"url": "https://www.jagran.com/rss/news-national-rss.xml", "source": "Dainik Jagran", "lang": "hi"},
]

UP_FEEDS = [
    {"url": "https://www.amarujala.com/rss/uttar-pradesh.xml", "district": "Uttar Pradesh", "source": "Amar Ujala"},
    {"url": "https://api.livehindustan.com/feeds/rss/uttar-pradesh/rssfeed.xml", "district": "Uttar Pradesh", "source": "Live Hindustan"},
    {"url": "https://www.bhaskarenglish.in/rss-v1--category-16346.xml", "district": "Uttar Pradesh", "source": "Bhaskar English"},
    {"url": "https://cms.patrika.com/googlefeed/blog/location/lucknow-news", "district": "Lucknow", "source": "Patrika"},
    {"url": "https://www.amarujala.com/rss/lucknow.xml", "district": "Lucknow", "source": "Amar Ujala"},
    {"url": "https://www.amarujala.com/rss/noida.xml", "district": "Noida", "source": "Amar Ujala"},
    {"url": "https://www.amarujala.com/rss/gorakhpur.xml", "district": "Gorakhpur", "source": "Amar Ujala"},
    {"url": "https://www.amarujala.com/rss/varanasi.xml", "district": "Varanasi", "source": "Amar Ujala"},
    {"url": "https://www.amarujala.com/rss/ayodhya.xml", "district": "Ayodhya", "source": "Amar Ujala"},
]

# --- LOGIC ---

def is_junk_title(title: str) -> bool:
    junk_triggers = ["watch:", "video:", "daily quiz", "quiz:", "horoscope", "web story", "reels", "viral", "check list"]
    t_lower = title.lower()
    for trigger in junk_triggers:
        if trigger in t_lower: return True
    return False

def get_report_category(title: str, summary: str) -> str:
    blob = (title + " " + summary).lower()
    if any(k in blob for k in ["supreme court", "high court", "verdict", "hearing", "bail", "court", "sc", "hc", "अदालत", "फैसला"]): return "National_Judicial"
    if any(k in blob for k in ["cabinet", "modi", "pm", "minister", "bill", "scheme", "yojana", "govt", "government", "policy", "project", "budget", "drdo", "isro", "प्रधानमंत्री", "सरकार", "योजना"]): return "National_Govt"
    if any(k in blob for k in ["congress", "rahul", "protest", "allegation", "slam", "sp", "akhilesh", "demand", "opposition", "dharna", "विपक्ष", "आरोप"]): return "National_Opposition"
    return "National_General"

def aggressive_clean(text: str) -> str:
    if not text: return ""
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    patterns = [r"Link Copied", r"Also Read", r"Read More", r"Click Here", r"Follow us.*", r"Subscribe.*", r"Watch Video", r"Details inside", r"Updated:.*", r"Advertisement"]
    for p in patterns: text = re.sub(p, "", text, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', text).strip()

def parse_date(date_str: str) -> str:
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.strftime('%Y-%m-%d')
    except:
        return datetime.now().strftime('%Y-%m-%d')

def fetch_rss(feed_config, section):
    stories = []
    # Real Browser User-Agent to avoid 403 Forbidden
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    }
    
    try:
        # 1. Fetch
        resp = requests.get(feed_config['url'], headers=headers, timeout=15)
        
        # 2. Check Status
        if resp.status_code != 200:
            print(f"❌ Failed {resp.status_code}: {feed_config['url']}")
            return []
            
        # 3. Parse (Try XML first, then HTML fallback)
        try:
            soup = BeautifulSoup(resp.content, "xml")
            items = soup.find_all("item")
        except:
            soup = BeautifulSoup(resp.content, "html.parser")
            items = soup.find_all("item")

        if not items:
            print(f"⚠️ No items found in: {feed_config['url']}")
            return []

        print(f"✅ Success: {len(items)} items from {feed_config['source']}")
        
        for item in items:
            title_tag = item.find("title")
            link_tag = item.find("link")
            
            if not title_tag or not link_tag: continue
            
            title = aggressive_clean(title_tag.get_text())
            if is_junk_title(title): continue 

            link = link_tag.get_text()
            
            desc_tag = item.find("description")
            desc = desc_tag.get_text() if desc_tag else ""
            summary = aggressive_clean(desc)
            
            pub_date_tag = item.find("pubDate")
            pub_date_raw = pub_date_tag.get_text() if pub_date_tag else ""
            
            category = "General"
            if section == "National": category = get_report_category(title, summary)
            elif section == "International": category = "International"
            elif section == "UP_Focus": category = "UP_Focus"

            stories.append({
                "id": hashlib.md5(link.encode()).hexdigest(),
                "title": title,
                "link": link,
                "summary": summary, # Full summary kept
                "date": parse_date(pub_date_raw),
                "timestamp": pub_date_raw,
                "section": section,
                "report_category": category,
                "source": feed_config.get('source', 'Unknown'),
                "district": feed_config.get('district', ''),
                "lang": feed_config.get('lang', 'en')
            })
    except Exception as e:
        print(f"🔥 Error processing {feed_config['url']}: {e}")
    
    # Polite delay
    time.sleep(1) 
    return stories

def main():
    data_file = "data/news.json"
    existing_data = []
    
    import pathlib
    pathlib.Path("data").mkdir(exist_ok=True)
    
    if os.path.exists(data_file):
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except: existing_data = []
            
    new_data = []
    print("\n--- Starting Fetch ---")
    for feed in INTERNATIONAL_FEEDS: new_data.extend(fetch_rss(feed, "International"))
    for feed in NATIONAL_FEEDS: new_data.extend(fetch_rss(feed, "National"))
    for feed in UP_FEEDS: new_data.extend(fetch_rss(feed, "UP_Focus"))
    print("--- Fetch Complete ---\n")
        
    combined_map = {}
    
    # 1. Load Existing Data (Handle corrupted/old data safely)
    for item in existing_data:
        if isinstance(item, dict) and 'id' in item:
            combined_map[item['id']] = item
            
    # 2. Add New Data
    for item in new_data:
        combined_map[item['id']] = item 
        
    final_list = list(combined_map.values())
    
    # 3. Clean up old data (> 7 days)
    cutoff_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    final_list = [x for x in final_list if x.get('date', '') >= cutoff_date]
    
    # 4. Sort
    final_list.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # 5. Save
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)
        
    print(f"🎉 Database Updated. Total Stories: {len(final_list)}")

if __name__ == "__main__":
    main()
