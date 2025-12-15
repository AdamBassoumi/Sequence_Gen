import time
from typing import List

from huggingface_hub import InferenceClient
from PIL import Image


class HuggingFace:
    def __init__(
        self,
        api_key,
        hugging_face_model,
        hugging_face_provider,
        num_inference_steps: int | None = None,
        guidance_scale: float | None = None,
        width: int | None = None,
        height: int | None = None,
    ):
        self.client = InferenceClient(
            provider=hugging_face_provider,
            api_key=api_key,
        )
        self.hugging_face_model = hugging_face_model
        # Base quality parameters (can be adjusted per-request using a quality level)
        self.num_inference_steps = num_inference_steps
        self.guidance_scale = guidance_scale
        self.width = width
        self.height = height

    def _resolve_quality_params(self, quality: int | None):
        """Compute inference parameters from a discrete quality level (1-3)."""
        base_steps = self.num_inference_steps or 30
        base_guidance = self.guidance_scale or 7.5

        # Map quality to multipliers; 2 = base
        if quality == 1:
            step_factor, guidance_delta = 0.6, -1.0
        elif quality == 3:
            step_factor, guidance_delta = 1.4, 1.0
        else:
            step_factor, guidance_delta = 1.0, 0.0

        steps = max(10, int(base_steps * step_factor))
        guidance = max(1.0, base_guidance + guidance_delta)

        return steps, guidance

    def generate_image(self, prompt: str, retries: int = 3, quality: int | None = None) -> Image.Image:
        """Generate image from Pollinations.ai"""
        for attempt in range(retries):
            try:

                steps, guidance = self._resolve_quality_params(quality)

                img = self.client.text_to_image(
                    prompt["prompt"],
                    model=self.hugging_face_model,
                    seed=123456,
                    negative_prompt=(prompt["negative_prompt"]),
                    num_inference_steps=steps,
                    guidance_scale=guidance,
                    width=self.width,
                    height=self.height,
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

    def generate_sequence(self, prompts: List[str], quality: int | None = None) -> List[Image.Image]:
        """Generate a sequence of images"""
        images: List[Image.Image] = []

        for i, prompt in enumerate(prompts):
            print(f"Generating image {i+1}/{len(prompts)}...")
            try:
                img = self.generate_image(prompt, quality=quality)
                images.append(img)
            except Exception as e:
                print(f"Error generating image {i+1}: {str(e)}")
                raise

        return images
