# Uttar Pradesh News Dashboard

This repository contains a self‑hosted dashboard that aggregates political and governance news about Uttar Pradesh from multiple RSS feeds.  The dashboard renders a list of unique articles summarised from the feeds and allows the user to filter by date range and category or view the top fifty stories published today.  It is designed to run without proprietary dependencies and can be hosted for free using static site hosts such as GitHub Pages or Netlify.

## Features
  
- **Multiple sources:** The back‑end script fetches RSS feeds from Dainik Bhaskar (English edition), Yugmarg and Live Hindustan【739932574703620†L29-L31】【960192868319618†L55-L73】.
- **Hourly updates:** By running the fetch script on a schedule (e.g. via GitHub Actions) the dashboard stays fresh between 07:00 and 22:00 local time.  The script deduplicates stories and writes the latest 60–100 items to `data/news.json`.
- **Summarised content:** Instead of showing raw links, the script extracts descriptions from the feeds and produces concise summaries so visitors get the gist without leaving the page.
- **Filterable by date and category:** The front‑end allows filtering by start/end date and by categories (Opposition Activity, NDA Activity, Governance issues and Judicial cases).  A quick “Top 50 Today” button displays the most recent stories.
- **Static hosting:** Because the dashboard consists of plain HTML, CSS, JSON and JavaScript it can be hosted on any static hosting platform.  No backend server is required once the JSON file has been generated.

## Directory structure

```
up_news_dashboard/
├── data/
│   └── news.json          # JSON file produced by the fetch script
├── fetch_news.py          # Script to download, summarise and classify RSS stories
├── index.html             # Web front‑end
├── script.js              # Client‑side logic for filtering and rendering
├── style.css              # Basic styling
└── README.md              # This file
```

## Usage

1. **Fetch the latest news:**

   Run the Python script to download and process the RSS feeds.  Ensure you have internet access and that the `requests` and `beautifulsoup4` packages are available (they are available by default in this repository's environment).  The script will write a JSON file to `data/news.json`.

   ```bash
   cd up_news_dashboard
   python fetch_news.py
   ```

2. **Preview locally:**

   You can open `index.html` directly in your browser.  For a better experience (avoiding cross‑origin restrictions) you may serve the directory with a simple HTTP server:

   ```bash
   cd up_news_dashboard
   python -m http.server 8000
   ```

   Then navigate to `http://localhost:8000/`.

3. **Deploy to GitHub Pages:**

   - Create a new repository on GitHub and push the contents of the `up_news_dashboard` directory to the root of the repository.
   - Enable GitHub Pages in your repository settings (choose the `main` branch and `/` as the folder).  Within a few minutes the dashboard will be available at `https://<username>.github.io/<repository>/`.

4. **Automate updates (optional):**

   To keep the dashboard up to date automatically, you can set up a GitHub Actions workflow that runs the fetch script hourly between 07:00 and 22:00 UTC+5:30 (adjust as needed).  Add a `.github/workflows/update_news.yml` file in your repository with the following content:

   ```yaml
   name: Update UP news
   on:
     schedule:
       # Run the job at the start of every hour between 01:30 and 16:30 UTC,
       # which corresponds to 07:00–22:00 IST.  Adjust to your timezone.
       - cron: '30 1-16 * * *'
   jobs:
     fetch:
       runs-on: ubuntu-latest
       steps:
         - name: Checkout
           uses: actions/checkout@v4
         - name: Setup Python
           uses: actions/setup-python@v5
           with:
             python-version: '3.10'
         - name: Install dependencies
           run: |
             python -m pip install --upgrade requests beautifulsoup4
         - name: Fetch latest news
           run: |
             python fetch_news.py
         - name: Commit and push if changed
           run: |
             git config user.name 'GitHub Action'
             git config user.email 'action@users.noreply.github.com'
             if [[ `git status --porcelain` ]]; then
               git add data/news.json
               git commit -m 'Update news feed'
               git push
             fi
   ```

   This workflow checks out your repository, runs the fetch script, and commits any changes to `data/news.json`.  GitHub Pages will automatically deploy the updated site.

## Limitations

- **Network access:** The fetch script relies on external websites and may fail if they return HTTP 403 or if there is no internet connectivity.  In such cases the script will skip the affected feed and continue with others.
- **Keyword classification:** The category assignment uses simple string matching.  While this catches many stories (e.g. those mentioning parties or leaders by name), it is not a substitute for a full NLP classifier.
- **Sample data:** Because the execution environment for this notebook does not permit outbound HTTP requests, the provided `news.json` file contains a handful of manually extracted stories from Dainik Bhaskar’s English feed.  When run in a normal environment the script will populate the JSON file with live data.

## Credits

This dashboard was assembled with publicly available RSS feeds.  The feed URLs were sourced from the official pages of Dainik Bhaskar, Yugmarg and Live Hindustan【739932574703620†L29-L31】【960192868319618†L55-L73】.  The code is released for educational purposes and does not claim ownership over the news content.
