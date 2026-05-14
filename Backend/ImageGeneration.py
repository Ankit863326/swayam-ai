import asyncio
from random import randint
from PIL import Image
import requests
from dotenv import get_key
import os
from time import sleep
from io import BytesIO

def open_images(prompt):
    folder_path = "Data"
    files = [f for f in os.listdir(folder_path)
             if f.startswith(prompt.replace(' ', '_')) and f.endswith('.jpg')]
    for image_file in files:
        image_path = os.path.join(folder_path, image_file)
        try:
            img = Image.open(image_path)
            print(f"Opening {image_path}")
            img.show()
            sleep(1)
        except IOError:
            print(f"Unable to open {image_path}")

API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {get_key('.env', 'HuggingFaceAPIKey')}"}

async def query(payload):
    response = await asyncio.to_thread(requests.post, API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.content
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

async def generate_images(prompt: str):
    tasks = []
    for _ in range(4):
        payload = {
            "inputs": f"{prompt}, quality=4k, sharpness=maximum, Ultra High details, High Resolution, seed={randint(0, 1000000)}"
        }
        task = asyncio.create_task(query(payload))
        tasks.append(task)

    image_bytes_list = await asyncio.gather(*tasks)

    for i, image_bytes in enumerate(image_bytes_list):
        if image_bytes:
            try:
                img = Image.open(BytesIO(image_bytes))
                img.save(os.path.join("Data", f"{prompt.replace(' ', '_')}_{i + 1}.jpg"), "JPEG")
            except Exception as e:
                print(f"Failed to save image {i+1}: {e}")

def GenerateImages(prompt: str):
    asyncio.run(generate_images(prompt))
    open_images(prompt)

while True:
    try:
        data_file = os.path.join("Frontend", "Files", "ImageGeneration.data")
        with open(data_file, "r") as f:
            data = f.read().strip()

        if not data:
            sleep(1)
            continue

        Prompt, Status = data.split(",")

        if Status.strip().lower() == "true":
            print("Generating Images...")
            GenerateImages(prompt=Prompt.strip())
            with open(data_file, "w") as f:
                f.write("False,False")
            break
        else:
            sleep(1)

    except Exception as e:
        print(f"Error: {e}")
        sleep(1)