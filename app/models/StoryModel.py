import json
from datetime import datetime
from pathlib import Path


class StoryModel:
    def __init__(self, image_gen_client: object, outputs_dir):

        self.image_gen_client = image_gen_client
        self.OUTPUTS_DIR = outputs_dir

    # Background task
    async def generate_images_task(
        self,
        story_id: str,
        prompts: List[str],
        scenes: List[SceneOutput],
        remove_watermarks: bool,
        story_store: dict,
    ):
        """Background task to generate images and save to outputs directory"""
        try:
            story = story_store[story_id]
            output_dir = Path(story.get("output_dir", self.OUTPUTS_DIR / story_id))

            # Generate images
            images = self.image_gen_client.generate_sequence(prompts)

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
                output_dir = Path(story.get("output_dir", self.OUTPUTS_DIR / story_id))
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
