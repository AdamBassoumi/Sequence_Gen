from typing import List, Optional

from pydantic import BaseModel
from typing import Optional, List
from .SceneOutput import SceneOutput


class StoryResponse(BaseModel):
    story_id: str
    status: str
    story_title: str
    character_concept: Optional[str] = None
    visual_style: str
    character_name: Optional[str] = None
    scenes: List[SceneOutput]
    created_at: str
    output_dir: Optional[str] = None  # Path to output directory
