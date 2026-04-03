import pandas as pd
import os
from datetime import datetime, timezone
from urllib.parse import urlparse

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BASE_DIR, 'data', 'raw')
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, 'data', 'processed')

def extract_domain(url):
    try:
        return urlparse(str(url)).netloc.replace('www.', '')
    except:
        return "unknown"

def process_gdelt():
    print("Starting GDELT Fast-Track Processing...")
    
    filepath = os.path.join(RAW_DATA_DIR, "gdelt_raw.csv")
    if not os.path.exists(filepath):
        print("❌ Could not find gdelt_raw.csv. Run ingestion.py first.")
        return

    # GDELT files are tab-separated (\t) and have no headers
    print("Reading raw GDELT data...")
    try:
        df = pd.read_csv(filepath, sep='\t', header=None, on_bad_lines='skip', low_memory=False)
    except Exception as e:
        print(f"❌ Failed to read GDELT file: {e}")
        return

    # CAMEO Root Codes Dictionary (Focusing on Conflict & Diplomacy)
    cameo_dict = {
        10: "Demand", 11: "Disapprove", 12: "Reject", 13: "Threaten",
        14: "Protest", 15: "Military Posture", 16: "Reduce Relations", 
        17: "Coerce", 18: "Assault", 19: "Fight", 20: "Mass Violence"
    }

    # GDELT 2.0 Column Indices
    # 6: Actor1Name, 16: Actor2Name, 28: EventRootCode, 52: ActionGeo_FullName, 60: SOURCEURL
    
    processed_df = pd.DataFrame()
    
    # We only want rows where the EventRootCode is a known conflict/diplomacy code (10-20)
    # GDELT column 28 is the EventRootCode
    df[28] = pd.to_numeric(df[28], errors='coerce')
    df_filtered = df[df[28].isin(cameo_dict.keys())].copy()
    
    print(f"Extracted {len(df_filtered)} high-relevance conflict events from GDELT database.")

    # Map to our 15-Field Schema
    processed_df["event_datetime_utc"] = datetime.now(timezone.utc).isoformat()
    processed_df["source_name"] = "GDELT Project"
    processed_df["source_url"] = df_filtered[60].fillna("http://gdeltproject.org")
    processed_df["source_type"] = "Structured Database"
    
    # Translate the numerical code to English
    processed_df["event_type"] = df_filtered[28].map(cameo_dict)
    
    processed_df["actor_1"] = df_filtered[6].fillna("Unknown")
    processed_df["actor_2"] = df_filtered[16].fillna("Unknown")
    processed_df["location_text"] = df_filtered[52].fillna("Unknown")
    processed_df["country"] = "" # GDELT country codes are complex, leaving blank for MVP
    
    # Synthesize a claim text for the ML Engine to read
    processed_df["claim_text"] = "Automated GDELT report: " + processed_df["event_type"] + " involving " + processed_df["actor_1"] + " and " + processed_df["actor_2"] + " near " + processed_df["location_text"]
    
    processed_df["domain"] = processed_df["source_url"].apply(extract_domain)
    processed_df["severity_score"] = 0.0
    processed_df["confidence_score"] = 0.0
    processed_df["tags"] = "gdelt, structured_data, automated"
    processed_df["last_updated_at"] = datetime.now(timezone.utc).isoformat()

    # Enforce strict 15-field schema
    final_schema_order = [
        "event_datetime_utc", "source_name", "source_url", "source_type", 
        "claim_text", "country", "location_text", "actor_1", "actor_2", 
        "event_type", "domain", "severity_score", "confidence_score", 
        "tags", "last_updated_at"
    ]
    processed_df = processed_df[final_schema_order]

    # Drop rows where actors are unknown
    processed_df = processed_df[(processed_df["actor_1"] != "Unknown") | (processed_df["actor_2"] != "Unknown")]

    out_path = os.path.join(PROCESSED_DATA_DIR, "gdelt_processed.csv")
    processed_df.to_csv(out_path, index=False)
    
    print(f"✅ GDELT Processing Complete! Saved {len(processed_df)} translated rows to {out_path}")

if __name__ == "__main__":
    process_gdelt()