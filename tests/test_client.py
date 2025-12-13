import json
import time

import requests


class PhotoSequenceClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def generate_story(self, prompt: str, num_scenes: int = 3):
        """Generate a story sequence"""
        response = requests.post(
            f"{self.base_url}/generate-story",
            json={
                "prompt": prompt,
                "max_num_scenes": num_scenes,
                "remove_watermarks": False,
            },
        )

        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            return None

        return response.json()

    def check_status(self, story_id: str):
        """Check story generation status"""
        response = requests.get(f"{self.base_url}/story/{story_id}")

        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            return None

        return response.json()

    def wait_for_completion(self, story_id: str, interval: int = 5, timeout: int = 300):
        """Wait for story generation to complete"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = self.check_status(story_id)

            if result is None:
                return None

            status = result.get("status")
            print(f"Status: {status}")

            if status == "completed":
                return result
            elif status == "failed":
                print(f"Generation failed: {result.get('error', 'Unknown error')}")
                return None

            time.sleep(interval)

        print("Timeout waiting for completion")
        return None

    def download_images(self, story_id: str, output_dir: str = "downloads"):
        """Download generated images"""
        import os

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Get story info
        story_info = self.check_status(story_id)
        if not story_info or not story_info.get("scenes"):
            print("No scenes available")
            return

        # Download each image from scenes
        for i, scene in enumerate(story_info["scenes"]):
            if scene.get("image_url"):
                image_url = f"{self.base_url}{scene['image_url']}"
                response = requests.get(image_url)

                if response.status_code == 200:
                    filename = f"{output_dir}/{story_id}_scene_{i+1}.png"
                    with open(filename, "wb") as f:
                        f.write(response.content)
                    print(f"Downloaded: {filename}")
                else:
                    print(f"Failed to download scene {i+1} image")


def main():
    """Test the API with a user prompt"""
    client = PhotoSequenceClient()

    # Get user input
    prompt = input("Enter your story prompt: ").strip()

    if not prompt:
        prompt = "A space explorer discovering ancient alien ruins on a distant planet"
        print(f"Using default prompt: {prompt}")

    # Generate story
    print(f"\nGenerating story for: {prompt}")
    result = client.generate_story(prompt, num_scenes=3)

    if not result:
        print("Failed to start generation")
        return

    story_id = result["story_id"]
    print(f"Story ID: {story_id}")
    print(f"Title: {result['story_title']}")
    print(f"Visual Style: {result.get('visual_style', 'N/A')}")
    print(f"Character Concept: {result.get('character_concept', 'N/A')}")

    # Show scenes instead of prompts
    print("\nGenerated Scenes:")
    if "scenes" in result:
        for i, scene in enumerate(result["scenes"], 1):
            print(f"\nScene {i}:")
            print(f"  Description: {scene.get('scene_description', 'N/A')}")
            prompt_text = scene.get("prompt", "")
            print(
                f"  Prompt: {prompt_text[:150]}..."
                if len(prompt_text) > 150
                else f"  Prompt: {prompt_text}"
            )
    else:
        print("No scenes generated")

    # Wait for completion
    print(f"\nWaiting for image generation...")
    final_result = client.wait_for_completion(story_id)

    if final_result and final_result["status"] == "completed":
        print("\n✅ Generation complete!")

        # Show completed scenes
        print("\nCompleted Scenes:")
        for i, scene in enumerate(final_result["scenes"], 1):
            print(f"\nScene {i}:")
            print(f"  Prompt: {scene.get('prompt', '')[:100]}...")
            if scene.get("image_url"):
                print(f"  Image: {client.base_url}{scene['image_url']}")

        # Download images
        download = input("\nDownload images? (y/n): ").lower().strip()
        if download == "y":
            client.download_images(story_id)
            print(f"\nImages saved to 'downloads/' directory")

        # Optional: Show complete story with images
        view_complete = (
            input("\nView complete story with embedded images? (y/n): ").lower().strip()
        )
        if view_complete == "y":
            complete_response = requests.get(
                f"{client.base_url}/story/{story_id}/complete"
            )
            if complete_response.status_code == 200:
                complete_data = complete_response.json()
                print(
                    f"\nComplete story with {len(complete_data.get('scenes', []))} scenes"
                )

    else:
        print("\n❌ Generation failed or timed out")


if __name__ == "__main__":
    main()
