from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
import os
from datetime import datetime

from app.core.prompt_generator import PromptGenerator, GeneratedPrompts
from app.core.image_generator import ImageGenerator
from app.core.watermark_remover import WatermarkRemover

# Models
class StoryRequest(BaseModel):
    prompt: str
    num_scenes: int = 3
    remove_watermarks: bool = False

class StoryResponse(BaseModel):
    story_id: str
    status: str
    story_title: str
    character_concept: Optional[str] = None
    visual_style: str
    character_name: Optional[str] = None  # For backward compatibility
    prompts: List[str]
    image_urls: Optional[List[str]] = None
    created_at: str

# Initialize app
app = FastAPI(
    title="Photo Sequence Generator API",
    description="Generate consistent photo sequences from text prompts",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
prompt_gen = None
image_gen = None
watermark_remover = None

# Storage for generated stories
story_store = {}

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global prompt_gen, image_gen, watermark_remover
    
    try:
        prompt_gen = PromptGenerator()
        image_gen = ImageGenerator()
        # watermark_remover = WatermarkRemover()  # Commented out temporarily
        print("All components initialized successfully")
    except Exception as e:
        print(f"Warning: {str(e)}")

@app.post("/generate-story", response_model=StoryResponse)
async def generate_story(request: StoryRequest, background_tasks: BackgroundTasks):
    """Generate a story sequence from a prompt"""
    try:
        # Generate story ID
        story_id = str(uuid.uuid4())
        
        # Generate prompts
        generated_prompts = prompt_gen.generate_story_prompts(
            request.prompt, 
            request.num_scenes
        )
        
        # Create image prompts
        image_prompts = [
            prompt_gen.create_image_prompt(p) 
            for p in generated_prompts.prompts
        ]
        
        # Store story info
        story_data = {
            "story_id": story_id,
            "status": "pending",
            "story_title": generated_prompts.story_title,
            "character_concept": generated_prompts.character_concept,
            "visual_style": generated_prompts.visual_style,
            "character_name": generated_prompts.character_name,
            "prompts": image_prompts,
            "images": [],
            "created_at": datetime.now().isoformat()
        }
        story_store[story_id] = story_data
        
        # Add background task for image generation
        background_tasks.add_task(
            generate_images_task,
            story_id,
            image_prompts,
            request.remove_watermarks
        )
        
        return StoryResponse(
            story_id=story_id,
            status="processing",
            story_title=generated_prompts.story_title,
            character_concept=generated_prompts.character_concept,
            visual_style=generated_prompts.visual_style,
            character_name=generated_prompts.character_name,
            prompts=image_prompts,
            created_at=story_data["created_at"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/story/{story_id}")
async def get_story(story_id: str):
    """Get story status and results"""
    if story_id not in story_store:
        raise HTTPException(status_code=404, detail="Story not found")
    
    story = story_store[story_id]
    
    # Create image URLs if images exist
    image_urls = None
    if story.get("images"):
        image_urls = [f"/images/{story_id}/{i}.png" for i in range(len(story["images"]))]
    
    return StoryResponse(
        story_id=story_id,
        status=story["status"],
        story_title=story["story_title"],
        character_concept=story.get("character_concept"),
        visual_style=story.get("visual_style", "cinematic"),
        character_name=story.get("character_name"),
        prompts=story["prompts"],
        image_urls=image_urls,
        created_at=story["created_at"]
    )

@app.get("/images/{story_id}/{image_index}")
async def get_image(story_id: str, image_index: int):
    """Get generated image"""
    if story_id not in story_store:
        raise HTTPException(status_code=404, detail="Story not found")
    
    story = story_store[story_id]
    
    if not story.get("images") or image_index >= len(story["images"]):
        raise HTTPException(status_code=404, detail="Image not found")
    
    # In production, serve from file system or cloud storage
    image_path = story["images"][image_index]
    
    if os.path.exists(image_path):
        return FileResponse(image_path, media_type="image/png")
    else:
        raise HTTPException(status_code=404, detail="Image file not found")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/debug/prompt-structure")
async def debug_prompt_structure():
    """Debug endpoint to check prompt structure"""
    try:
        # Create a test prompt to see the structure
        test_prompt = "A heroic astronaut on Mars"
        prompts = prompt_gen.generate_story_prompts(test_prompt, 1)
        
        return {
            "fields_available": dir(prompts),
            "story_title": prompts.story_title,
            "visual_style": prompts.visual_style,
            "character_concept": prompts.character_concept,
            "character_name": prompts.character_name,
            "has_character_concept": hasattr(prompts, 'character_concept'),
            "has_character_name": hasattr(prompts, 'character_name'),
            "prompts_count": len(prompts.prompts)
        }
    except Exception as e:
        return {"error": str(e)}

# Background task
async def generate_images_task(story_id: str, prompts: List[str], remove_watermarks: bool):
    """Background task to generate images"""
    try:
        story = story_store[story_id]
        
        # Generate images
        images = image_gen.generate_sequence(prompts)
        
        # Remove watermarks if requested and watermark remover is available
        if remove_watermarks and watermark_remover:
            try:
                print(f"Removing watermarks for story {story_id}...")
                images = watermark_remover.remove_watermarks_batch(images)
            except Exception as e:
                print(f"Watermark removal failed: {e}, using original images")
        
        # Save images
        saved_paths = []
        output_dir = f"generated_images/{story_id}"
        os.makedirs(output_dir, exist_ok=True)
        
        for i, img in enumerate(images):
            path = f"{output_dir}/{i}.png"
            img.save(path, "PNG")
            saved_paths.append(path)
        
        # Update story
        story["images"] = saved_paths
        story["status"] = "completed"
        
        print(f"Story {story_id} completed successfully")
        
    except Exception as e:
        story_store[story_id]["status"] = "failed"
        story_store[story_id]["error"] = str(e)
        print(f"Failed to generate images for story {story_id}: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)