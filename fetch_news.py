#!/usr/bin/env python3
"""
PoliticalIntel Backend v3.0 - Executive Briefing Edition
Features:
- 7-Day History Retention (Append Mode).
- Advanced NLP-based Categorization (Govt vs Opposition vs Judicial).
- Report-Ready Data Structure.
"""

import json
import re
import hashlib
import os
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---

# 1. INTERNATIONAL (English Only)
INTERNATIONAL_FEEDS = [
    {"url": "https://www.thehindu.com/news/international/feeder/default.rss", "source": "The Hindu"},
    {"url": "http://feeds.bbci.co.uk/news/world/rss.xml", "source": "BBC World"},
    {"url": "https://www.aljazeera.com/xml/rss/all.xml", "source": "Al Jazeera"},
    {"url": "https://www.loksatta.com/feed/rss/international", "source": "Loksatta"}, # Added variety
]

# 2. NATIONAL (Govt, Opposition, Judicial mix)
NATIONAL_FEEDS = [
    {"url": "https://www.thehindu.com/news/national/feeder/default.rss", "source": "The Hindu"},
    {"url": "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms", "source": "TOI India"},
    {"url": "https://www.livehindustan.com/rss/national/rssfeed.xml", "source": "Live Hindustan"},
    {"url": "https://www.amarujala.com/rss/india-news.xml", "source": "Amar Ujala"},
    {"url": "https://www.jagran.com/rss/news-national-rss.xml", "source": "Dainik Jagran"},
    {"url": "https://www.news18.com/rss/politics.xml", "source": "News18 Politics"},
]

# 3. UP STATE (For UP Focus Tab)
UP_FEEDS = [
    {"url": "https://www.amarujala.com/rss/uttar-pradesh.xml", "district": "Uttar Pradesh", "source": "Amar Ujala"},
    {"url": "https://api.livehindustan.com/feeds/rss/uttar-pradesh/rssfeed.xml", "district": "Uttar Pradesh", "source": "Live Hindustan"},
    {"url": "https://cms.patrika.com/googlefeed/blog/location/lucknow-news", "district": "Lucknow", "source": "Patrika"},
    {"url": "https://www.amarujala.com/rss/lucknow.xml", "district": "Lucknow", "source": "Amar Ujala"},
    {"url": "https://www.amarujala.com/rss/noida.xml", "district": "Noida", "source": "Amar Ujala"},
    {"url": "https://www.amarujala.com/rss/gorakhpur.xml", "district": "Gorakhpur", "source": "Amar Ujala"},
    {"url": "https://www.amarujala.com/rss/varanasi.xml", "district": "Varanasi", "source": "Amar Ujala"},
    {"url": "https://www.amarujala.com/rss/ayodhya.xml", "district": "Ayodhya", "source": "Amar Ujala"},
]

# --- INTELLIGENT TAGGING ---

def get_report_category(title: str, summary: str) -> str:
    """
    Classifies National news into specific Report Sections.
    """
    blob = (title + " " + summary).lower()
    
    # 1. JUDICIAL (Highest Priority)
    judicial_kw = ["supreme court", "high court", "bench", "verdict", "hearing", "cji", "chandrachud", "bail", "petition", "court", "sc", "hc", "अदालत", "कोर्ट", "फैसला", "याचिका", "सुप्रीम कोर्ट"]
    if any(k in blob for k in judicial_kw):
        return "National_Judicial"
        
    # 2. GOVERNMENT / POLICY (Medium Priority)
    govt_kw = [
        "cabinet", "modi", "pm", "minister", "bill", "act", "parliament", "scheme", "yojana", "mandate", 
        "govt", "government", "center", "centre", "inaugurate", "launch", "policy", "project", "highway",
        "railway", "vande bharat", "budget", "finance", "defense", "isro", "drdo", "president",
        "प्रधानमंत्री", "मोदी", "योगी", "सरकार", "योजना", "परियोजना", "बिल", "संसद", "कैबिनेट"
    ]
    if any(k in blob for k in govt_kw):
        return "National_Govt"
        
    # 3. OPPOSITION (Specific Context)
    opp_kw = [
        "congress", "rahul", "gandhi", "kharge", "protest", "allegation", "slam", "attack", "sp", "samajwadi", 
        "akhilesh", "yatra", "demand", "resignation", "tmc", "mamata", "aadmi party", "kejriwal", "opposition", 
        "walkout", "dharna", "विपक्ष", "कांग्रेस", "राहुल", "सपा", "अखिलेश", "प्रदर्शन", "आरोप"
    ]
    if any(k in blob for k in opp_kw):
        return "National_Opposition"
    
    # Default fallback
    return "National_General"

def aggressive_clean(text: str) -> str:
    if not text: return ""
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    patterns = [
        r"Link Copied", r"Also Read", r"Read More", r"Click Here", r"Follow us.*", 
        r"Subscribe.*", r"Watch Video", r"Live Updates", r"Details inside", 
        r"Check here", r"Posted by.*", r"Updated:.*", r"My City", r"Advertisement"
    ]
    for p in patterns:
        text = re.sub(p, "", text, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', text).strip()

def parse_date(date_str: str) -> str:
    try:
        dt = parsedate_to_datetime(date_str)
        # Convert to local simplified ISO date (YYYY-MM-DD) for filtering
        return dt.strftime('%Y-%m-%d')
    except:
        return datetime.now().strftime('%Y-%m-%d')

def fetch_rss(feed_config, section):
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
            pub_date_raw = item.find("pubDate").get_text() if item.find("pubDate") else ""
            
            # Categorize
            category = "General"
            if section == "National":
                category = get_report_category(title, summary)
            elif section == "International":
                category = "International"
            elif section == "UP_Focus":
                category = "UP_Focus"

            stories.append({
                "id": hashlib.md5(link.encode()).hexdigest(), # Unique ID
                "title": title,
                "link": link,
                "summary": summary[:250] + "..." if len(summary) > 250 else summary,
                "date": parse_date(pub_date_raw), # YYYY-MM-DD
                "timestamp": pub_date_raw, # Full string for display
                "section": section,
                "report_category": category,
                "source": feed_config.get('source', 'Unknown'),
                "district": feed_config.get('district', '')
            })
    except Exception as e:
        print(f"Error {feed_config['url']}: {e}")
    return stories

def main():
    data_file = "data/news.json"
    existing_data = []
    
    # 1. Load History (if exists)
    if os.path.exists(data_file):
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except:
            existing_data = []
            
    # 2. Fetch New Data
    new_data = []
    
    print("Fetching International...")
    for feed in INTERNATIONAL_FEEDS:
        new_data.extend(fetch_rss(feed, "International"))
        
    print("Fetching National...")
    for feed in NATIONAL_FEEDS:
        new_data.extend(fetch_rss(feed, "National"))
        
    print("Fetching UP Focus...")
    for feed in UP_FEEDS:
        new_data.extend(fetch_rss(feed, "UP_Focus"))
        
    # 3. Merge & Deduplicate
    # Create a dict of existing data keyed by ID to prevent duplicates
    combined_map = {item['id']: item for item in existing_data}
    
    # Update/Add new items
    for item in new_data:
        combined_map[item['id']] = item # Overwrite or add
        
    final_list = list(combined_map.values())
    
    # 4. Prune Old Data (> 7 Days)
    cutoff_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    final_list = [x for x in final_list if x['date'] >= cutoff_date]
    
    # 5. Sort by Date (Newest First)
    # Note: Sort by full timestamp if available, else date
    final_list.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Save
    import pathlib
    pathlib.Path("data").mkdir(exist_ok=True)
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)
        
    print(f"Database Updated. Total Stories: {len(final_list)}")

if __name__ == "__main__":
    main()
