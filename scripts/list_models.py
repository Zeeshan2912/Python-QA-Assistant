import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"Using API Key starting with: {api_key[:10] if api_key else 'None'}")

client = genai.Client(api_key=api_key)

try:
    print("Listing models...")
    models = client.models.list()
    for model in models:
        print(f"- Name: {model.name}")
        # Print display name or description if available
        display_name = getattr(model, "display_name", "")
        if display_name:
            print(f"  Display Name: {display_name}")
except Exception as e:
    print(f"Error listing models: {e}")

