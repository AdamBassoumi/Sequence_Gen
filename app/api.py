from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.ImageGeneratorProvider import ImageGeneratorProvider
from app.core.prompt_generator import PromptGenerator
from app.helpers.config import get_settings
from app.routes import base, story_gen

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


# Storage for generated stories
story_store = {}


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""

    settings = get_settings()
    try:
        app.prompt_gen = PromptGenerator()

        app.image_gen = ImageGeneratorProvider(settings).create()

        # watermark_remover = WatermarkRemover()  # Commented out temporarily
        print("All components initialized successfully")
    except Exception as e:
        print(f"Warning: {str(e)}")


app.include_router(base.base_router)
app.include_router(story_gen.story_router)
