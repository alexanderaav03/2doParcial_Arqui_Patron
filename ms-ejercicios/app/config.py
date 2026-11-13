from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql://user:password@localhost:5432/ejercicios"
    # Sin valor por defecto: si falta, el servicio NO arranca (evita firmar
    # tokens con un secreto conocido). Debe ser idéntico en los 3 servicios.
    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = 60
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_BUCKET: str = "ejercicios-media"
    MS_RUTINAS_URL: str = "http://localhost:8002"

    @field_validator("DATABASE_URL")
    @classmethod
    def _normalizar_esquema(cls, url: str) -> str:
        # SQLAlchemy 2.0 ya no acepta "postgres://" (formato que entregan
        # algunos proveedores, como Render o Heroku).
        if url.startswith("postgres://"):
            return "postgresql://" + url.removeprefix("postgres://")
        return url


settings = Settings()
