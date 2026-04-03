import pandas as pd
import json
import os
import time
from groq import Groq
from dotenv import load_dotenv

# 1. Configuration & Pathing
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=ENV_PATH)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("CRITICAL ERROR: GROQ_API_KEY missing from .env file!")

client = Groq(api_key=GROQ_API_KEY)

PROCESSED_DATA_DIR = os.path.join(BASE_DIR, 'data', 'processed')
INPUT_CSV = os.path.join(PROCESSED_DATA_DIR, "master_data.csv")
OUTPUT_SUCCESS = os.path.join(PROCESSED_DATA_DIR, "extracted_data.csv")
OUTPUT_DEADLETTER = os.path.join(PROCESSED_DATA_DIR, "failed_extractions.csv")

def extract_entities(text):
    """Uses Groq to extract entities, highly optimized for both News and Telegram OSINT."""
    prompt = f"""
    Analyze the following intelligence text and extract specific entities for a global conflict monitoring database. 
    
    CRITICAL INSTRUCTIONS:
    You will receive both traditional news paragraphs AND raw frontline OSINT (Telegram messages). 
    Ignore emojis, hashtags, and URLs.
    
    Extract entities if the text describes ANY of the following:
    1. Kinetic warfare: drone strikes, artillery, bombings, troop movements, or base attacks.
    2. Diplomatic or verbal threats between nations/leaders.
    3. Military budget approvals or funding.
    4. Dismissals or appointments of high-ranking military leadership.
    5. Passing of security, defense, or conflict-related laws.

    Extract the following exactly:
    - actor_1: The primary entity, country, or group taking action (e.g., 'Russia', 'IDF', 'Donald Trump', 'US Navy').
    - actor_2: The target, subject, or secondary entity.
    - location_text: The specific city, region, or facility where the event occurred.
    - country: The overarching country where the event took place.
    - event_type: A short 2-3 word description (e.g., 'drone strike', 'artillery fire', 'verbal threat', 'budget approval').
    - tags: 2-3 relevant keywords separated by commas.

    Respond ONLY with a valid JSON object using the exact keys listed above. If an event is truly not found, output null.
    
    Text: {text}
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a precise military/geopolitical intelligence extraction API. Output strict JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1, 
            max_tokens=200
        )
        
        result = response.choices[0].message.content.strip()
        
        # Aggressively strip markdown if the LLM hallucinates it
        if result.startswith("```json"):
            result = result[7:]
        if result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]
            
        return json.loads(result.strip())
    except Exception as e:
        return None

def run_extraction():
    if not os.path.exists(INPUT_CSV):
        print(f"❌ Input file not found: {INPUT_CSV}")
        return
        
    print(f"Loading master dataset from {INPUT_CSV}...")
    df = pd.read_csv(INPUT_CSV)
    text_cols = ['actor_1', 'actor_2', 'location_text', 'country', 'event_type', 'tags']
    df[text_cols] = df[text_cols].fillna("").astype(str)
    
    if df.empty:
        print("Dataset is empty. Exiting.")
        return

    # Only process rows that haven't been extracted yet
    mask_to_process = (df['actor_1'].isna()) | (df['actor_1'] == "") | (df['event_type'].isna()) | (df['event_type'] == "")
    total_to_process = mask_to_process.sum()
    
    print(f"Found {total_to_process} new articles/messages requiring AI extraction.")
    
    processed_count = 0
    
    for index, row in df[mask_to_process].iterrows():
        text = str(row['claim_text'])
        
        # Skip empty text (common in Telegram when a post is just an image)
        if len(text.strip()) < 10:
            continue
            
        processed_count += 1
        print(f"Processing {processed_count}/{total_to_process} | Source: {row['source_name']}")
        
        extracted_data = extract_entities(text)
        
        if extracted_data:
            df.at[index, 'actor_1'] = extracted_data.get('actor_1') or ""
            df.at[index, 'actor_2'] = extracted_data.get('actor_2') or ""
            df.at[index, 'location_text'] = extracted_data.get('location_text') or ""
            df.at[index, 'country'] = extracted_data.get('country') or ""
            df.at[index, 'event_type'] = extracted_data.get('event_type') or ""
            df.at[index, 'tags'] = extracted_data.get('tags') or ""
            
        # Increased to 2.0 seconds to prevent Groq API rate limit crashes on high-volume Telegram data
        time.sleep(2.0) 
        
        # Periodic checkpoint
        if processed_count % 15 == 0:
            print(" -> Saving checkpoint...")
            df.to_csv(INPUT_CSV, index=False)

    # ---------------------------------------------------------
    # PIPELINE ROUTING: Success vs. Dead-Letter
    # ---------------------------------------------------------
    print("\nRouting Data...")
    
    # Define a "Valid" row: Must have an Actor OR an Event Type
    valid_mask = (df['actor_1'] != "") & (df['actor_1'].notna()) | (df['event_type'] != "") & (df['event_type'].notna())
    
    df_success = df[valid_mask].copy()
    df_failed = df[~valid_mask].copy()
    
    df_success.to_csv(OUTPUT_SUCCESS, index=False)
    
    if not df_failed.empty:
        df_failed.to_csv(OUTPUT_DEADLETTER, index=False)
        
    print(f"✅ Extraction Complete!")
    print(f"🟢 Successfully Extracted: {len(df_success)} events (Saved to extracted_data.csv)")
    print(f"🔴 Failed/Filtered: {len(df_failed)} events (Saved to failed_extractions.csv)")

if __name__ == "__main__":
    run_extraction()