import warnings
from typing import List, Optional

import torch
from diffusers import FluxKontextPipeline
from PIL import Image

warnings.filterwarnings("ignore")


class WatermarkRemover:
    def __init__(self, device: str = None):
        """Initialize watermark removal model"""
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.pipe = None
        self.is_initialized = False

    def initialize(self):
        """Lazy initialization of the model"""
        if not self.is_initialized:
            print(f"Initializing WatermarkRemover on {self.device}...")

            try:
                torch_dtype = (
                    torch.bfloat16 if torch.cuda.is_available() else torch.float32
                )

                self.pipe = FluxKontextPipeline.from_pretrained(
                    "black-forest-labs/FLUX.1-Kontext-dev", torch_dtype=torch_dtype
                ).to(self.device)

                # Load watermark remover adapter
                self.pipe.load_lora_weights(
                    "prithivMLmods/Kontext-Watermark-Remover",
                    weight_name="Kontext-Watermark-Remover.safetensors",
                    adapter_name="watermark_remover",
                )

                self.is_initialized = True
                print("WatermarkRemover initialized successfully")

            except Exception as e:
                raise Exception(f"Failed to initialize WatermarkRemover: {str(e)}")

    def remove_watermark(
        self, image: Image.Image, prompt: Optional[str] = None
    ) -> Image.Image:
        """Remove watermark from image"""
        if not self.is_initialized:
            self.initialize()

        # Set up the adapter
        self.pipe.set_adapters(["watermark_remover"], adapter_weights=[1.0])

        # Default prompt optimized for watermark removal
        if prompt is None:
            prompt = (
                "[photo content], remove any watermark text or logos from the image "
                "while preserving the background, texture, lighting, and overall realism. "
                "Ensure the edited areas blend seamlessly with surrounding details, "
                "leaving no visible traces of watermark removal."
            )

        # Process the image
        try:
            result = self.pipe(
                image=image.convert("RGB"),
                prompt=prompt,
                guidance_scale=2.5,
                width=image.size[0],
                height=image.size[1],
                num_inference_steps=28,
                generator=torch.Generator(device=self.device).manual_seed(42),
            ).images[0]

            return result

        except Exception as e:
            raise Exception(f"Failed to remove watermark: {str(e)}")

    def remove_watermarks_batch(self, images: List[Image.Image]) -> List[Image.Image]:
        """Remove watermarks from a batch of images"""
        return [self.remove_watermark(img) for img in images]
