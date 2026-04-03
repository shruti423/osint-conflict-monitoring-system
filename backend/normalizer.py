import pandas as pd
import json
import os
from datetime import datetime, timezone
from urllib.parse import urlparse
import re

def keep_english_only(text):
    if not isinstance(text, str): return text
    cleaned = re.sub(r'[\u0400-\u052F\u0600-\u06FF\u0590-\u05FF\u4E00-\u9FFF]', '', text)
    cleaned = re.sub(r'[\U00010000-\U0010ffff]', '', cleaned)
    return cleaned.strip()


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BASE_DIR, 'data', 'raw')
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, 'data', 'processed')

os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

def extract_domain(url):
    try:
        return urlparse(str(url)).netloc.replace('www.', '')
    except:
        return "unknown"

def normalize_newsapi():
    print("Normalizing NewsAPI data...")
    filepath = os.path.join(RAW_DATA_DIR, "newsapi_raw.json")
    if not os.path.exists(filepath): return pd.DataFrame()
        
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    df = pd.DataFrame(data.get("articles", []))
    if df.empty: return df
    
    df_normalized = pd.DataFrame()
    df_normalized["event_datetime_utc"] = df["publishedAt"]
    df_normalized["source_name"] = df["source"].apply(lambda x: x.get('name') if isinstance(x, dict) else "NewsAPI")
    df_normalized["source_url"] = df["url"]
    df_normalized["source_type"] = "NewsAPI"
    df_normalized["claim_text"] = df["content"].fillna(df["description"])
    df_normalized["domain"] = df["url"].apply(extract_domain)
    return df_normalized

def normalize_rss():
    print("Normalizing RSS data...")
    filepath = os.path.join(RAW_DATA_DIR, "rss_raw.json")
    if not os.path.exists(filepath): return pd.DataFrame()
        
    with open(filepath, "r", encoding="utf-8") as f:
        df = pd.DataFrame(json.load(f))
        
    if df.empty: return df
    
    df_normalized = pd.DataFrame()
    df_normalized["event_datetime_utc"] = df.get("published", datetime.now(timezone.utc).isoformat())
    df_normalized["source_name"] = df["link"].apply(lambda x: extract_domain(x).split('.')[0].upper())
    df_normalized["source_url"] = df["link"]
    df_normalized["source_type"] = "RSS Feed"
    df_normalized["claim_text"] = df["summary"]
    df_normalized["domain"] = df["link"].apply(extract_domain)
    return df_normalized

def normalize_newsdata():
    print("Normalizing NewsData.io data...")
    filepath = os.path.join(RAW_DATA_DIR, "newsdata_raw.json")
    if not os.path.exists(filepath): return pd.DataFrame()
        
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    df = pd.DataFrame(data.get("results", []))
    if df.empty: return df
    
    df_normalized = pd.DataFrame()
    df_normalized["event_datetime_utc"] = df["pubDate"]
    df_normalized["source_name"] = df["source_id"].fillna("NewsData.io")
    df_normalized["source_url"] = df["link"]
    df_normalized["source_type"] = "NewsData.io"
    # Fallback cascade for text content
    df_normalized["claim_text"] = df.get("content", pd.Series([None]*len(df)))
    df_normalized["claim_text"] = df_normalized["claim_text"].fillna(df.get("description", ""))
    
    df_normalized["domain"] = df["link"].apply(extract_domain)
    return df_normalized

def normalize_telegram():
    """Formats raw Telegram OSINT data into our schema."""
    print("Normalizing Telegram OSINT data...")
    filepath = os.path.join(RAW_DATA_DIR, "telegram_raw.json")
    if not os.path.exists(filepath): return pd.DataFrame()
        
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    df = pd.DataFrame(data)
    if df.empty: return df
    
    df_normalized = pd.DataFrame()
    df_normalized["event_datetime_utc"] = df["date"]
    df_normalized["source_name"] = "@" + df["channel"]
    # Reconstruct the direct link to the Telegram message
    df_normalized["source_url"] = "https://t.me/" + df["channel"] + "/" + df["id"].astype(str)
    df_normalized["source_type"] = "Telegram OSINT"
    df_normalized["claim_text"] = df["text"]
    df_normalized["domain"] = "t.me"
    
    return df_normalized

def build_master_dataframe():
    df_news = normalize_newsapi()
    df_rss = normalize_rss()
    df_newsdata = normalize_newsdata()
    df_telegram = normalize_telegram()  # <-- Added Telegram here
    
    print("Merging NewsAPI, RSS, NewsData.io, and Telegram datasets into Master Schema...")
    # Added df_telegram to the concat list
    master_df = pd.concat([df_news, df_rss, df_newsdata, df_telegram], ignore_index=True)
    
    master_df["claim_text"] = master_df["claim_text"].apply(keep_english_only)
    master_df = master_df.dropna(subset=['claim_text'])
    master_df = master_df.drop_duplicates(subset=['source_url'])
    
    master_df["last_updated_at"] = datetime.now(timezone.utc).isoformat()
    
    llm_columns = ["country", "location_text", "actor_1", "actor_2", "event_type", "tags"]
    for col in llm_columns:
        master_df[col] = "" 
        
    ml_columns = ["severity_score", "confidence_score"]
    for col in ml_columns:
        master_df[col] = 0.0
        
    final_schema_order = [
        "event_datetime_utc", "source_name", "source_url", "source_type", 
        "claim_text", "country", "location_text", "actor_1", "actor_2", 
        "event_type", "domain", "severity_score", "confidence_score", 
        "tags", "last_updated_at"
    ]
    master_df = master_df[final_schema_order]
    
    print(f"✅ Normalization Complete! Total targeted articles ready for AI Extraction: {len(master_df)}")
    
    out_path = os.path.join(PROCESSED_DATA_DIR, "master_data.csv")
    master_df.to_csv(out_path, index=False)
    
    return master_df

if __name__ == "__main__":
    build_master_dataframe()