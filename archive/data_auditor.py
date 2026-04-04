import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_CSV = os.path.join(BASE_DIR, 'data', 'processed', 'extracted_data.csv')

def run_audit():
    print("=== OSINT DATA HEALTH REPORT ===\n")
    
    if not os.path.exists(INPUT_CSV):
        print("Could not find extracted_data.csv")
        return
        
    df = pd.read_csv(INPUT_CSV)
    total_rows = len(df)
    
    print(f"Total Articles Analyzed: {total_rows}\n")
    
    print("--- Missing Data Check ---")
    columns_to_check = ['actor_1', 'actor_2', 'location_text', 'country', 'event_type']
    
    for col in columns_to_check:
        # Count how many are completely blank or NaN
        missing = df[col].isna().sum() + (df[col] == "").sum()
        health_percent = 100 - ((missing / total_rows) * 100)
        
        # Color coding for the terminal
        status = "✅ Healthy" if health_percent > 70 else "⚠️ Poor"
        print(f"{col.ljust(15)}: {total_rows - missing}/{total_rows} filled ({health_percent:.1f}% Health) - {status}")

    print("\n--- Content Relevance Check ---")
    # Let's see how many articles actually have conflict-related tags
    if 'tags' in df.columns:
        conflict_keywords = ['military', 'war', 'strike', 'navy', 'conflict', 'escalation', 'diplomacy']
        
        def is_relevant(tag_string):
            if pd.isna(tag_string): return False
            return any(word in str(tag_string).lower() for word in conflict_keywords)
            
        relevant_count = df['tags'].apply(is_relevant).sum()
        print(f"Highly Relevant Conflict Articles: {relevant_count}/{total_rows} ({(relevant_count/total_rows)*100:.1f}%)")
    
    print("\n================================")

if __name__ == "__main__":
    run_audit()