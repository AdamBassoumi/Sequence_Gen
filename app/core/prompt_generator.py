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

        system_prompt = """You generate SHORT, CLEAR, ACTION-DRIVEN image prompts
optimized for Pollinations image models.

CRITICAL RULES:
- NOT a story
- Each prompt is an independent image
- ALWAYS produce a grammatically correct action sentence
- Use clear subject → verb → target structure
- Avoid tag lists

ACTION RULES:
- Action MUST include a target (e.g. 'chasing a cat')
- Prefer motion verbs (chasing, sprinting, fleeing, jumping)
- Add intensity or direction if possible

VARIATION:
- Change environment, style, lighting, or mood
- Keep the core action recognizable

CELEBRITY RULES:
- If user mentions a celebrity, include name ONLY in character_reference
- Never describe appearance or roles

Return VALID JSON EXACTLY in this structure:
{
  "story_title": "short title",
  "visual_style": "general aesthetic",
  "prompts": [
    {
      "primary_subject": "a dog",
      "action": "chasing a cat at full speed",
      "environment": "park with grass and trees",
      "style": "watercolor painting",
      "lighting": "bright sunlight",
      "mood": "playful",
      "character_reference": null
    }
  ]
}
"""

        user_prompt = f"""
Create up to {max_num_scenes} image variants for this concept:

"{user_prompt}"

Rules:
- Never output broken grammar
- Never omit the action target
- Each variant must stand alone
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
