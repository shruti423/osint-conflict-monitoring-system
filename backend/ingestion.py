import os
import json
import requests
import feedparser
from dotenv import load_dotenv

# 1. Load the secret API keys from the .env file
load_dotenv()
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# 2. Setup the folder path to save our raw data
RAW_DATA_DIR = "../data/raw"
os.makedirs(RAW_DATA_DIR, exist_ok=True)

# --- FETCHING FUNCTIONS FOR OPEN SOURCES ---

def fetch_reliefweb():
    """Fetches official humanitarian reports from the UN safely."""
    print("Fetching ReliefWeb data...")
    url = "https://api.reliefweb.int/v1/reports"
    # Using a params dictionary safely encodes the spaces!
    params = {
        "appname": "SAIG_OSINT",
        "query[value]": "Iran OR Israel",
        "limit": 10
    }
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        filepath = os.path.join(RAW_DATA_DIR, "reliefweb_raw.json")
        with open(filepath, "w") as f:
            json.dump(response.json(), f)
        print("ReliefWeb data saved!")
    else:
        print(f"Failed to fetch ReliefWeb. Status Code: {response.status_code}")

def fetch_rss_feed():
    """Fetches news from a massive list of targeted RSS feeds."""
    print("Fetching expanded RSS feeds...")
    
    # We expand from 1 source to an entire array of global sources
    rss_urls = [
        "https://www.aljazeera.com/xml/rss/all.xml",
        "http://feeds.bbci.co.uk/news/world/middle_east/rss.xml", # BBC Middle East
        "https://www.jpost.com/rss/rssfeedsfrontpage", # Jerusalem Post
        "https://www.tehrantimes.com/rss", # Tehran Times (Local perspective)
        "https://rss.nytimes.com/services/xml/rss/nyt/MiddleEast.xml" # NYT
    ]
    
    articles = []
    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                # Broadened the search terms slightly to catch more regional data
                title_lower = entry.title.lower()
                if any(keyword in title_lower for keyword in ['iran', 'israel', 'strike', 'idf', 'tehran', 'gaza']):
                    articles.append({"title": entry.title, "link": entry.link, "summary": getattr(entry, 'summary', '')})
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            
    filepath = os.path.join(RAW_DATA_DIR, "rss_raw.json")
    with open(filepath, "w") as f:
        json.dump(articles, f)
    print(f"Expanded RSS feed data saved! Total articles: {len(articles)}")

def fetch_newsapi():
    """Fetches a high volume of global news articles."""
    print("Fetching high-volume NewsAPI data...")
    if not NEWSAPI_KEY:
        print("Skipping NewsAPI: No API key found in .env file.")
        return
        
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "Iran OR Israel OR IDF OR Hezbollah", # Broadened query
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 100, # CRANKED FROM 10 TO 100
        "apiKey": NEWSAPI_KEY
    }
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        filepath = os.path.join(RAW_DATA_DIR, "newsapi_raw.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(response.json(), f)
        print(f"NewsAPI data saved! Total articles: {len(response.json().get('articles', []))}")
    else:
        print(f"Failed to fetch NewsAPI. Status Code: {response.status_code}")

def fetch_gdelt():
    """Fetches the latest global event CSV from GDELT."""
    print("Fetching GDELT data...")
    # GDELT updates a master CSV every 15 minutes. This gets the latest one.
    url = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"
    response = requests.get(url)
    
    if response.status_code == 200:
        # The text file contains the URL to the actual CSV zip file
        latest_csv_url = response.text.split(" ")[2].strip()
        print(f"GDELT Latest File located at: {latest_csv_url}")
        # Note: We will download and extract this in the Pandas phase tomorrow!
    else:
        print("Failed to reach GDELT.")

# --- UPDATE YOUR MAIN BLOCK ---
if __name__ == "__main__":
    fetch_reliefweb()
    fetch_rss_feed()
    fetch_newsapi()
    fetch_gdelt()