import os
import asyncio
import requests
import feedparser
from dotenv import load_dotenv
from telethon import TelegramClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, '.env'))

NEWS_API_KEY = os.getenv("NEWSAPI_KEY")
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", 0))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")

def _fetch_newsapi_sync():
    """Fetches full 100 articles from NewsAPI."""
    if not NEWS_API_KEY:
        return []
    
    query = "(war OR military OR strike OR missile OR conflict OR idf OR troops OR rebel OR navy)"
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&pageSize=100&apiKey={NEWS_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        articles = response.json().get('articles', [])
        return [{"source": "NewsAPI", "text": f"{a.get('title', '')}. {a.get('description', '')}"} for a in articles]
    except Exception as e:
        print(f"NewsAPI Error: {e}")
        return []

def _fetch_rss_sync():
    """Fetches all articles from all targeted RSS feeds."""
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
                text = f"{entry.get('title', '')}. {entry.get('summary', '')}"
                all_articles.append({"source": "RSS", "text": text})
        except Exception:
            pass 
    return all_articles

async def _fetch_telegram_async():
    """Fetches raw Telegram OSINT asynchronously using your existing session."""
    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        return []
        
    session_path = os.path.join(BASE_DIR, 'osint_session')
    target_channels = ['clashreport', 'BellumActaNews', 'Liveuamap'] 
    all_messages = []
    
    try:
        client = TelegramClient(session_path, TELEGRAM_API_ID, TELEGRAM_API_HASH)
        await client.connect()
        
        # Ensure session is valid without hanging
        if not await client.is_user_authorized():
            print("❌ Telegram session invalid. Skipping Telegram to prevent server hang.")
            return []
            
        for channel in target_channels:
            async for message in client.iter_messages(channel, limit=50):
                if message.text:
                    all_messages.append({"source": f"Telegram (@{channel})", "text": message.text})
                    
        await client.disconnect()
        return all_messages
    except Exception as e:
        print(f"Telegram Error: {e}")
        return []

async def fetch_all_sources_async() -> list[dict]:
    """Fires all ingestion streams simultaneously."""
    print("📡 Firing concurrent ingestion streams (Full Volume)...")
    
    results = await asyncio.gather(
        asyncio.to_thread(_fetch_newsapi_sync),
        asyncio.to_thread(_fetch_rss_sync),
        _fetch_telegram_async()
    )
    
    master_raw_data = []
    for source_data in results:
        master_raw_data.extend(source_data)
        
    print(f"✅ Ingestion Complete. Pulled {len(master_raw_data)} raw items globally.")
    return master_raw_data