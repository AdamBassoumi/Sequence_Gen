import time
import urllib.parse
from io import BytesIO
from typing import List, Optional

import requests
from PIL import Image


class ImageGenerator:
    def __init__(self) -> None:
        self.base_url = "https://image.pollinations.ai/prompt/"

    def generate_image(self, prompt: str, retries: int = 3) -> Image.Image:
        """Generate image from Pollinations.ai"""
        for attempt in range(retries):
            try:
                encoded_prompt = urllib.parse.quote(prompt)
                url = f"{self.base_url}{encoded_prompt}"

                response = requests.get(url, timeout=30)
                response.raise_for_status()

                img = Image.open(BytesIO(response.content))

                # Verify image is valid
                if img.mode != "RGB":
                    img = img.convert("RGB")

                return img

            except Exception as e:
                if attempt == retries - 1:
                    raise RuntimeError(
                        f"Failed to generate image after {retries} attempts: {str(e)}"
                    )
                time.sleep(2**attempt)  # Exponential backoff
        
        # This should never be reached due to the raise above, but mypy needs it
        raise RuntimeError("Unexpected error in generate_image")

    def generate_sequence(self, prompts: List[str]) -> List[Image.Image]:
        """Generate a sequence of images"""
        images: List[Image.Image] = []

        for i, prompt in enumerate(prompts):
            print(f"Generating image {i+1}/{len(prompts)}...")
            try:
                img = self.generate_image(prompt)
                images.append(img)
            except Exception as e:
                print(f"Error generating image {i+1}: {str(e)}")
                raise

        return images