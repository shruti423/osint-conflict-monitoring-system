import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
from datetime import datetime, timezone

# Load the NLP model globally so it only loads into memory once when the server starts
# We use a very small, fast model designed for semantic clustering
print("⏳ Loading NLP Embedding Model (this takes a few seconds on startup)...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ NLP Model Loaded.")

def _calculate_severity(event: dict) -> float:
    """Rule-based severity scoring based on event type and keywords."""
    event_type = str(event.get('event_type', '')).lower()
    tags = str(event.get('tags', '')).lower()
    text = str(event.get('claim_text', '')).lower()
    
    # Kinetic/Lethal events get maximum severity
    if any(word in event_type for word in ['strike', 'bombing', 'artillery', 'assassination', 'downed']):
        return 0.95
    if any(word in text for word in ['killed', 'destroyed', 'shot down']):
        return 0.85
        
    # Military posturing
    if any(word in event_type for word in ['troop movement', 'interception', 'drill']):
        return 0.60
        
    # Diplomatic/Economic
    if any(word in event_type for word in ['sanction', 'threat', 'budget', 'diplomacy']):
        return 0.40
        
    return 0.20 # Default low severity

def deduplicate_and_score(events: list[dict]) -> list[dict]:
    """
    Uses vector embeddings to group similar reports together.
    Boosts confidence if multiple independent sources report the exact same event.
    """
    if not events:
        return []

    print(f"🔬 Running Data Science clustering on {len(events)} events...")

    # 1. Create a "fingerprint" string for each event to embed
    # We combine actors, location, and event type to ensure accurate semantic matching
    fingerprints = []
    for e in events:
        fp = f"{e.get('actor_1', '')} {e.get('event_type', '')} {e.get('actor_2', '')} in {e.get('location_text', '')}"
        fingerprints.append(fp)

    # 2. Convert text to vector embeddings
    embeddings = embedder.encode(fingerprints)

    # 3. Cluster using DBSCAN
    # eps=0.35 means reports must be ~65% semantically similar to merge
    # min_samples=1 means a report can be in a cluster by itself
    clustering = DBSCAN(eps=0.35, min_samples=1, metric='cosine').fit(embeddings)
    
    # 4. Merge clusters and calculate Confidence
    final_alerts = []
    clusters = {}
    
    for idx, label in enumerate(clustering.labels_):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(events[idx])
        
    for cluster_id, cluster_events in clusters.items():
        # Base the final alert on the most complete event in the cluster
        base_event = cluster_events[0]
        
        # Collect all sources that reported this
        sources = list(set([e.get('source_name', 'Unknown') for e in cluster_events]))
        
        # Confidence Score Logic: 
        # 1 source = 35% confident. 2 sources = 65% confident. 3+ sources = 90%+ confident.
        confidence = min(0.35 + (len(sources) - 1) * 0.30, 0.98)
        
        # Calculate Severity
        severity = _calculate_severity(base_event)
        
        # Build the final outgoing IntelligenceAlertModel payload
        alert = {
            "actor_1": base_event.get("actor_1"),
            "actor_2": base_event.get("actor_2"),
            "location_text": base_event.get("location_text"),
            "country": base_event.get("country"),
            "event_type": base_event.get("event_type"),
            "tags": base_event.get("tags"),
            "source_name": " | ".join(sources), # Shows all sources confirming this
            "claim_text": base_event.get("claim_text"),
            "severity_score": round(severity, 2),
            "confidence_score": round(confidence, 2),
            "published_at": datetime.now(timezone.utc).isoformat()
        }
        final_alerts.append(alert)

    # Sort so the highest severity alerts are at the top of the dashboard
    final_alerts.sort(key=lambda x: x['severity_score'], reverse=True)
    
    print(f"📊 Clustering reduced {len(events)} raw reports into {len(final_alerts)} unique High-Confidence Alerts.")
    return final_alerts

def generate_sitrep(alerts: list[dict]) -> str:
    """Generates a quick Situation Report text based on the highest severity alerts."""
    if not alerts:
        return "No significant activity detected in the current window."
        
    top_alert = alerts[0]
    return f"**CRITICAL UPDATE:** {top_alert['actor_1']} involved in {top_alert['event_type']} near {top_alert['location_text']}. Monitored across {len(top_alert['source_name'].split('|'))} source(s)."