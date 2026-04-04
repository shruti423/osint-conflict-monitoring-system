import os
import json
from groq import Groq
from dotenv import load_dotenv

# Load API key
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def test_entity_extraction():
    print("Testing GROQ API for entity extraction...")
    
    # A fake sample article to test the AI's logic
    sample_text = "Early Thursday morning, US naval forces intercepted an unmanned aerial vehicle launched by Iran-aligned groups near a commercial shipping route in the Red Sea. No damage was reported."
    
    # The Prompt to the LLM
    prompt = f"""
    Analyze the following text and extract the key conflict entities.
    Return ONLY a valid JSON object with the exact following keys: 
    - actor_1
    - actor_2
    - location_text
    - event_type
    
    Text: '{sample_text}'
    """
    
    try:
        # We use Llama 3 on Groq because it is blazingly fast and great at JSON
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an intelligence data extractor. Output only raw JSON."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant", 
            response_format={"type": "json_object"}, # This forces it to never return conversational text
        )
        
        result = chat_completion.choices[0].message.content
        print("\n--- Extraction Successful! AI Output ---")
        print(json.dumps(json.loads(result), indent=2))
        
    except Exception as e:
        print(f"Error during API call: {e}")

if __name__ == "__main__":
    test_entity_extraction()