#!/usr/bin/env python3
"""
Advanced UP & National News Aggregator with Strict Political/Governance Filtering.
"""

import json
import re
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

# --- Configuration ---

# 1. NATIONAL FEEDS (Default View)
NATIONAL_FEEDS = [
    "https://www.jagran.com/rss/news-national-rss.xml",
    "https://www.amarujala.com/rss/india-news.xml",
    "https://www.livehindustan.com/rss/national/rssfeed.xml",
    "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms", # India News
]

# 2. UP DISTRICT FEEDS (Strictly Filtered)
UP_FEEDS = [
    # --- State Level (General UP) ---
    "https://www.bhaskarenglish.in/rss-v1--category-16346.xml",
    "https://www.yugmarg.com/rssfeed/uttarpradesh-rss.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/rssfeed.xml",
    "https://www.bhaskar.com/rss-v1--category-2052.xml",
    "https://www.amarujala.com/rss/uttar-pradesh.xml",
    "https://cms.patrika.com/googlefeed/blog/location/uttar-pradesh-news",

    # --- Agra ---
    "https://www.amarujala.com/rss/agra.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/agra/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/agra-news",

    # --- Aligarh ---
    "https://www.amarujala.com/rss/aligarh.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/aligarh/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/aligarh-news",

    # --- Ambedkar Nagar ---
    "https://www.amarujala.com/rss/ambedkar-nagar.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/ambedkar-nagar/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/ambedkar-nagar-news",

    # --- Amethi & Gauriganj ---
    "https://www.amarujala.com/rss/amethi.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/amethi/rssfeed.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/gauriganj/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/amethi-news",

    # --- Amroha ---
    "https://www.amarujala.com/rss/amroha.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/amroha/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/amroha-news",

    # --- Auraiya ---
    "https://www.amarujala.com/rss/auraiya.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/auraiya/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/auraiya-news",

    # --- Ayodhya (Faizabad) ---
    "https://www.amarujala.com/rss/faizabad.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/faizabad/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/faizabad-news",
    "https://cms.patrika.com/googlefeed/blog/location/ayodhya-news",

    # --- Azamgarh ---
    "https://www.amarujala.com/rss/azamgarh.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/azamgarh/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/azamgarh-news",

    # --- Baghpat ---
    "https://www.amarujala.com/rss/baghpat.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/bagpat/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/bagpat-news",

    # --- Bahraich ---
    "https://www.amarujala.com/rss/bahraich.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/bahraich/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/bahraich-news",

    # --- Ballia ---
    "https://www.amarujala.com/rss/ballia.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/balia/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/ballia-news",

    # --- Balrampur ---
    "https://www.amarujala.com/rss/balrampur.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/balrampur/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/balrampur-news",

    # --- Banda ---
    "https://www.amarujala.com/rss/banda.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/banda/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/banda-news",

    # --- Barabanki ---
    "https://www.amarujala.com/rss/barabanki.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/barabanki/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/barabanki-news",

    # --- Bareilly ---
    "https://www.amarujala.com/rss/bareilly.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/bareilly/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/bareilly-news",

    # --- Basti ---
    "https://www.amarujala.com/rss/basti.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/basti/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/basti-news",

    # --- Bhadohi ---
    "https://www.amarujala.com/rss/bhadohi.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/bhadohi/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/bhadohi-news",

    # --- Bijnor ---
    "https://www.amarujala.com/rss/bijnor.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/bijnor/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/bijnor-news",

    # --- Budaun (Badaun) ---
    "https://www.amarujala.com/rss/budaun.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/badaun/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/budaun-news",

    # --- Bulandshahr ---
    "https://www.amarujala.com/rss/bulandshahr.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/bulandshahr/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/bulandshahr-news",

    # --- Chandauli ---
    "https://www.amarujala.com/rss/chandauli.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/chandauli/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/chandauli-news",

    # --- Chitrakoot ---
    "https://www.amarujala.com/rss/chitrakoot.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/chitrakoot/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/chitrakoot-news",

    # --- Deoria ---
    "https://www.amarujala.com/rss/deoria.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/deoria/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/deoria-news",

    # --- Etah ---
    "https://www.amarujala.com/rss/etah.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/etah/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/etah-news",

    # --- Etawah ---
    "https://www.amarujala.com/rss/etawah.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/etawah/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/etawah-news",

    # --- Farrukhabad ---
    "https://www.amarujala.com/rss/farrukhabad.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/farrukhabad/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/farrukhabad-news",

    # --- Fatehpur ---
    "https://www.amarujala.com/rss/fatehpur.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/fatehpur/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/fatehpur-news",

    # --- Firozabad ---
    "https://www.amarujala.com/rss/firozabad.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/firozabad/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/firozabad-news",

    # --- Ghaziabad ---
    "https://www.amarujala.com/rss/ghaziabad.xml",
    "https://cms.patrika.com/googlefeed/blog/location/ghaziabad-news",

    # --- Ghazipur ---
    "https://www.amarujala.com/rss/ghazipur.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/ghazipur/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/ghazipur-news",

    # --- Gonda ---
    "https://www.amarujala.com/rss/gonda.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/gonda/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/gonda-news",

    # --- Gorakhpur ---
    "https://www.amarujala.com/rss/gorakhpur.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/gorakhpur/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/gorakhpur-news",

    # --- Hamirpur ---
    "https://www.amarujala.com/rss/hamirpur.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/hamirpur/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/hamirpur-news",

    # --- Hapur ---
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/hapur/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/hapur-news",

    # --- Hardoi ---
    "https://www.amarujala.com/rss/hardoi.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/hardoi/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/hardoi-news",

    # --- Hathras ---
    "https://www.amarujala.com/rss/hathras.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/hathras/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/hathras-news",

    # --- Jalaun (Orai) ---
    "https://www.amarujala.com/rss/jalaun.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/orai/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/jalaun-news",

    # --- Jaunpur ---
    "https://www.amarujala.com/rss/jaunpur.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/jaunpur/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/jaunpur-news",

    # --- Jhansi ---
    "https://www.amarujala.com/rss/jhansi.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/jhansi/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/jhansi-news",

    # --- Kannauj ---
    "https://www.amarujala.com/rss/kannauj.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/kannauj/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/kannauj-news",

    # --- Kanpur (City, Rural, Dehat) ---
    "https://www.amarujala.com/rss/kanpur.xml",
    "https://www.amarujala.com/rss/ghatampur.xml",
    "https://www.amarujala.com/rss/bilhor.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/kanpur/rssfeed.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/kanpur-rural/rssfeed.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/bilhor/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/kanpur-news",

    # --- Kasganj ---
    "https://cms.patrika.com/googlefeed/blog/location/kasganj-news",

    # --- Kaushambi ---
    "https://www.amarujala.com/rss/kaushambi.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/kausambi/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/kaushambi-news",

    # --- Kushinagar ---
    "https://www.amarujala.com/rss/kushinagar.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/kushinagar/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/kushinagar-news",

    # --- Lakhimpur Kheri ---
    "https://www.amarujala.com/rss/lakhimpur-kheri.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/lakhimpur-kheri/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/lakhimpur-kheri-news",

    # --- Lalitpur ---
    "https://www.amarujala.com/rss/lalitpur.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/lalitpur/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/lalitpur-news",

    # --- Lucknow ---
    "https://www.amarujala.com/rss/lucknow.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/lucknow/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/lucknow-news",

    # --- Maharajganj ---
    "https://www.amarujala.com/rss/maharajganj.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/maharajganj/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/mahrajganj-news",

    # --- Mahoba ---
    "https://www.amarujala.com/rss/mahoba.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/mahoba/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/mahoba-news",

    # --- Mainpuri ---
    "https://www.amarujala.com/rss/mainpuri.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/mainpuri/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/mainpuri-news",

    # --- Mathura ---
    "https://www.amarujala.com/rss/mathura.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/mathura/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/mathura-news",

    # --- Mau ---
    "https://www.amarujala.com/rss/mau.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/mau/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/mau-news",

    # --- Meerut ---
    "https://www.amarujala.com/rss/meerut.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/meerut/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/meerut-news",

    # --- Mirzapur ---
    "https://www.amarujala.com/rss/mirzapur.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/mirzapur/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/mirzapur-news",

    # --- Moradabad ---
    "https://www.amarujala.com/rss/moradabad.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/moradabad/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/moradabad-news",

    # --- Muzaffarnagar ---
    "https://www.amarujala.com/rss/muzaffarnagar.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/muzaffarnagar/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/muzaffarnagar-news",

    # --- Noida / Greater Noida (Gautam Buddha Nagar) ---
    "https://cms.patrika.com/googlefeed/blog/location/noida-news",
    "https://cms.patrika.com/googlefeed/blog/location/greater-noida-news",

    # --- Pilibhit ---
    "https://www.amarujala.com/rss/pilibhit.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/pilibhit/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/pilibhit-news",

    # --- Pratapgarh ---
    "https://www.amarujala.com/rss/pratapgarh.xml",
    "https://cms.patrika.com/googlefeed/blog/location/pratapgarh-news",

    # --- Prayagraj (Allahabad) ---
    "https://www.amarujala.com/rss/allahabad.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/prayagraj/rssfeed.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/gangapar/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/prayagraj-news",

    # --- Raebareli ---
    "https://www.amarujala.com/rss/raebareli.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/raebareli/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/raebareli-news",

    # --- Rampur ---
    "https://www.amarujala.com/rss/rampur.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/rampur/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/rampur-news",

    # --- Saharanpur ---
    "https://www.amarujala.com/rss/saharanpur.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/saharanpur/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/saharanpur-news",

    # --- Sambhal ---
    "https://www.amarujala.com/rss/sambhal.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/sambhal/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/sambhal-news",

    # --- Sant Kabir Nagar ---
    "https://www.amarujala.com/rss/sant-kabir-nagar.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/sant-kabir-nagar/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/sant-kabir-nagar-news",

    # --- Shahjahanpur ---
    "https://www.amarujala.com/rss/shahjahanpur.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/shahjahanpur/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/shahjahanpur-news",

    # --- Shamli ---
    "https://www.amarujala.com/rss/shamli.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/shamli/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/shamli-news",

    # --- Shravasti ---
    "https://www.amarujala.com/rss/shravasti.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/shravasti/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/shravasti-news",

    # --- Siddharthnagar ---
    "https://www.amarujala.com/rss/siddharthnagar.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/siddharth-nagar/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/sidharthnagar-news",

    # --- Sitapur ---
    "https://www.amarujala.com/rss/sitapur.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/sitapur/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/sitapur-news",

    # --- Sonbhadra ---
    "https://www.amarujala.com/rss/sonbhadra.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/sonbhadra/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/sonbhadra-news",

    # --- Sultanpur ---
    "https://www.amarujala.com/rss/sultanpur.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/sultanpur/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/sultanpur-news",

    # --- Unnao ---
    "https://www.amarujala.com/rss/unnao.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/unnao/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/unnao-news",

    # --- Varanasi ---
    "https://www.amarujala.com/rss/varanasi.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/varanasi/rssfeed.xml",
    "https://cms.patrika.com/googlefeed/blog/location/varanasi-news",
]

# 3. KEYWORDS FOR FILTERING
# If these exist, the story is KEEPABLE.
POSITIVE_KEYWORDS = [
    "bjp", "sp", "samajwadi", "congress", "bsp", "modi", "yogi", "akhilesh", 
    "mayawati", "rahul", "priyanka", "dm", "ssp", "commissioner", "high court", 
    "supreme court", "verdict", "bail", "hearing", "yojana", "scheme", "project", 
    "inauguration", "protest", "dharna", "vidhan sabha", "loksabha", "mla", "mp", 
    "minister", "mantri", "election", "vote", "constituency", "development", 
    "road", "highway", "expressway", "airport", "budget", "policy", "governance",
    "cm office", "pm office", "nagarnigam", "municipality", "panchayat",
    "मुख्यमंत्री", "प्रधानमंत्री", "सांसद", "विधायक", "मंत्री", "योजना", "परियोजना",
    "अदालत", "कोर्ट", "जज", "फैसला", "जमानत", "हाईकोर्ट", "सुप्रीम कोर्ट", "धरना", 
    "प्रदर्शन", "ज्ञापन", "अधिकारी", "डीएम", "एसएसपी", "पुलिस कप्तान", "विकास",
    "सड़क", "पुल", "अस्पताल", "मेडिकल कॉलेज", "शिक्षा", "बजट", "घोटाला", "जांच"
]

# If these exist WITHOUT a Positive Keyword, the story is REJECTED.
NEGATIVE_KEYWORDS = [
    "wife", "husband", "lover", "suicide", "murder", "killed", "died", "accident", 
    "collision", "theft", "robbery", "looted", "rape", "molestation", "dowry", 
    "hanging", "poison", "dead body", "corpse", "love affair", "extramarital",
    "पति", "पत्नी", "प्रेमी", "प्रेमिका", "आत्महत्या", "फंदे", "लटका", "शव", "लाश",
    "हत्या", "मर्डर", "गोली मारकर", "चाकू", "रेप", "दुष्कर्म", "चोरी", "लूट", 
    "हादसा", "टक्कर", "डंपर", "एक्सीडेंट", "मौत", "घायल", "विवाद", "मारपीट"
]

def aggressive_clean(text: str) -> str:
    """Removes 'Link Copied', app promos, and other junk."""
    if not text: return ""
    
    # 1. Remove HTML
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    
    # 2. Specific Junk Phrases to Delete
    junk_phrases = [
        r"Link Copied", r"Also Read", r"Read More", r"Click Here",
        r"Download.*App", r"Follow us on", r"Subscribe to",
        r"मेरा शहर", r"My City", r"WhatsApp Channel", 
        r"Next Article", r"Please wait", r"Share this",
        r"Live Updates", r"Watch Video", r"विज्ञापन",
        r"रहें हर खबर से अपडेट.*", r"Get all India News.*"
    ]
    
    for pattern in junk_phrases:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        
    return re.sub(r'\s+', ' ', text).strip()

def is_relevant_story(title: str, summary: str) -> bool:
    """
    The Gatekeeper. 
    Returns True if:
    1. It has NO negative keywords.
    2. OR It has negative keywords BUT ALSO has positive (Political/Gov) keywords.
    """
    combined = (title + " " + summary).lower()
    
    has_positive = any(kw in combined for kw in POSITIVE_KEYWORDS)
    has_negative = any(kw in combined for kw in NEGATIVE_KEYWORDS)
    
    # If it's a crime story but involves politics/governance (e.g. MLA murder), Keep it.
    if has_negative and has_positive:
        return True
        
    # If it's just a crime story (husband killed wife), Reject it.
    if has_negative and not has_positive:
        return False
        
    # If it's neutral or purely positive, Keep it.
    return True

def get_category(text: str) -> str:
    text = text.lower()
    if any(k in text for k in ["court", "bail", "verdict", "justice", "अदालत", "कोर्ट", "फैसला"]):
        return "Judicial"
    if any(k in text for k in ["yojana", "scheme", "project", "inaugurate", "development", "road", "water", "supply", "योजना", "विकास", "सड़क"]):
        return "Governance & Dev"
    if any(k in text for k in ["protest", "strike", "demand", "memorandum", "opposition", "akhilesh", "mayawati", "congress", "sp", "bsp", "धरना", "प्रदर्शन", "विपक्ष", "सपा", "बसपा"]):
        return "Opposition/Political"
    if any(k in text for k in ["bjp", "yogi", "modi", "minister", "cm", "dm", "admin", "भाजपा", "योगी", "मोदी", "मंत्री", "प्रशासन"]):
        return "Government/NDA"
    return "General Political"

def fetch_feed(url: str, scope: str, district: str = "Uttar Pradesh") -> List[Dict]:
    stories = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.content, "xml")
        items = soup.find_all("item")
        
        for item in items:
            title = aggressive_clean(item.find("title").get_text())
            link = item.find("link").get_text()
            desc_raw = item.find("description").get_text() if item.find("description") else ""
            summary = aggressive_clean(desc_raw)
            pub_date = item.find("pubDate").get_text() if item.find("pubDate") else str(datetime.now())
            
            # --- THE FILTER CHECK ---
            if scope == "state" and not is_relevant_story(title, summary):
                continue
            # ------------------------

            # Deduplication ID
            story_id = hashlib.md5(link.encode()).hexdigest()
            
            stories.append({
                "id": story_id,
                "title": title,
                "link": link,
                "summary": summary[:250] + "..." if len(summary) > 250 else summary,
                "pubDate": pub_date,
                "scope": scope, # 'national' or 'state'
                "district": district,
                "category": get_category(title + " " + summary),
                "source": urlparse(url).netloc.replace("www.", "").split(".")[0].title()
            })
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        
    return stories

def main():
    all_data = []
    
    print("Fetching National News...")
    for url in NATIONAL_FEEDS:
        all_data.extend(fetch_feed(url, "national", "India"))
        
    print("Fetching UP News...")
    for url in UP_FEEDS:
        # Simple district inference from URL
        dist = "Uttar Pradesh"
        for d in ["lucknow", "kanpur", "varanasi", "noida", "ghaziabad", "agra", "meerut", "gorakhpur", "amethi", "ayodhya"]:
            if d in url:
                dist = d.title()
                break
        all_data.extend(fetch_feed(url, "state", dist))
        
    # Deduplicate based on ID
    unique_stories = {s['id']: s for s in all_data}.values()
    final_list = list(unique_stories)
    
    # Sort by Date (Requires parsing, doing simple sort for now, better parsing recommended in prod)
    # This is a basic sort, reliable parsing needs `dateutil`
    final_list.sort(key=lambda x: x['pubDate'], reverse=True)
    
    # Save
    with open("data/news.json", "w", encoding="utf-8") as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(final_list)} clean stories.")

if __name__ == "__main__":
    main()
