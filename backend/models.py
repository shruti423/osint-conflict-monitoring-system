from pydantic import BaseModel, Field
from typing import List, Optional

# 1. The schema expected OUT of the Groq LLM
class ExtractedEntityModel(BaseModel):
    actor_1: Optional[str] = Field(default=None, description="Primary entity taking action")
    actor_2: Optional[str] = Field(default=None, description="Target or secondary entity")
    location_text: Optional[str] = Field(default=None, description="Specific city, region, or facility")
    country: Optional[str] = Field(default=None, description="Overarching country")
    event_type: Optional[str] = Field(default=None, description="Short 2-3 word description of event")
    tags: Optional[str] = Field(default=None, description="Relevant keywords separated by commas")

# 2. The finalized alert sent to the frontend (Combines extraction + scoring + provenance)
class IntelligenceAlertModel(ExtractedEntityModel):
    source_name: str = Field(description="Where this data came from (e.g., NewsAPI, clashreport)")
    claim_text: str = Field(description="The original text of the intelligence")
    severity_score: float = Field(default=0.0, description="0.0 to 1.0 scale")
    confidence_score: float = Field(default=0.0, description="0.0 to 1.0 scale based on sources")
    published_at: str = Field(description="ISO timestamp of the event")

# 3. KPI wrapper for the dashboard
class KPISummary(BaseModel):
    total_events: int
    active_actors: int
    alert_level: str
    avg_severity: float

# 4. The final payload sent to the React UI
class DashboardResponseModel(BaseModel):
    kpis: KPISummary
    sitrep: str
    flash_alerts: List[IntelligenceAlertModel]