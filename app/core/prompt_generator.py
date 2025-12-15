import json
import os
import re
from typing import List, Optional

from groq import Groq
from pydantic import BaseModel, Field


class StoryPrompt(BaseModel):
    """Model for individual story section prompts"""

    description: str = Field(description="Overall scene description")
    scene_description: str = Field(description="Specific scene details")
    character_reference: Optional[str] = Field(
        default=None,
        description="Optional celebrity/character name ONLY if provided by user",
    )
    visual_context: str = Field(
        description="Visual mood, composition, and style elements",
        examples=["cinematic wide shot", "close-up portrait", "dynamic action scene"],
    )
    background_details: str = Field(description="Detailed background description")
    lighting_style: str = Field(description="Lighting description")
    consistency_keywords: List[str] = Field(
        default_factory=lambda: ["consistent visual style", "cohesive narrative"],
        description="Keywords to maintain consistency",
    )
    negative_prompt: str = Field(description="Negative prompts, things to avoid")

    # Add prompt property for API compatibility
    @property
    def prompt(self) -> str:
        """Generate a complete prompt string for image generation"""
        components = []

        # Add character reference if present
        if self.character_reference:
            components.append(f"{self.character_reference}")

        # Add scene description
        components.append(self.description)

        # Add visual context
        components.append(self.visual_context)

        # Add environment and lighting
        components.append(f"in {self.background_details}")
        components.append(f"with {self.lighting_style}")

        # Add style and quality keywords
        components.append("photorealistic, cinematic, 8k, high detail")

        # Add consistency keywords
        if self.consistency_keywords:
            components.append(", ".join(self.consistency_keywords))

        # Join all components
        prompt = ", ".join(components)

        # Clean up any accidental descriptive phrases about celebrities
        prompt = self._clean_celebrity_descriptions(prompt)

        return prompt

    def _clean_celebrity_descriptions(self, prompt: str) -> str:
        """Remove any accidental celebrity physical descriptions"""
        patterns_to_remove = [
            r" with (?:his|her) (?:signature|distinctive|characteristic) .+?(?:,|$)",
            r" featuring (?:his|her) .+? (?:appearance|look|style)",
            r" (?:wearing|sporting) (?:his|her) .+?(?:,|$)",
            r" (?:known for|recognizable by) .+?(?:,|$)",
            r" with (?:intense|piercing|striking) .+?(?:,|$)",
        ]

        for pattern in patterns_to_remove:
            prompt = re.sub(pattern, "", prompt, flags=re.IGNORECASE)

        # Remove double commas and clean up
        prompt = re.sub(r",\s*,", ",", prompt)
        prompt = re.sub(r",\s*$", "", prompt)

        return prompt.strip()


class GeneratedPrompts(BaseModel):
    """Model for the complete story prompts"""

    story_title: str = Field(description="Title of the story")
    visual_style: str = Field(
        description="Overall visual aesthetic",
        examples=["cinematic thriller", "epic fantasy", "sci-fi adventure"],
    )
    prompts: List[StoryPrompt]

    # Backward compatibility fields
    character_concept: Optional[str] = Field(
        default=None, description="Character concept (backward compatibility)"
    )
    character_name: Optional[str] = Field(
        default=None, description="Character name (backward compatibility)"
    )


class PromptGenerator:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Groq client"""
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")

        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.1-8b-instant"

    def generate_story_prompts(
        self, user_prompt: str, max_num_scenes: int = 3
    ) -> GeneratedPrompts:
        """Generate story prompts while preserving user's celebrity references"""

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

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content

            # Handle potential None content
            if not content:
                raise ValueError("Empty response from Groq API")

            result = json.loads(content)

            # Ensure backward compatibility fields exist
            if "character_concept" not in result:
                result["character_concept"] = result.get("visual_style", "")
            if "character_name" not in result:
                result["character_name"] = result.get(
                    "character_concept", result.get("visual_style", "")
                )

            return GeneratedPrompts(**result)

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from API: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to generate prompts: {str(e)}")

    def create_image_prompt(self, story_prompt: StoryPrompt) -> str:
        """Create AI-friendly image prompt that preserves celebrity references safely"""
        # Just use the prompt property from StoryPrompt
        return story_prompt.prompt

    def validate_prompt_safety(self, prompt: str) -> tuple[bool, List[str]]:
        """Validate that prompt doesn't contain problematic celebrity descriptions"""
        warnings = []

        problematic_patterns = [
            (
                r"(?i)\b(his|her) (?:hair|eyes|face|smile|body|build)\b",
                "Physical description of celebrity",
            ),
            (
                r"(?i)\b(wearing|dressed in) (?:his|her) (?:signature|trademark)\b",
                "Signature look description",
            ),
            (
                r"(?i)\b(as seen in|from the movie|portraying)\b",
                "Specific role reference",
            ),
            (
                r"(?i)\b(younger|older|aged|youthful) (?:version|look)\b",
                "Age-specific description",
            ),
        ]

        for pattern, warning in problematic_patterns:
            if re.search(pattern, prompt):
                warnings.append(warning)

        return len(warnings) == 0, warnings
