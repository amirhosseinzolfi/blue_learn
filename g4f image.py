import g4f
from g4f.client import Client
import requests
import os
import time

# --- Configuration & System Instructions ---
SYSTEM_INSTRUCTION = (
    "Task: Professional Image Prompt Engineering. "
    "Output: Highly detailed, cinematic 16:9 widescreen composition. "
    "Style: Photorealistic, 8k, dramatic lighting, depth of field. "
    "Constraint: No watermarks, no text, no distorted limbs."
)

def generate_image_app():
    # Best working models for 2026
    models = [
        {"id": "flux", "name": "Flux-1.1 Pro (Best Overall)"},
        {"id": "midjourney", "name": "Midjourney (Artistic V8)"},
        {"id": "sdxl", "name": "SDXL (Stable & Fast)"},
        {"id": "dalle-3", "name": "DALL-E 3 (High Detail)"},
    ]

    print("\n--- AI Image Generator [Standard Edition] ---")
    for i, m in enumerate(models):
        print(f"[{i}] {m['name']}")

    try:
        choice = int(input("\nSelect model number: "))
        selected_model = models[choice]['id']
    except (ValueError, IndexError):
        print("Invalid selection. Defaulting to Flux.")
        selected_model = "flux"

    user_concept = input("Enter your visual concept: ")

    # Combine instruction with concept for the 'extracted' result you want
    final_prompt = f"{SYSTEM_INSTRUCTION} Concept: {user_concept}"

    print(f"\n[*] Requesting {selected_model}...")

    try:
        # Initializing the standard Client (Prevents the Protocol Error)
        client = Client()
        
        response = client.images.generate(
            model=selected_model,
            prompt=final_prompt,
            width=1344,
            height=768
        )

        image_url = response.data[0].url
        
        # URL Correction Logic
        if image_url.startswith("/"):
            image_url = f"https://pollinations.ai{image_url}"
        elif not image_url.startswith("http"):
            image_url = f"https://{image_url}"

        print(f"[*] Downloading Image from: {image_url}")

        # Extracting binary data to ensure a JPEG file result
        img_data = requests.get(image_url, timeout=30).content
        
        # Professional naming with timestamp
        timestamp = int(time.time())
        filename = f"image_{selected_model}_{timestamp}.jpg"
        
        with open(filename, 'wb') as handler:
            handler.write(img_data)

        print(f"\n[SUCCESS] File extracted: {os.path.abspath(filename)}")

    except Exception as e:
        print(f"\n[ERROR] Process failed: {e}")
        print("Tip: Run 'pip install -U g4f' to ensure your providers are up to date.")

if __name__ == "__main__":
    generate_image_app()