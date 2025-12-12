import requests
import json
import time

class PhotoSequenceClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def generate_story(self, prompt: str, num_scenes: int = 3):
        """Generate a story sequence"""
        response = requests.post(
            f"{self.base_url}/generate-story",
            json={
                "prompt": prompt,
                "num_scenes": num_scenes,
                "remove_watermarks": True
            }
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
        if not story_info or not story_info.get("image_urls"):
            print("No images available")
            return
        
        # Download each image
        for i, url in enumerate(story_info["image_urls"]):
            response = requests.get(f"{self.base_url}{url}")
            
            if response.status_code == 200:
                filename = f"{output_dir}/{story_id}_{i}.png"
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f"Downloaded: {filename}")
            else:
                print(f"Failed to download image {i}")

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
    print(f"Character: {result['character_name']}")
    
    # Show prompts
    print("\nGenerated Prompts:")
    for i, p in enumerate(result["prompts"], 1):
        print(f"\nScene {i}:")
        print(p[:200] + "..." if len(p) > 200 else p)
    
    # Wait for completion
    print(f"\nWaiting for image generation...")
    final_result = client.wait_for_completion(story_id)
    
    if final_result and final_result["status"] == "completed":
        print("\n✅ Generation complete!")
        
        # Download images
        download = input("\nDownload images? (y/n): ").lower().strip()
        if download == 'y':
            client.download_images(story_id)
            print(f"\nImages saved to 'downloads/' directory")
        
        # Show image URLs
        print(f"\nImage URLs:")
        for i, url in enumerate(final_result["image_urls"], 1):
            print(f"Scene {i}: {client.base_url}{url}")
    
    else:
        print("\n❌ Generation failed or timed out")

if __name__ == "__main__":
    main()