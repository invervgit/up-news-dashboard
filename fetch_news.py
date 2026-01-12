#!/usr/bin/env python3
"""
Enhanced news fetcher for the Uttar Pradesh News Dashboard.
Features:
- Robust cleanup of boilerplate text (Link Copied, Ads).
- Browser-like headers to avoid 403 errors.
- Automatic Github Actions integration ready.
"""

import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

######################################################################
# Configuration
######################################################################

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

FEED_DISTRICT_MAP: Dict[str, str] = {
  "https://www.bhaskar.com/rss-v1--category-2052.xml": "Uttar Pradesh",  
  # Examples:
    # "https://www.bhaskar.com/rss-v1--category-2052.xml": "Uttar Pradesh",
}

CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Opposition Activity": [
        "samajwadi", "sp", "congress", "inc", "aazad samaj", "bsp", "aimim",
        "ad(k)", "akhilesh", "mayawati", "azad", "owaisi", "rahul", "gandhi",
        "priyanka", "chalisa", "sp chief", "inc leader", "up congress", 
        "विपक्ष", "सपा", "बसपा", "अखिलेश", "मायावती", "कांग्रेस",],
    "NDA Activity": [
        "bjp", "nda", "sbsp", "ad(s)", "rld", "nishad", "modi", "yogi",
        "pm modi", "amit shah", "jp nadda", "apna dal", "nath", "rajnath",
        "भाजपा", "योगी", "मोदी", "आदित्यनाथ", "एनडीए",],
    "Governance issues": [
        "development", "infrastructure", "scheme", "mission", "project",
        "programme", "road", "bridge", "hospital", "demand", "protest", 
        "complaint", "health", "education", "school", "college", "budget", 
        "fund", "electricity", "water", "admin", "dm", "police",
        "मुख्यमंत्री", "सरकार", "विकास", "योजना", "परियोजना", "सड़क", 
        "अस्पताल", "शिक्षा", "बिजली", "पानी", "प्रशासन",],
    "Judicial cases": [
        "court", "high court", "supreme court", "verdict", "judgment", "judge",
        "petition", "litigation", "bail", "arrest", "cbi", "ed", "fir",
        "अदालत", "न्यायालय", "कोर्ट", "जज", "याचिका", "फैसला", "मुकदमा",], ],}


######################################################################
# Utility functions
######################################################################
def clean_boilerplate(text: str) -> str:
    """
    Removes common boilerplate phrases found in Hindi news sites.
    """
    junk_phrases = [
        "Link Copied", "Link copied", "Follow Us", "Follow us", 
        "Read More", "Read more", "विज्ञापन", "विस्तार", 
        "Click here", "Subscribe", "Allow Notifications", 
        "मेरा शहर", "My City", "What's App", "WhatsApp Channel",
        "Reactions", "सांकेतिक तस्वीर", "फाइल फोटो"
    ]
    
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip lines that are just junk phrases
        is_junk = False
        for junk in junk_phrases:
            if junk.lower() in line.lower() and len(line) < 50:
                is_junk = True
                break
        
        if not is_junk:
            cleaned_lines.append(line)
            
    return " ".join(cleaned_lines)
def fetch_article_content(url: str) -> Optional[str]:
    """
    Fetches article content with proper headers to mimic a browser.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "html.parser")
        
        # Remove unwanted elements before extracting text
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
            
        # Try to find the main article body based on common classes
        article_body = soup.find('div', class_=re.compile(r'(article|story|content|body)', re.I))
        
        if not article_body:
            article_body = soup  # Fallback to full body if specific container not found
            
        paragraphs = article_body.find_all('p')
        text_content = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            # Filter out very short lines which are usually metadata/links
            if len(text) > 40: 
                text_content.append(text)
                
        full_text = "\n".join(text_content)
        return clean_boilerplate(full_text)
        
    except Exception as e:
        print(f"Error fetching {url}: {e}") # Uncomment for debugging
        return None

def summarise(description: str, link: str, max_words: int = 80) -> str:
    """
    Smart summarizer that prefers fetched content over RSS description
    if the RSS description is too short.
    """
    clean_desc = BeautifulSoup(description, "html.parser").get_text(separator=" ", strip=True)
    clean_desc = clean_boilerplate(clean_desc)
    
    final_text = clean_desc
    
    # If RSS description is short (< 200 chars), try to fetch the real article
    if len(clean_desc) < 200 and link:
        fetched_text = fetch_article_content(link)
        if fetched_text and len(fetched_text) > len(clean_desc):
            final_text = fetched_text

    # Truncate logic
    words = final_text.split()
    if len(words) > max_words:
        return " ".join(words[:max_words]) + "..."
    return final_text

def parse_pubdate(pubdate: str) -> str:
    for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M %z", "%d %b %Y %H:%M:%S %z"]:
        try:
            dt = datetime.strptime(pubdate, fmt)
            return dt.astimezone(timezone.utc).isoformat()
        except Exception:
            continue
    return datetime.now(timezone.utc).isoformat()

def classify(text: str) -> str:
    lower_text = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in lower_text for kw in keywords):
            return category
    return "Uncategorised"

def infer_district_from_feed(url: str) -> str:
    if url in FEED_DISTRICT_MAP:
        return FEED_DISTRICT_MAP[url]
    try:
        path = urlparse(url).path
        segments = [seg for seg in path.split('/') if seg]
        
        # Logic for Amar Ujala / Live Hindustan
        for seg in segments:
            if seg.endswith('.xml'):
                seg = seg.replace('.xml', '')
            if seg in ["rss", "feed", "rssfeed", "uttar-pradesh", "news"]:
                continue
            # Return the first meaningful segment as district
            return seg.replace('-', ' ').title()
    except:
        pass
    return "Uttar Pradesh"

def extract_source(url: str) -> str:
    try:
        domain = urlparse(url).netloc
        return domain.replace("www.", "").split(".")[0].title()
    except:
        return "Unknown"

def main():
    all_stories = []
    seen_links = set()
    
    print(f"Fetching {len(FEEDS)} feeds...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for feed_url in FEEDS:
        try:
            resp = requests.get(feed_url, headers=headers, timeout=15)
            if resp.status_code != 200:
                continue
            
            soup = BeautifulSoup(resp.content, "xml")
            items = soup.find_all("item")
            
            district = infer_district_from_feed(feed_url)
            source = extract_source(feed_url)
            
            for item in items:
                link = item.find("link").get_text(strip=True)
                if link in seen_links:
                    continue
                seen_links.add(link)
                
                title = item.find("title").get_text(strip=True)
                desc = item.find("description").get_text(strip=True) if item.find("description") else ""
                pubdate = item.find("pubDate").get_text(strip=True) if item.find("pubDate") else ""
                
                summary = summarise(desc, link)
                category = classify(f"{title} {summary}")
                
                all_stories.append({
                    "title": title,
                    "link": link,
                    "pubDate": parse_pubdate(pubdate),
                    "summary": summary,
                    "category": category,
                    "source": source,
                    "district": district
                })
                
        except Exception as e:
            print(f"Failed to process feed {feed_url}: {e}")

    # Sort by date (newest first)
    all_stories.sort(key=lambda x: x['pubDate'], reverse=True)
    
    # Save
    import pathlib
    data_dir = pathlib.Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    with open(data_dir / "news.json", "w", encoding="utf-8") as f:
        json.dump(all_stories, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully scraped {len(all_stories)} stories.")

if __name__ == "__main__":
    main()
