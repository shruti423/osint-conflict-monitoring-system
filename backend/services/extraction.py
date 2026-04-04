import os
import json
import asyncio
from groq import AsyncGroq
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, '.env'))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Use the Async version of the Groq client
client = AsyncGroq(api_key=GROQ_API_KEY)

async def _extract_single_event(item: dict, semaphore: asyncio.Semaphore) -> dict:
    """Processes a single text snippet through Groq, controlled by a semaphore."""
    async with semaphore:
        text = item.get("text", "")
        source = item.get("source", "Unknown")
        
        # Skip empty text
        if len(text.strip()) < 10:
            return None

        prompt = f"""
        Analyze the following intelligence text and extract specific entities for a global conflict monitoring database. 
        
        Extract the following exactly:
        - actor_1: The primary entity taking action.
        - actor_2: The target or secondary entity.
        - location_text: The specific city, region, or facility.
        - country: The overarching country.
        - event_type: A short 2-3 word description (e.g., 'drone strike', 'artillery fire', 'budget approval').
        - tags: 2-3 relevant keywords separated by commas.

        Respond ONLY with a valid JSON object using the exact keys listed above. If an event is truly not found, output null.
        
        Text: {text}
        """
        
        try:
            response = await client.chat.completions.create(
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
                
            extracted_data = json.loads(result.strip())
            
            # If the LLM returned null or empty, drop it
            if not extracted_data or not extracted_data.get('actor_1'):
                return None
                
            # Merge the extracted structured data with the original provenance data
            return {
                "source_name": source,
                "claim_text": text,
                **extracted_data
            }
            
        except Exception as e:
            # We silently fail on individual extraction errors to keep the pipeline moving
            return None

async def run_extraction_async(raw_data: list[dict]) -> list[dict]:
    """
    Takes the raw data from the ingestion phase and extracts entities concurrently.
    Limits to 10 concurrent requests to respect Groq API limits.
    """
    print(f"🧠 Starting AI Extraction on {len(raw_data)} items...")
    
    # The Semaphore limits us to 10 simultaneous Groq API calls
    semaphore = asyncio.Semaphore(10)
    
    # Create a list of async tasks
    tasks = [_extract_single_event(item, semaphore) for item in raw_data]
    
    # Run them all, waiting for the full batch to complete
    results = await asyncio.gather(*tasks)
    
    # Filter out None values (failed extractions or non-events)
    valid_events = [res for res in results if res is not None]
    
    print(f"✅ Extraction Complete. Yielded {len(valid_events)} valid structured events.")
    return valid_events