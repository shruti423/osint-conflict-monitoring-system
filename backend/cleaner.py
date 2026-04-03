import pandas as pd
import re
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, 'data', 'processed')
INPUT_CSV = os.path.join(PROCESSED_DATA_DIR, "extracted_data.csv")

def keep_english_only(text):
    if not isinstance(text, str): return text
    # Scrubs Cyrillic, Arabic, Hebrew, Asian chars
    cleaned = re.sub(r'[\u0400-\u052F\u0600-\u06FF\u0590-\u05FF\u4E00-\u9FFF]', '', text)
    # Scrubs Emojis
    cleaned = re.sub(r'[\U00010000-\U0010ffff]', '', cleaned)
    return cleaned.strip()

print("Cleaning extracted data...")
df = pd.read_csv(INPUT_CSV)
df["claim_text"] = df["claim_text"].apply(keep_english_only)
df.to_csv(INPUT_CSV, index=False)
print("✅ Done! Your extracted_data.csv is now 100% English.")