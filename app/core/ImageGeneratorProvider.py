from .HuggingFace import HuggingFace
from .PolliNationsImgGenerator import PolliNationsImgGenerator


class ImageGeneratorProvider:
    def __init__(self, settings: dict):
        self.settings = settings

    def create(self):
        if self.settings.IMG_GEN_PROVIDER == "HUGGING_FACE":
            return HuggingFace(
                self.settings.HUGGING_FACE_KEY,
                self.settings.HUGGING_FACE_MODEL,
                self.settings.HUGGING_FACE_PROVIDER,
                num_inference_steps=self.settings.HUGGING_FACE_NUM_INFERENCE_STEPS,
                guidance_scale=self.settings.HUGGING_FACE_GUIDANCE_SCALE,
                width=self.settings.HUGGING_FACE_WIDTH,
                height=self.settings.HUGGING_FACE_HEIGHT,
            )
        elif self.settings.IMG_GEN_PROVIDER == "PolliNations":
            return PolliNationsImgGenerator()
