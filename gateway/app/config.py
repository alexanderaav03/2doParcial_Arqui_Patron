from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Sin valor por defecto: si falta, el servicio NO arranca (evita correr
    # con un secreto conocido). Debe ser idéntico en los 3 servicios.
    JWT_SECRET: str
    MS_EJERCICIOS_URL: str = "http://localhost:8001"
    MS_RUTINAS_URL: str = "http://localhost:8002"


settings = Settings()
