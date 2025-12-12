import os
import re
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from groq import Groq

class StoryPrompt(BaseModel):
    """Model for individual story section prompts"""
    description: str = Field(description="Overall scene description")
    scene_description: str = Field(description="Specific scene details")
    character_reference: Optional[str] = Field(
        default=None,
        description="Optional celebrity/character name ONLY if provided by user"
    )
    visual_context: str = Field(
        description="Visual mood, composition, and style elements",
        examples=["cinematic wide shot", "close-up portrait", "dynamic action scene"]
    )
    background_details: str = Field(description="Detailed background description")
    lighting_style: str = Field(description="Lighting description")
    consistency_keywords: List[str] = Field(
        default_factory=lambda: ["consistent visual style", "cohesive narrative"],
        description="Keywords to maintain consistency"
    )
    
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
            r' with (?:his|her) (?:signature|distinctive|characteristic) .+?(?:,|$)',
            r' featuring (?:his|her) .+? (?:appearance|look|style)',
            r' (?:wearing|sporting) (?:his|her) .+?(?:,|$)',
            r' (?:known for|recognizable by) .+?(?:,|$)',
            r' with (?:intense|piercing|striking) .+?(?:,|$)',
        ]
        
        for pattern in patterns_to_remove:
            prompt = re.sub(pattern, '', prompt, flags=re.IGNORECASE)
        
        # Remove double commas and clean up
        prompt = re.sub(r',\s*,', ',', prompt)
        prompt = re.sub(r',\s*$', '', prompt)
        
        return prompt.strip()

class GeneratedPrompts(BaseModel):
    """Model for the complete story prompts"""
    story_title: str = Field(description="Title of the story")
    visual_style: str = Field(
        description="Overall visual aesthetic",
        examples=["cinematic thriller", "epic fantasy", "sci-fi adventure"]
    )
    prompts: List[StoryPrompt]
    
    # Backward compatibility fields
    character_concept: Optional[str] = Field(
        default=None,
        description="Character concept (backward compatibility)"
    )
    character_name: Optional[str] = Field(
        default=None,
        description="Character name (backward compatibility)"
    )

class PromptGenerator:
    def __init__(self, api_key: str = None):
        """Initialize Groq client"""
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.1-8b-instant"
    
    def generate_story_prompts(self, user_prompt: str, max_num_scenes: int = 3) -> GeneratedPrompts:
        """Generate story prompts while preserving user's celebrity references"""
        
        system_prompt = """You are a professional visual storyteller for AI image generation.
        Your task is to create cinematic scene descriptions that work with AI image models.
        
        CRITICAL RULES FOR CELEBRITY HANDLING:
        1. If the user mentions a celebrity name, include it ONLY in the character_reference field
        2. DO NOT describe the celebrity's appearance, features, or characteristics
        3. DO NOT add details about how the celebrity looks
        4. Focus on SCENE composition, lighting, mood, and background
        5. Let the AI model handle the celebrity's visual representation
        
        Return your response as a valid JSON object with this exact structure:
        {
            "story_title": "Descriptive title without celebrity names",
            "visual_style": "Overall visual aesthetic (e.g., 'cinematic sci-fi')",
            "character_concept": "Brief character concept",
            "character_name": "Optional character name for reference",
            "prompts": [
                {
                    "description": "Scene overview (mood and action)",
                    "scene_description": "Specific moment or composition",
                    "character_reference": "ONLY if user mentioned a celebrity, otherwise null",
                    "visual_context": "Visual style and composition",
                    "background_details": "Detailed environment description",
                    "lighting_style": "Lighting description",
                    "consistency_keywords": ["keyword1", "keyword2"]
                }
            ]
        }"""
        
        user_prompt = f"""Create cinematic image prompts for: "{user_prompt}"
        
        Max Number of scenes: {max_num_scenes}

        You dont need to Generate The maximum number always
        
        Guidelines:
        1. Focus on scene composition, lighting, and atmosphere
        2. Describe the environment and mood in detail
        3. Include visual style keywords for consistency
        4. Progress the story through different scenes
        5. For characters: only reference names if provided, NO physical descriptions
        
        Each scene should advance the narrative while maintaining visual consistency."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Ensure backward compatibility fields exist
            if "character_concept" not in result:
                result["character_concept"] = result.get("visual_style", "")
            if "character_name" not in result:
                result["character_name"] = result.get("character_concept", result.get("visual_style", ""))
            
            return GeneratedPrompts(**result)
            
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
            (r'(?i)\b(his|her) (?:hair|eyes|face|smile|body|build)\b', 
             "Physical description of celebrity"),
            (r'(?i)\b(wearing|dressed in) (?:his|her) (?:signature|trademark)\b',
             "Signature look description"),
            (r'(?i)\b(as seen in|from the movie|portraying)\b',
             "Specific role reference"),
            (r'(?i)\b(younger|older|aged|youthful) (?:version|look)\b',
             "Age-specific description"),
        ]
        
        for pattern, warning in problematic_patterns:
            if re.search(pattern, prompt):
                warnings.append(warning)
        
        return len(warnings) == 0, warnings