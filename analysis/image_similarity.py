import requests
from PIL import Image
import imagehash
from io import BytesIO

def compute_image_similarity(img1_url, img2_url):
    try:
        if not img1_url or not img2_url:
            return 0.5
        resp1 = requests.get(img1_url, timeout=10)
        resp2 = requests.get(img2_url, timeout=10)
        img1 = Image.open(BytesIO(resp1.content)).convert('RGB')
        img2 = Image.open(BytesIO(resp2.content)).convert('RGB')
        hash1 = imagehash.phash(img1)
        hash2 = imagehash.phash(img2)
        max_hash = len(hash1.hash) ** 2
        dist = hash1 - hash2
        sim = 1 - (dist / max_hash)
        return sim
    except Exception as e:
        print(f'Image similarity error: {e}')
        return 0.5 