import warnings
from typing import List, Optional, Any

warnings.filterwarnings("ignore")


class WatermarkRemover:
    """
    Safe stub implementation.
    """

    def __init__(self, device: str = None):
        self.device = device or "cpu"
        self.is_initialized = True
        self.pipe = None

    def initialize(self):
        """
        Stub initializer.
        Exists so calls do not fail.
        """
        self.is_initialized = True

    def remove_watermark(self, image: Any, prompt: Optional[str] = None) -> Any:
        """
        Stub watermark removal.

        Returns the image unchanged.
        """
        if not self.is_initialized:
            self.initialize()

        return image

    def remove_watermarks_batch(self, images: List[Any]) -> List[Any]:
        """
        Stub batch processing.
        """
        if not self.is_initialized:
            self.initialize()

        return list(images)
