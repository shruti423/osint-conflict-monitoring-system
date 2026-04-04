import pandas as pd
import os
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from groq import Groq
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=ENV_PATH)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

PROCESSED_DATA_DIR = os.path.join(BASE_DIR, 'data', 'processed')
INPUT_CSV = os.path.join(PROCESSED_DATA_DIR, "extracted_data.csv")
OUTPUT_CSV = os.path.join(PROCESSED_DATA_DIR, "final_intelligence_feed.csv")
DASHBOARD_JSON = os.path.join(PROCESSED_DATA_DIR, "dashboard_data.json")

def generate_sitrep(top_events_text):
    if not client: return "GROQ API Key missing."
    prompt = f"Write a 3-sentence Executive SITREP based on these events:\n{top_events_text}"
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2, max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"SITREP Error: {e}"

def run_ml_engine():
    print("Starting ML Engine...")
    df = pd.read_csv(INPUT_CSV)
    df.fillna("", inplace=True)
    
    text_data = df['claim_text'] + " " + df['event_type'] + " " + df['location_text']
    vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
    X_vectors = vectorizer.fit_transform(text_data)
    
    print("Running DBSCAN Clustering (eps=0.6)...")
    dbscan = DBSCAN(eps=0.6, min_samples=2, metric='cosine')
    df['cluster_id'] = dbscan.fit_predict(X_vectors)
    
    cluster_counts = df['cluster_id'].value_counts()
    
    def calculate_confidence(cluster_id):
        if cluster_id == -1: return 0.35 
        size = cluster_counts[cluster_id]
        return round(min(0.95, 0.5 + (size * 0.1)), 2)
        
    df['confidence_score'] = df['cluster_id'].apply(calculate_confidence)
    
    # Anomaly/Severity Score
    iso_forest = IsolationForest(contamination=0.1, random_state=42)
    iso_forest.fit(X_vectors.toarray())
    inverted_scores = iso_forest.decision_function(X_vectors.toarray()).reshape(-1, 1) * -1 
    df['severity_score'] = MinMaxScaler(feature_range=(0.1, 1.0)).fit_transform(inverted_scores).round(2)
    
    # ---------------------------------------------------------
    # RESTORED VISUALIZATION BLOCK
    # ---------------------------------------------------------
    print("Generating 2D Cluster Visualization...")
    pca = PCA(n_components=2)
    X_2d = pca.fit_transform(X_vectors.toarray())
    
    plt.figure(figsize=(12, 8))
    scatter = plt.scatter(X_2d[:, 0], X_2d[:, 1], c=df['cluster_id'], cmap='tab20', alpha=0.6, s=50)
    
    anomalies = X_2d[df['severity_score'] > 0.8]
    if len(anomalies) > 0:
        plt.scatter(anomalies[:, 0], anomalies[:, 1], color='red', marker='*', s=200, label='High Severity Anomaly')
    
    plt.title("OSINT Conflict Data: NLP Clustering & Anomalies")
    plt.xlabel("PCA Dimension 1 (Text Variance)")
    plt.ylabel("PCA Dimension 2 (Text Variance)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    viz_path = os.path.join(PROCESSED_DATA_DIR, "cluster_visualization.png")
    plt.savefig(viz_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved visualization to: {viz_path}")
    # ---------------------------------------------------------

    print("Generating Executive SITREP & JSON...")
    clean_df = df[(df['actor_1'].str.strip() != "") & (df['event_type'].str.strip() != "")]
    top_events = clean_df.sort_values(by=['severity_score', 'confidence_score'], ascending=[False, False]).head(5)
    
    events_text = "\n".join([f"- {row['actor_1']} in {row['location_text']}: {row['claim_text']}" for _, row in top_events.iterrows()])
    sitrep_text = generate_sitrep(events_text)
    
    avg_severity = df['severity_score'].mean()
    alert_level = "CRITICAL" if avg_severity > 0.7 else "ELEVATED" if avg_severity > 0.45 else "STANDARD"
    
    dashboard_data = {
        "kpis": {
            "total_events": len(df),
            "active_actors": int(clean_df['actor_1'].nunique()),
            "alert_level": alert_level,
            "avg_severity": round(float(avg_severity), 2)
        },
        "sitrep": sitrep_text,
        "flash_alerts": top_events[['actor_1', 'location_text', 'event_type', 'severity_score', 'confidence_score']].to_dict(orient='records')
    }
    
    with open(DASHBOARD_JSON, "w") as f:
        json.dump(dashboard_data, f, indent=4)
        
    df.drop(columns=['cluster_id'], inplace=True, errors='ignore')
    df.to_csv(OUTPUT_CSV, index=False)
    
    print("\n" + "="*50)
    print("✅ ML Engine Complete!")
    print(f"📁 Dashboard JSON is saved at: {DASHBOARD_JSON}")
    print(f"📁 Cluster Map is saved at: {viz_path}")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_ml_engine()