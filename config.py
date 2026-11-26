"""Configuration management for WasteWise AI backend."""

from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR.parent / ".env")
load_dotenv(BASE_DIR / ".env")

APP_NAME: str = os.getenv("APP_NAME", "WasteWise AI")
APP_ENV: str = os.getenv("APP_ENV", "development")
DATABASE_BACKEND: str = os.getenv("DATABASE_BACKEND", "sqlite")

DATA_DIR: Path = BASE_DIR / "data"
ARTIFACTS_DIR: Path = BASE_DIR / "artifacts"

SQLITE_DB_PATH: Path = BASE_DIR / os.getenv("SQLITE_DB_PATH", "data/wastewise.db")
MODEL_ARTIFACT_PATH: Path = BASE_DIR / os.getenv("MODEL_ARTIFACT_PATH", "artifacts/demand_rf_model.joblib")
MODEL_METADATA_PATH: Path = BASE_DIR / os.getenv("MODEL_METADATA_PATH", "artifacts/model_metadata.json")
DATASET_CSV_PATH: Path = BASE_DIR / os.getenv("DATASET_CSV_PATH", "data/synthetic_canteen_dataset.csv")

DEFAULT_SAFETY_BUFFER_PCT: float = float(os.getenv("DEFAULT_SAFETY_BUFFER_PCT", "10.0"))
MIN_TRAINING_RECORDS: int = int(os.getenv("MIN_TRAINING_RECORDS", "50"))
MIN_NEW_RECORDS_FOR_RETRAIN: int = int(os.getenv("MIN_NEW_RECORDS_FOR_RETRAIN", "5"))

CORS_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173",
    ).split(",")
    if origin.strip()
]

SYNTHETIC_DATA_LABEL: str = "SYNTHETIC DEMONSTRATION DATA – NOT REAL CANTEEN RECORDS."

FOOD_ITEMS_CATALOG: list[dict] = [
    {"name": "Veg Biryani", "category": "Main Course", "default_cost_per_portion": 65.0, "base_popularity": 1.15},
    {"name": "Masala Dosa", "category": "South Indian", "default_cost_per_portion": 45.0, "base_popularity": 1.10},
    {"name": "Chole Bhature", "category": "North Indian", "default_cost_per_portion": 55.0, "base_popularity": 1.05},
    {"name": "Sandwich", "category": "Snacks", "default_cost_per_portion": 35.0, "base_popularity": 0.95},
    {"name": "Rajma Chawal", "category": "Main Course", "default_cost_per_portion": 50.0, "base_popularity": 1.00},
    {"name": "Paneer Roll", "category": "Rolls & Wraps", "default_cost_per_portion": 60.0, "base_popularity": 0.98},
    {"name": "Samosa", "category": "Snacks", "default_cost_per_portion": 15.0, "base_popularity": 1.35},
    {"name": "Poha", "category": "Breakfast", "default_cost_per_portion": 25.0, "base_popularity": 0.85},
    {"name": "Idli", "category": "South Indian", "default_cost_per_portion": 30.0, "base_popularity": 0.88},
    {"name": "Fried Rice", "category": "Chinese", "default_cost_per_portion": 55.0, "base_popularity": 0.92},
]

DAYS_OF_WEEK: list[str] = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
