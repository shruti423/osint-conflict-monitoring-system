import pandas as pd
import numpy as np
import os

# Define paths consistent with your project structure
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, 'data', 'processed')
EXTRACTED_CSV = os.path.join(PROCESSED_DATA_DIR, "extracted_data.csv")
FINAL_FEED_CSV = os.path.join(PROCESSED_DATA_DIR, "final_intelligence_feed.csv")

def evaluate_pipeline():
    print("--- OSINT Intelligence Pipeline Evaluation ---\n")
    
    if not os.path.exists(EXTRACTED_CSV) or not os.path.exists(FINAL_FEED_CSV):
        print("Error: Required data files not found. Please run extractor.py and ml_engine.py first.")
        return

    df_extracted = pd.read_csv(EXTRACTED_CSV)
    df_final = pd.read_csv(FINAL_FEED_CSV)

    # 1. LLM Extraction Accuracy (Completeness)
    print("[1/3] LLM Extraction Audit")
    total = len(df_extracted)
    missing_actors = df_extracted['actor_1'].isna().sum()
    missing_events = df_extracted['event_type'].isna().sum()
    
    success_rate = ((total - missing_actors) / total) * 100
    print(f" - Total articles processed: {total}")
    print(f" - Extraction success rate (Actors): {success_rate:.2f}%")
    print(f" - Rows missing Event Type: {missing_events}")
    
    # 2. Clustering Performance (DBSCAN)
    print("\n[2/3] Clustering & Confidence Audit")
    # Confidence 0.35 is your baseline for 'Noise' (singletons)
    noise_count = len(df_final[df_final['confidence_score'] == 0.35])
    clustered_count = len(df_final[df_final['confidence_score'] > 0.35])
    
    print(f" - Unique/Singleton events (Noise): {noise_count}")
    print(f" - Events successfully clustered (Duplicates): {clustered_count}")
    
    if clustered_count > 0:
        avg_conf = df_final[df_final['confidence_score'] > 0.35]['confidence_score'].mean()
        print(f" - Average Confidence for clustered events: {avg_conf:.2f}")

    # 3. Anomaly Detection (Isolation Forest)
    print("\n[3/3] Severity & Anomaly Audit")
    top_anomalies = df_final.sort_values(by='severity_score', ascending=False).head(3)
    
    print(f" - Global Average Severity Score: {df_final['severity_score'].mean():.2f}")
    print("\n--- Top 3 Detected Anomalies (Check for High Severity) ---")
    for i, row in top_anomalies.iterrows():
        print(f"Severity: {row['severity_score']} | Actor: {row['actor_1']} | Event: {row['event_type']}")
        print(f"Text: {str(row['claim_text'])[:120]}...\n")

if __name__ == "__main__":
    evaluate_pipeline()