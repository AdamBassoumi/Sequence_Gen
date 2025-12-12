import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Create directories
    os.makedirs("generated_images", exist_ok=True)
    
    # Run the app
    uvicorn.run(
        "app.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )