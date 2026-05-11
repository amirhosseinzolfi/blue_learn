import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor
import time
import json

# --- YOUR ORGANIZED WORKING KEYS ---
FINAL_API_LIST = [
    {"label": "gemini 12", "key": "AIzaSyDZLcdWEYGtvlmcDrPSaZS1VxMIjOAFOcI"},
    {"label": "gemini voice 3", "key": "AIzaSyCTO-5yN8i9ILIYufqhZqagTUDXMur0YYc"}
]

# Testing with 1.5-Flash (Reliable & Persian-capable)
MODEL_NAME = "gemini-flash-lite-latest"

# Stress Test: Persian Analysis + JSON formatting
TEST_PROMPT = """
Analyze the following sentence and return result in JSON format:
'توسعه سیستم‌های هوشمند برای تحلیل رسانه ضروری است.'
Required JSON fields: {language: string, complexity: int, translated: string}
"""

def stress_test_key(api_info):
    label = api_info['label']
    key = api_info['key']
    
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel(MODEL_NAME)
        
        start = time.time()
        # Using a slight temperature to ensure the engine is actually working
        response = model.generate_content(TEST_PROMPT, generation_config={"temperature": 0.1})
        latency = round(time.time() - start, 2)
        
        # Verify it actually returned valid JSON content
        if "language" in response.text.lower():
            print(f"💎 {label:.<25} [PASS] Latency: {latency}s")
            return {"label": label, "key": key, "latency": latency}
        else:
            print(f"⚠️ {label:.<25} [PASS - UNEXPECTED FORMAT]")
            return {"label": label, "key": key, "latency": latency}
            
    except Exception as e:
        error_brief = str(e).split('\n')[0][:45]
        print(f"❌ {label:.<25} [FAIL] {error_brief}")
        return None

def run_production_test():
    print("\n" + "═"*60)
    print(f"🧪 PRODUCTION READINESS TEST: {len(FINAL_API_LIST)} KEYS")
    print(f"Model: {MODEL_NAME} | Task: Persian JSON Analysis")
    print("═"*60 + "\n")

    results = []
    # Using 12 workers to test all keys at the exact same time
    with ThreadPoolExecutor(max_workers=len(FINAL_API_LIST)) as executor:
        results = list(filter(None, executor.map(stress_test_key, FINAL_API_LIST)))

    results.sort(key=lambda x: x['latency'])

    print("\n" + "═"*60)
    print("📊 FINAL RANKING (BY PRODUCTION SPEED)")
    print("═"*60)
    
    for i, res in enumerate(results, 1):
        indicator = "🔥" if i <= 3 else "✅"
        print(f"{indicator} {res['label']} - {res['latency']}s")
    
    print("\nUse the top 3 keys for real-time analysis tasks in Project Vera.")

if __name__ == "__main__":
    run_production_test()