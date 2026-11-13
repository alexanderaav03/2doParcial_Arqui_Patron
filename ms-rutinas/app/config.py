from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql://user:password@localhost:5432/rutinas"
    # Sin valor por defecto: si falta, el servicio NO arranca (evita validar
    # tokens con un secreto conocido). Debe ser idéntico en los 3 servicios.
    JWT_SECRET: str
    MS_EJERCICIOS_URL: str = "http://localhost:8001"

    @field_validator("DATABASE_URL")
    @classmethod
    def _normalizar_esquema(cls, url: str) -> str:
        # SQLAlchemy 2.0 ya no acepta "postgres://" (formato que entregan
        # algunos proveedores, como Render o Heroku).
        if url.startswith("postgres://"):
            return "postgresql://" + url.removeprefix("postgres://")
        return url


settings = Settings()
