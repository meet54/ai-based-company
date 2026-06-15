from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", env_file_encoding="utf-8", extra="ignore")

    # Provider: groq (free), gemini (free), openai (paid), demo
    llm_provider: str = "groq"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    ceo_name: str = "CEO"
    ceo_email: str = "ceo@aicompany.com"
    ceo_login_email: str = "smeet4454@gmail.com"
    ceo_login_password: str = "1234"
    auth_secret: str = "ai-nexus-ceo-session-secret"
    company_name: str = "AI Nexus Solutions"
    host: str = "0.0.0.0"
    port: int = 8765
    demo_mode: bool = True
    ssl_verify: bool = True
    fallback_on_rate_limit: bool = True
    database_url: str = f"sqlite+aiosqlite:///{ROOT / 'ai_company.db'}"

    def _key_ok(self, key: str) -> bool:
        k = key.strip()
        return bool(k) and k not in ("sk-your-key-here", "your-key-here")

    @property
    def active_provider(self) -> str:
        if self.demo_mode:
            return "demo"
        provider = self.llm_provider.strip().lower()
        if provider == "auto":
            if self._key_ok(self.groq_api_key):
                return "groq"
            if self._key_ok(self.gemini_api_key):
                return "gemini"
            if self._key_ok(self.openai_api_key):
                return "openai"
            return "demo"
        return provider

    @property
    def has_api_key(self) -> bool:
        p = self.active_provider
        if p == "groq":
            return self._key_ok(self.groq_api_key)
        if p == "gemini":
            return self._key_ok(self.gemini_api_key)
        if p == "openai":
            return self._key_ok(self.openai_api_key)
        return False

    @property
    def use_demo(self) -> bool:
        if self.active_provider == "demo":
            return True
        return not self.has_api_key

    @property
    def ai_mode(self) -> str:
        if self.use_demo:
            if not self.demo_mode and self.active_provider != "demo":
                return "missing_key"
            return "demo"
        return "real"

    @property
    def active_model(self) -> str:
        p = self.active_provider
        if p == "groq":
            return self.groq_model
        if p == "gemini":
            return self.gemini_model
        if p == "openai":
            return self.openai_model
        return "demo"


settings = Settings()
