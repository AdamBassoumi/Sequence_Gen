from .HuggingFace import HuggingFace 
from .PolliNationsImgGenerator import PolliNationsImgGenerator

class ImageGeneratorProvider:
    def __init__(self, settings:dict):
        self.settings = settings 

    def create(self):
        if self.settings.IMG_GEN_PROVIDER == "HUGGING_FACE":
            return HuggingFace(
                self.settings.HUGGING_FACE_KEY,
                self.settings.HUGGING_FACE_MODEL
            )
        elif self.settings.IMG_GEN_PROVIDER == "PolliNations":
            return ImageGenerator()