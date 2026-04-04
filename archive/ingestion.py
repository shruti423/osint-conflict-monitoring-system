import os
import requests
import json
import feedparser
import time
from dotenv import load_dotenv
from telethon.sync import TelegramClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, '.env')
RAW_DATA_DIR = os.path.join(BASE_DIR, 'data', 'raw')
os.makedirs(RAW_DATA_DIR, exist_ok=True)

load_dotenv(dotenv_path=ENV_PATH)
NEWS_API_KEY = os.getenv("NEWSAPI_KEY")
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")

def fetch_newsapi_data():
    print("Fetching high-quality conflict data from NewsAPI...")
    query = "(war OR military OR strike OR missile OR conflict OR idf OR troops OR rebel OR navy)"
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&pageSize=100&apiKey={NEWS_API_KEY}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        filepath = os.path.join(RAW_DATA_DIR, "newsapi_raw.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"✅ NewsAPI: Fetched {len(data.get('articles', []))} conflict articles.")
    except Exception as e:
        print(f"❌ Error fetching NewsAPI data: {e}")

def fetch_rss_data():
    print("Fetching data from Geopolitical & Defense RSS feeds...")
    rss_urls = [
        "http://feeds.bbci.co.uk/news/world/rss.xml", 
        "https://www.aljazeera.com/xml/rss/all.xml",  
        "https://mwi.westpoint.edu/feed/",            
        "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?max=20&Site=945" 
    ]
    all_articles = []
    
    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                article = {
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                    "published": entry.get("published", "")
                }
                all_articles.append(article)
        except Exception as e:
            pass 
            
    filepath = os.path.join(RAW_DATA_DIR, "rss_raw.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, indent=4)
    print(f"✅ RSS: Fetched {len(all_articles)} total geopolitical articles.")

def fetch_newsdata_io():
    print("Fetching multiple pages of conflict data from NewsData.io...")
    if not NEWSDATA_API_KEY:
        print("❌ Missing NEWSDATA_API_KEY. Skipping NewsData.io.")
        return

    query = "war OR military OR conflict OR strike OR troops OR diplomacy"
    base_url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&q={query}&category=politics,world&language=en"
    
    all_articles = []
    next_page = None
    
    for i in range(5):
        url = base_url
        if next_page:
            url += f"&page={next_page}"
            
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            results = data.get('results', [])
            all_articles.extend(results)
            print(f" - Page {i+1}: Fetched {len(results)} articles.")
            
            next_page = data.get('nextPage')
            if not next_page:
                break 
                
            time.sleep(1) 
            
        except Exception as e:
            print(f"❌ Error fetching NewsData.io Page {i+1}: {e}")
            break

    filepath = os.path.join(RAW_DATA_DIR, "newsdata_raw.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({"results": all_articles}, f, indent=4)
        
    print(f"✅ NewsData.io: Successfully fetched {len(all_articles)} total articles.")

def fetch_telegram_data():
    """Fetches raw frontline OSINT data directly from Telegram channels."""
    print("Fetching raw OSINT data from Telegram...")
    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        print("❌ Missing Telegram API keys. Skipping Telegram.")
        return

    # List of public OSINT/Conflict channels to scrape
    target_channels = ['clashreport', 'BellumActaNews', 'Liveuamap'] 
    all_messages = []
    
    session_path = os.path.join(BASE_DIR, 'osint_session')

    try:
        # This will prompt you in the terminal for your phone number on the very first run!
        with TelegramClient(session_path, TELEGRAM_API_ID, TELEGRAM_API_HASH) as client:
            for channel in target_channels:
                print(f" - Scraping Telegram channel: @{channel}")
                # Grab the last 50 messages from each channel
                for message in client.iter_messages(channel, limit=50):
                    if message.text: # Ensure it's text and not just an isolated image/video
                        all_messages.append({
                            "id": message.id,
                            "channel": channel,
                            "text": message.text,
                            "date": message.date.isoformat()
                        })
                        
        filepath = os.path.join(RAW_DATA_DIR, "telegram_raw.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(all_messages, f, indent=4)
            
        print(f"✅ Telegram: Fetched {len(all_messages)} raw frontline messages.")
    except Exception as e:
        print(f"❌ Error fetching Telegram data: {e}")

def run_ingestion():
    fetch_newsapi_data()
    fetch_rss_data()
    fetch_newsdata_io()
    fetch_telegram_data() # Added Telegram to the pipeline
    print("\n✅ Ingestion Phase Complete. All data saved to data/raw/")

if __name__ == "__main__":
    run_ingestion()