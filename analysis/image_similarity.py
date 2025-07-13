import requests
from PIL import Image
import imagehash
from io import BytesIO

def compute_image_similarity(img1_url, img2_url):
    """
    Computes the perceptual hash similarity between two images from URLs.

    Uses the perceptual hash (pHash) algorithm to generate a hash for each image
    and calculates the difference between the hashes. The similarity is
    represented as a value between 0 and 1, where 1 indicates high similarity.

    Args:
        img1_url (str): The URL of the first image.
        img2_url (str): The URL of the second image.

    Returns:
        float: A similarity score between 0 and 1. Returns 0.5 on error or if URLs are missing.
    """
    try:
        if not img1_url or not img2_url:
            return 0.5
        resp1 = requests.get(img1_url, timeout=10)
        resp2 = requests.get(img2_url, timeout=10)
        img1 = Image.open(BytesIO(resp1.content)).convert('RGB')
        img2 = Image.open(BytesIO(resp2.content)).convert('RGB')

        # Compute perceptual hash for both images
        hash1 = imagehash.phash(img1)
        hash2 = imagehash.phash(img2)

        # Calculate similarity based on hash difference
        max_hash = len(hash1.hash) ** 2
        dist = hash1 - hash2
        sim = 1 - (dist / max_hash)
        return sim
    except Exception as e:
        print(f'Image similarity error: {e}')
        return 0.5 