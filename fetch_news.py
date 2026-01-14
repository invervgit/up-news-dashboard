#!/usr/bin/env python3
"""
PoliticalIntel Backend v4.0 - Anti-Bot Edition
Features:
- Rotates User-Agents to bypass 403/429 blocks.
- Extensive Error Logging (Check Actions Logs!).
- Generates a 'System Alert' if fetching fails completely.
"""

import json
import hashlib
import os
import time
import random
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# --- CONFIGURATION ---

INTERNATIONAL_FEEDS = [
    {"url": "https://www.thehindu.com/news/international/feeder/default.rss", "source": "The Hindu"},
    {"url": "http://feeds.bbci.co.uk/news/world/rss.xml", "source": "BBC World"},
    {"url": "https://www.aljazeera.com/xml/rss/all.xml", "source": "Al Jazeera"},
    # Fallback safe feed
    {"url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "source": "NYT World"}, 
]

NATIONAL_FEEDS = [
    {"url": "https://www.thehindu.com/news/national/feeder/default.rss", "source": "The Hindu", "lang": "en"},
    {"url": "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms", "source": "TOI India", "lang": "en"},
    {"url": "https://www.livehindustan.com/rss/national/rssfeed.xml", "source": "Live Hindustan", "lang": "hi"},
    {"url": "https://www.amarujala.com/rss/india-news.xml", "source": "Amar Ujala", "lang": "hi"},
    {"url": "https://www.jagran.com/rss/news-national-rss.xml", "source": "Dainik Jagran", "lang": "hi"},
    # Fallback safe feed
    {"url": "https://feeds.feedburner.com/ndtvnews-india-news", "source": "NDTV India", "lang": "en"},
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

ua = UserAgent()

def get_headers():
    """Generates random headers to mimic a real browser."""
    return {
        "User-Agent": ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

def is_junk_title(title: str) -> bool:
    junk_triggers = ["watch:", "video:", "daily quiz", "quiz:", "horoscope", "web story", "reels", "viral", "check list"]
    return any(trigger in title.lower() for trigger in junk_triggers)

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
    url = feed_config['url']
    
    # Retry logic (3 attempts)
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=get_headers(), timeout=20)
            
            if resp.status_code == 200:
                # Success! Break retry loop
                break
            elif resp.status_code == 403:
                print(f"🚫 Blocked (403) on attempt {attempt+1}: {url}")
                time.sleep(2) # Wait before retry
            else:
                print(f"⚠️ Error {resp.status_code} on attempt {attempt+1}: {url}")
                
        except Exception as e:
            print(f"🔥 Exception on {url}: {e}")
            time.sleep(2)
    else:
        # Loop finished without success
        print(f"❌ FAILED to fetch: {url}")
        return []

    # Parse Content
    try:
        # Explicitly use LXML for robustness
        soup = BeautifulSoup(resp.content, "xml")
        items = soup.find_all("item")
        
        # Fallback to HTML parser if XML fails
        if not items:
            soup = BeautifulSoup(resp.content, "html.parser")
            items = soup.find_all("item")

        if not items:
            print(f"⚠️ Empty Feed (Parsed but no items): {url}")
            return []

        print(f"✅ Extracted {len(items)} items from: {url}")

        for item in items:
            title_tag = item.find("title")
            link_tag = item.find("link")
            
            if not title_tag or not link_tag: continue
            
            title = aggressive_clean(title_tag.get_text())
            if is_junk_title(title): continue 

            link = link_tag.get_text()
            desc = item.find("description").get_text() if item.find("description") else ""
            summary = aggressive_clean(desc)
            pub_date = item.find("pubDate").get_text() if item.find("pubDate") else ""
            
            category = "General"
            if section == "National": category = get_report_category(title, summary)
            elif section == "International": category = "International"
            elif section == "UP_Focus": category = "UP_Focus"

            stories.append({
                "id": hashlib.md5(link.encode()).hexdigest(),
                "title": title,
                "link": link,
                "summary": summary,
                "date": parse_date(pub_date),
                "timestamp": pub_date,
                "section": section,
                "report_category": category,
                "source": feed_config.get('source', 'Unknown'),
                "district": feed_config.get('district', ''),
                "lang": feed_config.get('lang', 'en')
            })
            
    except Exception as e:
        print(f"☠️ Parsing Error {url}: {e}")
        
    return stories

def create_system_alert(message):
    """Creates a fake news item to alert the user on the dashboard."""
    return {
        "id": "system_alert",
        "title": "⚠️ System Alert: Data Fetching Issue",
        "link": "#",
        "summary": message,
        "date": datetime.now().strftime('%Y-%m-%d'),
        "timestamp": datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000'),
        "section": "National",
        "report_category": "National_General",
        "source": "System",
        "district": "",
        "lang": "en"
    }

def main():
    data_file = "data/news.json"
    existing_data = []
    
    import pathlib
    pathlib.Path("data").mkdir(exist_ok=True)
    
    # Load existing data carefully
    if os.path.exists(data_file):
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                content = f.read()
                if content:
                    existing_data = json.loads(content)
        except Exception as e:
            print(f"Old data corrupted, starting fresh: {e}")
            existing_data = []
            
    new_data = []
    print("\n--- 🚀 STARTING FETCH ---")
    for feed in INTERNATIONAL_FEEDS: new_data.extend(fetch_rss(feed, "International"))
    for feed in NATIONAL_FEEDS: new_data.extend(fetch_rss(feed, "National"))
    for feed in UP_FEEDS: new_data.extend(fetch_rss(feed, "UP_Focus"))
    print("--- 🏁 FETCH COMPLETE ---\n")
        
    # If fetch failed completely, protect the file or add alert
    if not new_data:
        print("🚨 CRITICAL: No new data fetched! Adding System Alert.")
        # If we have old data, keep it. If totally empty, add alert.
        if not existing_data:
            new_data.append(create_system_alert("Unable to fetch news from external sources. Please check GitHub Actions logs for 403 errors."))
        else:
            print("Keeping old data intact.")
    
    # Merge Logic
    combined_map = {}
    for item in existing_data:
        if isinstance(item, dict) and 'id' in item: combined_map[item['id']] = item
    for item in new_data:
        combined_map[item['id']] = item 
        
    final_list = list(combined_map.values())
    
    # Prune old
    cutoff_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    final_list = [x for x in final_list if x.get('date', '') >= cutoff_date]
    
    # Sort
    final_list.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Write
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)
        
    print(f"💾 Saved {len(final_list)} stories to news.json")

if __name__ == "__main__":
    main()
