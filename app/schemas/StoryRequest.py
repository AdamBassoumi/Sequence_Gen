from pydantic import BaseModel
from typing import Optional


class StoryRequest(BaseModel):
    prompt: str
    max_num_scenes: int = 5
    remove_watermarks: bool = False
    # Optional visual style hint (e.g. "realistic", "anime", "comic book")
    visual_style: Optional[str] = None
    # Discrete quality level (1 = rapide, 2 = normal, 3 = haute qualité)
    quality: int = 2
