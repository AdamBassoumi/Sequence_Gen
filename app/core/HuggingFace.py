import time
from typing import List

from huggingface_hub import InferenceClient
from PIL import Image


class HuggingFace:
    def __init__(self, api_key, hugging_face_model):
        self.client = InferenceClient(
            provider="nscale",
            api_key=api_key,
        )
        self.hugging_face_model = hugging_face_model

    def generate_image(self, prompt: str, retries: int = 3) -> Image.Image:
        """Generate image from Pollinations.ai"""
        for attempt in range(retries):
            try:

                img = self.client.text_to_image(
                    prompt,
                    model=self.hugging_face_model,
                )

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
