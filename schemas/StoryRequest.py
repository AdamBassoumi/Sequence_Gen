from pydantic import BaseModel

class StoryRequest(BaseModel):
    prompt: str
    max_num_scenes: int = 5
    remove_watermarks: bool = False
