import json
import os
import re
from typing import List, Optional

from groq import Groq
from pydantic import BaseModel, Field, validator


# =========================================================
# PROMPT MODEL (ACTION-FIRST, GRAMMAR-SAFE)
# =========================================================
class StoryPrompt(BaseModel):
    """
    Single image variant prompt.
    Optimized for Pollinations / SD-like models.
    """

    primary_subject: str = Field(description="Main actor (e.g. 'a golden retriever')")
    action: str = Field(
        description="Clear verb phrase including target (e.g. 'chasing a black cat')"
    )
    environment: str = Field(
        description="Setting with minimal detail (e.g. 'green park with trees')"
    )
    style: str = Field(description="Art or render style (e.g. 'watercolor painting')")
    lighting: str = Field(
        description="Lighting or time of day (e.g. 'bright sunlight')"
    )
    mood: Optional[str] = Field(
        default=None,
        description="Optional mood (e.g. playful, tense, dramatic)",
    )
    character_reference: Optional[str] = Field(
        default=None,
        description="Celebrity name ONLY if user explicitly mentioned it",
    )
    negative_prompt: str = Field(description="Negative prompts, things to avoid")

    @validator("action")
    def action_must_contain_verb(cls, v):
        if len(v.split()) < 2:
            raise ValueError("Action must be a verb phrase, not a single word")
        return v

    @property
    def prompt(self) -> str:
        parts = []

        if self.character_reference:
            parts.append(self.character_reference)

        # Core sentence — this is CRITICAL
        parts.append(f"{self.primary_subject} {self.action}")

        parts.append(self.environment)

        if self.mood:
            parts.append(self.mood)

        parts.append(self.style)
        parts.append(self.lighting)

        # Motion + quality bias (cheap but effective)
        parts.append("dynamic action, motion blur")
        parts.append("high quality, detailed")

        prompt = ", ".join(parts)
        return self._sanitize(prompt)

    def _sanitize(self, prompt: str) -> str:
        # Remove accidental physical descriptions
        prompt = re.sub(r"(?i)\b(his|her)\b.*?(?:,|$)", "", prompt)
        prompt = re.sub(r",\s*,", ",", prompt)
        return prompt.strip()


# =========================================================
# OUTPUT CONTAINER
# =========================================================
class GeneratedPrompts(BaseModel):
    story_title: str
    visual_style: str
    prompts: List[StoryPrompt]

    # Backward compatibility
    character_concept: Optional[str] = None
    character_name: Optional[str] = None


# =========================================================
# PROMPT GENERATOR
# =========================================================
class PromptGenerator:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")

        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.1-8b-instant"

    def generate_story_prompts(
        self, user_prompt: str, max_num_scenes: int = 3
    ) -> GeneratedPrompts:
        """
        Generate independent IMAGE VARIANTS with strong action clarity.
        """

        system_prompt = """
        You are a CREATIVE DIRECTOR and professional visual storyteller for AI image generation.

        The user will provide ONLY a GENERAL IDEA.
        Your responsibility is to:
        - Interpret the idea creatively
        - Invent a compelling narrative
        - Design a coherent multi-scene visual story
        - Decide the number of scenes (up to the maximum provided)
        - Ensure strong cinematic progression

        You are NOT a simple prompt rewriter.
        You are responsible for STORY, VISUALS, and CONSISTENCY.

        GENERAL RESPONSIBILITIES:
        - Create a creative scenario inspired by the user idea
        - Identify all primary characters involved (explicit or implied)
        - Invent meaningful interactions and emotional progression
        - Design scenes that feel connected as a story

        CRITICAL RULES FOR CELEBRITY HANDLING:
        1. If the user mentions a celebrity name, include it ONLY in the character_reference field
        2. DO NOT describe the celebrity's appearance, features, or characteristics
        3. DO NOT add details about how the celebrity looks
        4. Focus on SCENE composition, lighting, mood, and background
        5. Let the AI model handle the celebrity's visual representation

        CRITICAL MULTI-CHARACTER CONSISTENCY RULES (MANDATORY):
        1. Identify ALL primary characters from the user idea.
        2. For EACH primary character, create a FIXED CHARACTER CONTRACT:
        - A concise visual identity description
        - Reused VERBATIM across all scenes
        3. Character contracts MUST remain consistent across scenes.
        4. Every scene MUST include ALL primary characters.
        5. Every scene MUST explicitly state that ALL characters are visible in the same scene.
        6. Every scene MUST describe INTERACTIONS between the characters.
        7. Do NOT introduce new characters unless required by the user idea.
        8. Do NOT remove characters between scenes.
        9. Do NOT allow single-character scenes unless the user explicitly requests it.

        NEGATIVE PROMPT RULES:
        For each scene, generate a negative prompt that:
        - Prevents missing characters
        - Prevents single-subject images
        - Prevents cropped or out-of-frame characters
        - Prevents background-only images
        - Prevents low-quality or incoherent images

        NEGATIVE PROMPTS MUST BE DYNAMIC and ADAPTED to the scene and characters.

        Return your response as a VALID JSON object with this EXACT structure:

        {
        "story_title": "Creative title that reflects the invented scenario",
        "visual_style": "Overall visual aesthetic (e.g., cinematic manga, fantasy realism)",
        "character_concept": "Summary of the characters and invented story",
        "character_name": "Optional character name for reference",
        "prompts": [
            {
            "description": "Narrative purpose of the scene",
            "scene_description": "Specific moment in the invented story",
            "character_reference": "ONLY if a celebrity is mentioned, otherwise null",
            "visual_context": "Full image prompt including all character contracts verbatim",
            "background_details": "Detailed environment description",
            "lighting_style": "Lighting and atmosphere description",
            "consistency_keywords": ["keyword1", "keyword2"],
            "negative_prompt": "Scene-specific negative prompt"
            }
        ]
        }
        """

        user_prompt = f"""
        User idea:
        "{user_prompt}"

        Maximum number of scenes: {max_num_scenes}

        Create a creative visual story inspired by this idea.
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.6,
            max_tokens=1200,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from Groq API")

        result = json.loads(content)

        # Backward compatibility
        result.setdefault("character_concept", result.get("story_title", ""))
        result.setdefault("character_name", None)

        return GeneratedPrompts(**result)

    def create_image_prompt(self, story_prompt: StoryPrompt) -> str:
        return story_prompt.prompt
