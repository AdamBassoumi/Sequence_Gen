from typing import Optional

from pydantic import BaseModel


class SceneOutput(BaseModel):
    """Model for individual scene output"""

    scene_number: int
    prompt: str
    image_url: Optional[str] = None
    image_path: Optional[str] = None  # Local file path
    negative_prompt: str
