from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    APP_NAME: str
    APP_VERSION: str

    IMG_GEN_PROVIDER: str

    GROQ_API_KEY: str

    HUGGING_FACE_KEY: str
    HUGGING_FACE_MODEL: str
    HUGGING_FACE_PROVIDER: str

    POLLINATIONS_TIMEOUT: int
    POLLINATIONS_RETRIES: int

    # DEVICE: str= "cuda"
    # TORCH_DTYPE: float  #bfloat16  # or float32

    OUTPUTS_DIR_PATH: str

    class Config:
        env_file = "../../.env"


def get_settings():
    return Settings()
