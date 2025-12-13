import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.core.image_generator import ImageGenerator
from app.core.prompt_generator import GeneratedPrompts, PromptGenerator
from app.core.watermark_remover import WatermarkRemover


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


# Initialize app
app = FastAPI(
    title="Photo Sequence Generator API",
    description="Generate consistent photo sequences from text prompts",
    version="1.0.0",
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

# Create outputs directory
OUTPUTS_DIR = Path("outputs")
OUTPUTS_DIR.mkdir(exist_ok=True)


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global prompt_gen, image_gen, watermark_remover

    try:
        prompt_gen = PromptGenerator()
        image_gen = ImageGenerator()
        # watermark_remover = WatermarkRemover()  # Commented out temporarily
        print("All components initialized successfully")
        print(f"Outputs will be saved to: {OUTPUTS_DIR.absolute()}")
    except Exception as e:
        print(f"Warning: {str(e)}")


@app.post("/generate-story", response_model=StoryResponse)
async def generate_story(request: StoryRequest, background_tasks: BackgroundTasks):
    """Generate a story sequence from a prompt"""
    try:
        # Generate story ID
        story_id = str(uuid.uuid4())

        # Create output directory for this story
        story_output_dir = OUTPUTS_DIR / story_id
        story_output_dir.mkdir(exist_ok=True)

        # Generate prompts
        generated_prompts = prompt_gen.generate_story_prompts(
            request.prompt, max_num_scenes=request.max_num_scenes
        )

        # Save prompts to JSON file
        prompts_file = story_output_dir / "prompts.json"
        with open(prompts_file, "w") as f:
            json.dump(
                {
                    "story_id": story_id,
                    "user_prompt": request.prompt,
                    "story_title": generated_prompts.story_title,
                    "visual_style": generated_prompts.visual_style,
                    "character_concept": generated_prompts.character_concept,
                    "character_name": generated_prompts.character_name,
                    "generated_prompts": [p.prompt for p in generated_prompts.prompts],
                    "created_at": datetime.now().isoformat(),
                },
                f,
                indent=2,
            )

        # Extract the prompt strings
        image_prompts = [p.prompt for p in generated_prompts.prompts]

        # Create initial scene outputs
        scenes = []
        for i, prompt_text in enumerate(image_prompts):
            scenes.append(
                SceneOutput(
                    scene_number=i + 1,
                    prompt=prompt_text,
                    image_url=f"/images/{story_id}/{i}.png",
                    image_path=str(story_output_dir / f"scene_{i+1}.png"),
                )
            )

        # Store story info
        story_data = {
            "story_id": story_id,
            "status": "pending",
            "story_title": generated_prompts.story_title,
            "character_concept": generated_prompts.character_concept,
            "visual_style": generated_prompts.visual_style,
            "character_name": generated_prompts.character_name,
            "prompts": image_prompts,
            "scenes": [scene.dict() for scene in scenes],
            "images": [],
            "output_dir": str(story_output_dir),
            "created_at": datetime.now().isoformat(),
        }
        story_store[story_id] = story_data

        # Add background task for image generation
        background_tasks.add_task(
            generate_images_task,
            story_id,
            image_prompts,
            scenes,
            request.remove_watermarks,
        )

        return StoryResponse(
            story_id=story_id,
            status="processing",
            story_title=generated_prompts.story_title,
            character_concept=generated_prompts.character_concept,
            visual_style=generated_prompts.visual_style,
            character_name=generated_prompts.character_name,
            scenes=scenes,
            output_dir=str(story_output_dir),
            created_at=story_data["created_at"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/story/{story_id}", response_model=StoryResponse)
async def get_story(story_id: str):
    """Get story status and results"""
    if story_id not in story_store:
        raise HTTPException(status_code=404, detail="Story not found")

    story = story_store[story_id]

    # Reconstruct scenes with updated image paths
    scenes = []
    for i, scene_data in enumerate(story.get("scenes", [])):
        image_url = None
        image_path = None

        if story.get("images") and i < len(story["images"]):
            image_url = f"/images/{story_id}/{i}.png"
            image_path = story["images"][i]

        scenes.append(
            SceneOutput(
                scene_number=scene_data.get("scene_number", i + 1),
                prompt=scene_data.get(
                    "prompt",
                    story["prompts"][i] if i < len(story.get("prompts", [])) else "",
                ),
                image_url=image_url,
                image_path=image_path,
            )
        )

    return StoryResponse(
        story_id=story_id,
        status=story["status"],
        story_title=story["story_title"],
        character_concept=story.get("character_concept"),
        visual_style=story.get("visual_style", "cinematic"),
        character_name=story.get("character_name"),
        scenes=scenes,
        output_dir=story.get("output_dir"),
        created_at=story["created_at"],
    )


@app.get("/images/{story_id}/{image_index}")
async def get_image(story_id: str, image_index: int):
    """Get generated image"""
    if story_id not in story_store:
        raise HTTPException(status_code=404, detail="Story not found")

    story = story_store[story_id]

    if not story.get("images") or image_index >= len(story["images"]):
        raise HTTPException(status_code=404, detail="Image not found")

    image_path = story["images"][image_index]

    if os.path.exists(image_path):
        return FileResponse(image_path, media_type="image/png")
    else:
        raise HTTPException(status_code=404, detail="Image file not found")


@app.get("/story/{story_id}/download")
async def download_story(story_id: str):
    """Download entire story as a ZIP file"""
    if story_id not in story_store:
        raise HTTPException(status_code=404, detail="Story not found")

    story = story_store[story_id]
    output_dir = story.get("output_dir")

    if not output_dir or not os.path.exists(output_dir):
        raise HTTPException(status_code=404, detail="Story output directory not found")

    # Create ZIP file
    import zipfile

    zip_path = f"outputs/{story_id}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add all files in the story directory
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=output_dir)
                zipf.write(file_path, arcname=f"{story_id}/{arcname}")

    return FileResponse(
        zip_path, media_type="application/zip", filename=f"{story_id}.zip"
    )


@app.get("/story/{story_id}/files")
async def list_story_files(story_id: str):
    """List all files in the story output directory"""
    if story_id not in story_store:
        raise HTTPException(status_code=404, detail="Story not found")

    story = story_store[story_id]
    output_dir = story.get("output_dir")

    if not output_dir or not os.path.exists(output_dir):
        raise HTTPException(status_code=404, detail="Story output directory not found")

    files = []
    for file in os.listdir(output_dir):
        file_path = os.path.join(output_dir, file)
        if os.path.isfile(file_path):
            files.append(
                {
                    "name": file,
                    "path": file_path,
                    "size": os.path.getsize(file_path),
                    "type": os.path.splitext(file)[1],
                }
            )

    return {"story_id": story_id, "output_dir": output_dir, "files": files}


@app.get("/stories")
async def list_stories():
    """List all generated stories"""
    stories = []
    for story_id, story_data in story_store.items():
        stories.append(
            {
                "story_id": story_id,
                "title": story_data.get("story_title", "Untitled"),
                "status": story_data.get("status", "unknown"),
                "created_at": story_data.get("created_at"),
                "scenes_count": len(story_data.get("prompts", [])),
                "output_dir": story_data.get("output_dir"),
            }
        )

    # Also check for stories in outputs directory that might not be in memory
    for story_dir in OUTPUTS_DIR.iterdir():
        if story_dir.is_dir() and story_dir.name not in story_store:
            prompts_file = story_dir / "prompts.json"
            if prompts_file.exists():
                try:
                    with open(prompts_file, "r") as f:
                        prompts_data = json.load(f)

                    stories.append(
                        {
                            "story_id": story_dir.name,
                            "title": prompts_data.get("story_title", "Untitled"),
                            "status": "archived",  # Not in active memory
                            "created_at": prompts_data.get("created_at"),
                            "scenes_count": len(
                                prompts_data.get("generated_prompts", [])
                            ),
                            "output_dir": str(story_dir),
                        }
                    )
                except:
                    pass

    return {"stories": stories}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "outputs_dir": str(OUTPUTS_DIR.absolute()),
        "stories_count": len(story_store),
    }


# Background task
async def generate_images_task(
    story_id: str,
    prompts: List[str],
    scenes: List[SceneOutput],
    remove_watermarks: bool,
):
    """Background task to generate images and save to outputs directory"""
    try:
        story = story_store[story_id]
        output_dir = Path(story.get("output_dir", OUTPUTS_DIR / story_id))

        # Generate images
        images = image_gen.generate_sequence(prompts)

        # Remove watermarks if requested
        if remove_watermarks and watermark_remover:
            try:
                print(f"Removing watermarks for story {story_id}...")
                images = watermark_remover.remove_watermarks_batch(images)
            except Exception as e:
                print(f"Watermark removal failed: {e}, using original images")

        # Save images to output directory
        saved_paths = []
        for i, (img, scene) in enumerate(zip(images, scenes)):
            # Save as scene_1.png, scene_2.png, etc.
            filename = f"scene_{i+1}.png"
            image_path = output_dir / filename
            img.save(image_path, "PNG")
            saved_paths.append(str(image_path))

            # Update scene with actual image path
            scene.image_path = str(image_path)

            # Update story scenes data
            if i < len(story["scenes"]):
                story["scenes"][i]["image_path"] = str(image_path)

        # Update prompts.json with image paths
        prompts_file = output_dir / "prompts.json"
        if prompts_file.exists():
            with open(prompts_file, "r") as f:
                prompts_data = json.load(f)

            prompts_data["image_paths"] = saved_paths
            prompts_data["completed_at"] = datetime.now().isoformat()
            prompts_data["status"] = "completed"

            with open(prompts_file, "w") as f:
                json.dump(prompts_data, f, indent=2)

        # Update story in memory
        story["images"] = saved_paths
        story["status"] = "completed"
        story["completed_at"] = datetime.now().isoformat()

        print(f"✅ Story {story_id} completed successfully")
        print(f"📁 Output saved to: {output_dir}")

    except Exception as e:
        story_store[story_id]["status"] = "failed"
        story_store[story_id]["error"] = str(e)

        # Save error info to prompts.json
        try:
            output_dir = Path(story.get("output_dir", OUTPUTS_DIR / story_id))
            prompts_file = output_dir / "prompts.json"
            if prompts_file.exists():
                with open(prompts_file, "r") as f:
                    prompts_data = json.load(f)

                prompts_data["status"] = "failed"
                prompts_data["error"] = str(e)

                with open(prompts_file, "w") as f:
                    json.dump(prompts_data, f, indent=2)
        except:
            pass

        print(f"❌ Failed to generate images for story {story_id}: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
