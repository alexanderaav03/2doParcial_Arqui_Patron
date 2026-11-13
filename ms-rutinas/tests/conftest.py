"""Configuración mínima para correr los tests sin .env ni Postgres.

pytest carga este archivo ANTES de importar los tests, así que estas
variables ya existen cuando app.config crea Settings(). JWT_SECRET no tiene
valor por defecto en app/config.py, por eso hay que darlo acá. Los valores
solo se usan si no vienen ya definidos en el entorno.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "solo-para-tests")
