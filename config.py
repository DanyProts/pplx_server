import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()  # Load from .env if present


@dataclass(frozen=True)
class Settings:
    perplexity_api_key: str = os.getenv("PERPLEXITY_API_KEY", "")
    perplexity_api_url: str = os.getenv(
        "PERPLEXITY_API_URL", "https://api.perplexity.ai/chat/completions"
    )
    perplexity_search_url: str = os.getenv(
        "PERPLEXITY_SEARCH_URL", "https://api.perplexity.ai/search"
    )
    perplexity_model: str = os.getenv(
        "PERPLEXITY_MODEL", "llama-3.1-sonar-small-128k-online"
    )
    request_timeout_seconds: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "60"))
    client_ident_key: str = os.getenv("CLIENT_IDENT_KEY", "")


settings = Settings()
