from pydantic import BaseModel
from typing import Optional

class SceneOutput(BaseModel):
    """Model for individual scene output"""

    scene_number: int
    prompt: str
    image_url: Optional[str] = None
    image_path: Optional[str] = None  # Local file path
