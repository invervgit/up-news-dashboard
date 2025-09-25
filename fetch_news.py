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
from urllib.parse import urlparse
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


# List of RSS feeds to ingest.  Each entry in this list is a URL
# pointing to a feed or page that contains stories about Uttar Pradesh.
# The script will attempt to fetch and parse each one.  When adding
# new feeds here, ensure they point to a valid RSS/Atom feed or a
# webpage that can be parsed with BeautifulSoup.
#
# Note: rather than mapping names to URLs, we derive the source and
# district from the URL itself.  The source is extracted from the
# second‑level domain (e.g. "amarujala" becomes "Amarujala"), and the
# district is inferred from the last meaningful path segment (e.g.
# "https://www.amarujala.com/uttar-pradesh/gorakhpur" yields the
# district "Gorakhpur").  If no district can be determined the
# district is set to "General".
FEEDS: List[str] = [
    # Existing feeds from the initial implementation
    "https://www.bhaskarenglish.in/rss-v1--category-16346.xml",
    "https://www.yugmarg.com/rssfeed/uttarpradesh-rss.xml",
    "https://api.livehindustan.com/feeds/rss/uttar-pradesh/rssfeed.xml",
    # Additional feeds provided by the user.  These include generic
    # state‑level pages as well as district specific pages from
    # Amar Ujala, Live Hindustan, Times of India, Navbharat Times,
    # Patrika and other local news outlets.  The parser will skip
    # any entries that do not contain valid RSS items.
    "https://www.bhaskar.com/mera-shaher/local/uttar-pradesh/",
    "https://www.amarujala.com/uttar-pradesh",
    "https://www.amarujala.com/uttar-pradesh/gorakhpur",
    "https://www.amarujala.com/uttar-pradesh/lucknow",
    "https://www.amarujala.com/uttar-pradesh/amroha",
    "https://www.amarujala.com/uttar-pradesh/amethi",
    "https://www.amarujala.com/uttar-pradesh/ambedkar-nagar",
    "https://www.amarujala.com/uttar-pradesh/faizabad",
    "https://www.amarujala.com/uttar-pradesh/aligarh",
    "https://www.amarujala.com/uttar-pradesh/agra",
    "https://www.amarujala.com/uttar-pradesh/azamgarh",
    "https://www.amarujala.com/uttar-pradesh/etawah",
    "https://www.amarujala.com/uttar-pradesh/unnao",
    "https://www.amarujala.com/uttar-pradesh/etah",
    "https://www.amarujala.com/uttar-pradesh/auraiya",
    "https://www.amarujala.com/uttar-pradesh/kannauj",
    "https://www.amarujala.com/uttar-pradesh/kanpur",
    "https://www.amarujala.com/uttar-pradesh/kushinagar",
    "https://www.amarujala.com/uttar-pradesh/kaushambi",
    "https://www.amarujala.com/uttar-pradesh/ghazipur",
    "https://www.amarujala.com/uttar-pradesh/gonda",
    "https://www.amarujala.com/uttar-pradesh/ghatampur",
    "https://www.amarujala.com/uttar-pradesh/chandauli",
    "https://www.amarujala.com/uttar-pradesh/chitrakoot",
    "https://www.amarujala.com/uttar-pradesh/jalaun",
    "https://www.amarujala.com/uttar-pradesh/jaunpur",
    "https://www.amarujala.com/uttar-pradesh/jhansi",
    "https://www.amarujala.com/uttar-pradesh/deoria",
    "https://www.amarujala.com/uttar-pradesh/pilibhit",
    "https://www.amarujala.com/uttar-pradesh/pratapgarh",
    "https://www.amarujala.com/uttar-pradesh/allahabad",
    "https://www.amarujala.com/uttar-pradesh/fatehpur",
    "https://www.amarujala.com/uttar-pradesh/farrukhabad",
    "https://www.amarujala.com/uttar-pradesh/firozabad",
    "https://www.amarujala.com/uttar-pradesh/budaun",
    "https://www.amarujala.com/uttar-pradesh/bareilly",
    "https://www.amarujala.com/uttar-pradesh/balrampur",
    "https://www.amarujala.com/uttar-pradesh/ballia",
    "https://www.amarujala.com/uttar-pradesh/basti",
    "https://www.amarujala.com/uttar-pradesh/bahraich",
    "https://www.amarujala.com/uttar-pradesh/banda",
    "https://www.amarujala.com/uttar-pradesh/baghpat",
    "https://www.amarujala.com/uttar-pradesh/barabanki",
    "https://www.amarujala.com/uttar-pradesh/bijnor",
    "https://www.amarujala.com/uttar-pradesh/bulandshahr",
    "https://www.amarujala.com/uttar-pradesh/bhadohi",
    "https://www.amarujala.com/uttar-pradesh/mau",
    "https://www.amarujala.com/uttar-pradesh/mathura",
    "https://www.amarujala.com/uttar-pradesh/maharajganj",
    "https://www.amarujala.com/uttar-pradesh/mahoba",
    "https://www.amarujala.com/uttar-pradesh/mirzapur",
    "https://www.amarujala.com/uttar-pradesh/muzaffarnagar",
    "https://www.amarujala.com/uttar-pradesh/moradabad",
    "https://www.amarujala.com/uttar-pradesh/meerut",
    "https://www.amarujala.com/uttar-pradesh/mainpuri",
    "https://www.amarujala.com/uttar-pradesh/rampur",
    "https://www.amarujala.com/uttar-pradesh/raebareli",
    "https://www.amarujala.com/uttar-pradesh/lakhimpur-kheri",
    "https://www.amarujala.com/uttar-pradesh/lalitpur",
    "https://www.amarujala.com/uttar-pradesh/varanasi",
    "https://www.amarujala.com/uttar-pradesh/shamli",
    "https://www.amarujala.com/uttar-pradesh/shahjahanpur",
    "https://www.amarujala.com/uttar-pradesh/shravasti",
    "https://www.amarujala.com/uttar-pradesh/sant-kabir-nagar",
    "https://www.amarujala.com/uttar-pradesh/sambhal",
    "https://www.amarujala.com/uttar-pradesh/saharanpur",
    "https://www.amarujala.com/uttar-pradesh/siddharthnagar",
    "https://www.amarujala.com/uttar-pradesh/sitapur",
    "https://www.amarujala.com/uttar-pradesh/sultanpur",
    "https://www.amarujala.com/uttar-pradesh/sonbhadra",
    "https://www.amarujala.com/uttar-pradesh/hamirpur",
    "https://www.amarujala.com/uttar-pradesh/hardoi",
    "https://www.amarujala.com/uttar-pradesh/hathras",
    "https://www.livehindustan.com/uttar-pradesh/lucknow/news",
    "https://www.livehindustan.com/uttar-pradesh/varanasi/news",
    "https://www.livehindustan.com/uttar-pradesh/bareilly/news",
    "https://www.livehindustan.com/uttar-pradesh/moradabad/news",
    "https://www.livehindustan.com/uttar-pradesh/meerut/news",
    "https://www.livehindustan.com/uttar-pradesh/agra/news",
    "https://www.livehindustan.com/uttar-pradesh/aligarh/news",
    "https://www.livehindustan.com/uttar-pradesh/prayagraj/news",
    "https://www.livehindustan.com/uttar-pradesh/gorakhpur/news",
    "https://www.livehindustan.com/uttar-pradesh/kanpur/news",
    "https://www.livehindustan.com/uttar-pradesh/barabanki/news",
    "https://www.livehindustan.com/uttar-pradesh/azamgarh/news",
    "https://www.livehindustan.com/uttar-pradesh/balia/news",
    "https://www.livehindustan.com/uttar-pradesh/bhadohi/news",
    "https://www.livehindustan.com/uttar-pradesh/chandauli/news",
    "https://www.livehindustan.com/uttar-pradesh/ghazipur/news",
    "https://www.livehindustan.com/uttar-pradesh/jaunpur/news",
    "https://www.livehindustan.com/uttar-pradesh/mau/news",
    "https://www.livehindustan.com/uttar-pradesh/mirzapur/news",
    "https://www.livehindustan.com/uttar-pradesh/sonbhadra/news",
    "https://www.livehindustan.com/uttar-pradesh/basti/news",
    "https://www.livehindustan.com/uttar-pradesh/kushinagar/news",
    "https://www.livehindustan.com/uttar-pradesh/deoria/news",
    "https://www.livehindustan.com/uttar-pradesh/maharajganj/news",
    "https://www.livehindustan.com/uttar-pradesh/sant-kabir-nagar/news",
    "https://www.livehindustan.com/uttar-pradesh/siddharth-nagar/news",
    "https://www.livehindustan.com/uttar-pradesh/bagpat/news",
    "https://www.livehindustan.com/uttar-pradesh/shamli/news",
    "https://www.livehindustan.com/uttar-pradesh/bijnor/news",
    "https://www.livehindustan.com/uttar-pradesh/bulandshahr/news",
    "https://www.livehindustan.com/uttar-pradesh/hapur/news",
    "https://www.livehindustan.com/uttar-pradesh/muzaffarnagar/news",
    "https://www.livehindustan.com/uttar-pradesh/saharanpur/news",
    "https://www.livehindustan.com/uttar-pradesh/badaun/news",
    "https://www.livehindustan.com/uttar-pradesh/lakhimpur-kheri/news",
    "https://www.livehindustan.com/uttar-pradesh/pilibhit/news",
    "https://www.livehindustan.com/uttar-pradesh/shahjahanpur/news",
    "https://www.livehindustan.com/uttar-pradesh/etah/news",
    "https://www.livehindustan.com/uttar-pradesh/firozabad/news",
    "https://www.livehindustan.com/uttar-pradesh/mainpuri/news",
    "https://www.livehindustan.com/uttar-pradesh/mathura/news",
    "https://www.livehindustan.com/uttar-pradesh/ambedkar-nagar/news",
    "https://www.livehindustan.com/uttar-pradesh/amethi/news",
    "https://www.livehindustan.com/uttar-pradesh/gauriganj/news",
    "https://www.livehindustan.com/uttar-pradesh/shravasti/news",
    "https://www.livehindustan.com/uttar-pradesh/balrampur/news",
    "https://www.livehindustan.com/uttar-pradesh/bahraich/news",
    "https://www.livehindustan.com/uttar-pradesh/faizabad/news",
    "https://www.livehindustan.com/uttar-pradesh/gonda/news",
    "https://www.livehindustan.com/uttar-pradesh/raebareli/news",
    "https://www.livehindustan.com/uttar-pradesh/fatehpur/news",
    "https://www.livehindustan.com/uttar-pradesh/sitapur/news",
    "https://www.livehindustan.com/uttar-pradesh/sultanpur/news",
    "https://www.livehindustan.com/uttar-pradesh/auraiya/news",
    "https://www.livehindustan.com/uttar-pradesh/akbarpur/news",
    "https://www.livehindustan.com/uttar-pradesh/bilhor/news",
    "https://www.livehindustan.com/uttar-pradesh/lalitpur/news",
    "https://www.livehindustan.com/uttar-pradesh/mahoba/news",
    "https://www.livehindustan.com/uttar-pradesh/kanpur-rural/news",
    "https://www.livehindustan.com/uttar-pradesh/chitrakoot/news",
    "https://www.livehindustan.com/uttar-pradesh/banda/news",
    "https://www.livehindustan.com/uttar-pradesh/etawah/news",
    "https://www.livehindustan.com/uttar-pradesh/farrukhabad/news",
    "https://www.livehindustan.com/uttar-pradesh/kannauj/news",
    "https://www.livehindustan.com/uttar-pradesh/hamirpur/news",
    "https://www.livehindustan.com/uttar-pradesh/hardoi/news",
    "https://www.livehindustan.com/uttar-pradesh/jhansi/news",
    "https://www.livehindustan.com/uttar-pradesh/orai/news",
    "https://www.livehindustan.com/uttar-pradesh/unnao/news",
    "https://www.livehindustan.com/uttar-pradesh/hathras/news",
    "https://www.livehindustan.com/uttar-pradesh/amroha/news",
    "https://www.livehindustan.com/uttar-pradesh/rampur/news",
    "https://www.livehindustan.com/uttar-pradesh/sambhal/news",
    "https://www.livehindustan.com/uttar-pradesh/gangapar/news",
    "https://www.livehindustan.com/uttar-pradesh/kausambi/news",
    "https://timesofindia.indiatimes.com/india/uttar-pradesh",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/articlelist/21236867.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/mathura/articlelist/19928262.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/ayodhya/articlelist/19987335.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/gorakhpur/articlelist/61483701.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/aligarh/articlelist/75575224.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/agra/articlelist/61483684.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/varanasi/articlelist/61483673.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/allahabad/articlelist/5195544.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/meerut/articlelist/11364157.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/bareilly/articlelist/75575203.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/moradabad/articlelist/75575184.cms",
    "https://navbharattimes.indiatimes.com/city/shahjahanpur",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/ghaziabad/articlelist/75575006.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/bulandshahr/articlelist/75574987.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/bagpat/articlelist/75574968.cms",
    "https://jmdnewsflash.com/",
    "https://www.amarujala.com/delhi-ncr/ghaziabad",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/amethi/articlelist/92989585.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/auraiya/articlelist/92989626.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/baghpat/articlelist/19928219.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/ballia/articlelist/92989796.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/banda/articlelist/92989785.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/barabanki/articlelist/92989781.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/bareilly/articlelist/75575203.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/basti/articlelist/92989793.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/bhadohi/articlelist/92989735.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/bijnor/articlelist/92989774.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/chitrakoot/articlelist/92989572.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/etawah/articlelist/92989625.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/farrukhabad/articlelist/92989831.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/fatehpur/articlelist/92989835.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/ghazipur/articlelist/92989634.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/gonda/articlelist/92989542.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/hamirpur/articlelist/92989708.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/hapur/articlelist/92989677.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/hardoi/articlelist/92989699.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/jaunpur/articlelist/92989849.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/jhansi/articlelist/92989606.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/kannauj/articlelist/92989629.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/kanpur/articlelist/5194950.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/kaushambi/articlelist/92989659.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/kushinagar/articlelist/92989608.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/lalitpur/articlelist/92989752.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/maharajganj/articlelist/92989765.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/mahoba/articlelist/92989763.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/mainpuri/articlelist/92989761.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/mau/articlelist/92989767.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/mirzapur/articlelist/75575063.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/moradabad/articlelist/75575184.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/raebareli/articlelist/75575044.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/sambhal/articlelist/92989724.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/sant-kabir-nagar/articlelist/92989739.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/shamli/articlelist/92989748.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/shravasti/articlelist/92989746.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/siddharthnagar/articlelist/92989723.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/sonbhadra/articlelist/92989719.cms",
    "https://navbharattimes.indiatimes.com/state/uttar-pradesh/unnao/articlelist/92989661.cms",
    "https://chandaulisamachar.com/",
    "https://www.inextlive.com/uttar-pradesh/gorakhpur/",
    "https://public.app/city/news-in-maharajganj",
    "https://www.thevirallines.net/",
    "https://www.friendstimes.in/",
    "https://thedeoriatimes.com/",
    "https://www.azmlive.in/",
    "https://ballialive.in/",
    "https://ballialive.in/",
    "https://www.patrika.com/uttar-pradesh-news",
    "https://www.patrika.com/agra-news",
    "https://www.patrika.com/firozabad-news",
    "https://www.patrika.com/mainpuri-news",
    "https://www.patrika.com/mathura-news",
    "https://www.patrika.com/aligarh-news",
    "https://www.patrika.com/etah-news",
    "https://www.patrika.com/etawah-news",
    "https://www.patrika.com/hathras-news",
    "https://www.patrika.com/kasganj-news",
    "https://www.patrika.com/kaushambi-news",
    "https://www.patrika.com/prayagraj-news",
    "https://www.patrika.com/fatehpur-news",
    "https://www.patrika.com/pratapgarh-news",
    "https://www.patrika.com/azamgarh-news",
    "https://www.patrika.com/ballia-news",
    "https://www.patrika.com/mau-news",
    "https://www.patrika.com/bareilly-news",
    "https://www.patrika.com/budaun-news",
    "https://www.patrika.com/pilibhit-news",
    "https://www.patrika.com/shahjahanpur-news",
    "https://www.patrika.com/basti-news",
    "https://www.patrika.com/sant-kabir-nagar-news",
    "https://www.patrika.com/sidharthnagar-news",
    "https://www.patrika.com/banda-news",
    "https://www.patrika.com/chitrakoot-news",
    "https://www.patrika.com/hamirpur-news",
    "https://www.patrika.com/mahoba-news",
    "https://www.patrika.com/bahraich-news",
    "https://www.patrika.com/balrampur-news",
    "https://www.patrika.com/gonda-news",
    "https://www.patrika.com/shravasti-news",
    "https://www.patrika.com/ambedkar-nagar-news",
    "https://www.patrika.com/amethi-news",
    "https://www.patrika.com/ayodhya-news",
    "https://www.patrika.com/barabanki-news",
    "https://www.patrika.com/faizabad-news",
    "https://www.patrika.com/sultanpur-news",
    "https://www.patrika.com/deoria-news",
    "https://www.patrika.com/gorakhpur-news",
    "https://www.patrika.com/kushinagar-news",
    "https://www.patrika.com/mahrajganj-news",
    "https://www.patrika.com/jalaun-news",
    "https://www.patrika.com/jhansi-news",
    "https://www.patrika.com/lalitpur-news",
    "https://www.patrika.com/auraiya-news",
    "https://www.patrika.com/farrukhabad-news",
    "https://www.patrika.com/kannauj-news",
    "https://www.patrika.com/kanpur-news",
    "https://www.patrika.com/hardoi-news",
    "https://www.patrika.com/lakhimpur-kheri-news",
    "https://www.patrika.com/lucknow-news",
    "https://www.patrika.com/raebareli-news",
    "https://www.patrika.com/sitapur-news",
    "https://www.patrika.com/unnao-news",
    "https://www.patrika.com/bagpat-news",
    "https://www.patrika.com/bulandshahr-news",
    "https://www.patrika.com/greater-noida-news",
    "https://www.patrika.com/noida-news",
    "https://www.patrika.com/ghaziabad-news",
    "https://www.patrika.com/ghazipur-news",
    "https://www.patrika.com/hapur-news",
    "https://www.patrika.com/meerut-news",
    "https://www.patrika.com/bhadohi-news",
    "https://www.patrika.com/mirzapur-news",
    "https://www.patrika.com/sonbhadra-news",
    "https://www.patrika.com/amroha-news",
    "https://www.patrika.com/bijnor-news",
    "https://www.patrika.com/moradabad-news",
    "https://www.patrika.com/rampur-news",
    "https://www.patrika.com/sambhal-news",
    "https://www.patrika.com/muzaffarnagar-news",
    "https://www.patrika.com/saharanpur-news",
    "https://www.patrika.com/shamli-news",
    "https://www.patrika.com/chandauli-news",
    "https://www.patrika.com/jaunpur-news",
    "https://www.patrika.com/varanasi-news",
]


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

# ---------------------------------------------------------------------------
# URL helper functions
#
# To support filtering by geography and source, the following helpers
# derive the news source and district from a feed URL.  The source is
# approximated from the second‑level domain (e.g. "amarujala.com"
# becomes "Amarujala"), while the district is inferred from the
# last meaningful segment in the path (e.g. "uttar-pradesh/gorakhpur"
# yields "Gorakhpur").  If a district cannot be determined the
# function returns "General".

def extract_domain(url: str) -> str:
    """Return the network location (e.g. 'www.amarujala.com') for a URL."""
    try:
        return urlparse(url).netloc or ""
    except Exception:
        return ""


def extract_source(domain: str) -> str:
    """Derive a human‑friendly source name from a domain.

    This function takes the second‑level domain component and converts
    hyphens into spaces.  For example, 'www.livehindustan.com' becomes
    'Livehindustan'.  If the domain contains fewer than two parts the
    entire domain (sans 'www.') is title‑cased.
    """
    if not domain:
        return "Unknown"
    domain = domain.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    parts = domain.split(".")
    if len(parts) >= 2:
        # Use the second‑last component (e.g. 'amarujala' in 'amarujala.com')
        sld = parts[-2]
    else:
        sld = parts[0]
    sld = sld.replace("-", " ")
    return sld.title()


def extract_district(url: str) -> str:
    """Infer the district or locality from a feed URL.

    The function examines the path segments of the URL and returns the
    last segment that does not contain common generic terms (such as
    'uttar', 'pradesh', 'state', 'news', 'articlelist' etc.) or
    numeric identifiers.  Hyphens and underscores are converted into
    spaces and the result is title‑cased.  If no suitable segment
    exists the string 'General' is returned.
    """
    try:
        path = urlparse(url).path
    except Exception:
        return "General"
    segments = [s for s in path.split("/") if s]
    ignore_substrings = [
        "uttar", "pradesh", "uttar-pradesh", "state", "news",
        "articlelist", "rss", "rssfeed", "city", "nation",
        "district", "local", "india",
    ]
    district = None
    # Iterate over segments in reverse to find the last meaningful part
    for seg in reversed(segments):
        seg_no_ext = seg.split(".")[0]  # drop extensions like .cms
        # Skip purely numeric segments
        if seg_no_ext.isdigit():
            continue
        # Skip segments containing ignored substrings
        lowered = seg_no_ext.lower()
        if any(sub in lowered for sub in ignore_substrings):
            continue
        district = seg_no_ext
        break
    if district:
        district = district.replace("-", " ").replace("_", " ")
        return district.title()
    return "General"


# ---------------------------------------------------------------------------
# URL helper functions
#
# To support filtering by geography and source, the following helpers
# derive the news source and district from a feed URL.  The source is
# approximated from the second‑level domain (e.g. "amarujala.com"
# becomes "Amarujala"), while the district is inferred from the
# last meaningful segment in the path (e.g. "uttar-pradesh/gorakhpur"
# yields "Gorakhpur").  If a district cannot be determined the
# function returns "General".

def extract_domain(url: str) -> str:
    """Return the network location (e.g. 'www.amarujala.com') for a URL."""
    try:
        return urlparse(url).netloc or ""
    except Exception:
        return ""


def extract_source(domain: str) -> str:
    """Derive a human‑friendly source name from a domain.

    This function takes the second‑level domain component and converts
    hyphens into spaces.  For example, 'www.livehindustan.com' becomes
    'Livehindustan'.  If the domain contains fewer than two parts the
    entire domain (sans 'www.') is title‑cased.
    """
    if not domain:
        return "Unknown"
    domain = domain.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    parts = domain.split(".")
    if len(parts) >= 2:
        # Use the second‑last component (e.g. 'amarujala' in 'amarujala.com')
        sld = parts[-2]
    else:
        sld = parts[0]
    sld = sld.replace("-", " ")
    return sld.title()


def extract_district(url: str) -> str:
    """Infer the district or locality from a feed URL.

    The function examines the path segments of the URL and returns the
    last segment that does not contain common generic terms (such as
    'uttar', 'pradesh', 'state', 'news', 'articlelist' etc.) or
    numeric identifiers.  Hyphens and underscores are converted into
    spaces and the result is title‑cased.  If no suitable segment
    exists the string 'General' is returned.
    """
    try:
        path = urlparse(url).path
    except Exception:
        return "General"
    segments = [s for s in path.split("/") if s]
    ignore_substrings = [
        "uttar", "pradesh", "uttar-pradesh", "state", "news",
        "articlelist", "rss", "rssfeed", "city", "nation",
        "district", "local", "india",
    ]
    district = None
    # Iterate over segments in reverse to find the last meaningful part
    for seg in reversed(segments):
        seg_no_ext = seg.split(".")[0]  # drop extensions like .cms
        # Skip purely numeric segments
        if seg_no_ext.isdigit():
            continue
        # Skip segments containing ignored substrings
        lowered = seg_no_ext.lower()
        if any(sub in lowered for sub in ignore_substrings):
            continue
        district = seg_no_ext
        break
    if district:
        district = district.replace("-", " ").replace("_", " ")
        return district.title()
    return "General"


def parse_feed(url: str) -> List[Dict[str, str]]:
    """
    Download a feed and return a list of story dictionaries.  Each
    dictionary includes the story title, link, publication date, a
    generated summary, its category, the inferred source and the
    inferred district.  Duplicate detection is handled by the caller.
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Warning: failed to fetch feed {url}: {e}")
        return []
    content = response.content
    # Parse XML using BeautifulSoup's XML parser.  Some pages may not be
    # pure RSS but if they contain <item> tags the parser will find them.
    soup = BeautifulSoup(content, "xml")
    items = soup.find_all("item")
    stories: List[Dict[str, str]] = []
    # Derive the source and district from the feed URL.  These values
    # apply to every story in the feed.
    domain = extract_domain(url)
    source = extract_source(domain)
    district = extract_district(url)
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
            "source": source,
            "district": district,
        })
    return stories


def aggregate_feeds() -> List[Dict[str, str]]:
    """
    Iterate through all configured feeds, parse them and collate unique
    stories.  Duplicate stories are discarded based on their canonical
    link.  The aggregated list is sorted by publication date in reverse
    chronological order.
    """
    seen_links: set[str] = set()
    aggregated: List[Dict[str, str]] = []
    for feed_url in FEEDS:
        stories = parse_feed(feed_url)
        for story in stories:
            link = story.get("link")
            # Avoid duplicates by URL
            if link and link not in seen_links:
                seen_links.add(link)
                aggregated.append(story)
    # Sort descending by pubDate
    aggregated.sort(key=lambda s: s.get("pubDate", ""), reverse=True)
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
