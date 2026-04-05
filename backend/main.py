from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import time
import asyncio

# Import our Pydantic Models
from models import DashboardResponseModel, KPISummary

# Import our TTL Cache
from cache import dashboard_cache

# Import our Async Services
from services.ingestion import fetch_all_sources_async
from services.extraction import run_extraction_async
from services.analysis import deduplicate_and_score, generate_sitrep

# Create a global lock for the OSINT pipeline to prevent SQLite database locks
pipeline_lock = asyncio.Lock()

# Initialize the FastAPI application
app = FastAPI(
    title="OSINT Conflict Monitoring API",
    description="Live intelligence ingestion, extraction, and scoring engine.",
    version="1.0.0"
)

# Configure CORS so React can consume this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/system/health")
async def health_check():
    return {"status": "online", "message": "OSINT Backend is running securely."}

@app.get("/api/v1/dashboard/live", response_model=DashboardResponseModel)
async def get_live_dashboard():
    """
    The master endpoint. Fetches, extracts, scores, and serves live OSINT data.
    Protected by a 2-minute TTL cache AND an asyncio Lock to prevent API rate limiting
    and SQLite database crashes (Cache Stampede).
    """
    start_time = time.time()
    
    # 1. First Check: The Fast Path
    # If the cache is full, return it instantly without making anyone wait in line.
    cached_dashboard = dashboard_cache.get("live_dashboard")
    if cached_dashboard:
        print("🚀 Serving dashboard from cache.")
        return cached_dashboard

    # 2. Acquire the Lock: The Bouncer
    # Only ONE request is allowed past this point at a time.
    async with pipeline_lock:
        
        # 3. Second Check: The Safety Net
        # While we were waiting in line, another request might have finished 
        # running the pipeline and filled the cache. We check one more time!
        cached_dashboard = dashboard_cache.get("live_dashboard")
        if cached_dashboard:
            print("🚀 Serving dashboard from cache (after waiting for lock).")
            return cached_dashboard
            
        print("🔍 CACHE MISS for 'live_dashboard'")
        print("⚠️ Cache miss. Triggering live OSINT pipeline...")
        
        try:
            # 4. Async Ingestion (Fetch everything at once)
            raw_data = await fetch_all_sources_async()
            raw_count = len(raw_data)
            
            if not raw_data:
                raise HTTPException(status_code=503, detail="Failed to fetch data from upstream sources.")

            # 5. Async Extraction (Parse unstructured text to strict JSON via Groq)
            extracted_events = await run_extraction_async(raw_data)
            
            # 6. Analysis & Data Science (Score, Deduplicate, Cluster)
            high_confidence_alerts = deduplicate_and_score(extracted_events)
            
            # 7. Calculate Dashboard KPIs
            total_events = len(high_confidence_alerts)
            active_actors = len(set([alert.get('actor_1') for alert in high_confidence_alerts if alert.get('actor_1')]))
            
            avg_severity = 0.0
            if total_events > 0:
                avg_severity = round(sum([alert.get('severity_score', 0) for alert in high_confidence_alerts]) / total_events, 2)
                
            alert_level = "ELEVATED" if avg_severity > 0.4 else "STANDARD"
            if avg_severity > 0.7:
                alert_level = "CRITICAL"

            kpis = KPISummary(
                total_events=total_events,
                active_actors=active_actors,
                alert_level=alert_level,
                avg_severity=avg_severity,
                raw_count=raw_count
            )

            # 8. Generate SITREP
            sitrep = generate_sitrep(high_confidence_alerts)

            # 9. Build the final payload
            final_dashboard = DashboardResponseModel(
                kpis=kpis,
                sitrep=sitrep,
                flash_alerts=high_confidence_alerts
            )

            # 10. Save to Cache and Return
            dashboard_cache.set("live_dashboard", final_dashboard.dict())
            
            process_time = round(time.time() - start_time, 2)
            print(f"🏁 Pipeline Complete in {process_time} seconds. Serving payload.")
            
            return final_dashboard

        except Exception as e:
            print(f"❌ Critical Pipeline Error: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal OSINT Pipeline Failure.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)