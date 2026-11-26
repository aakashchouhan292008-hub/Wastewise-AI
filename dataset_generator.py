"""Synthetic Indian college canteen dataset generator for WasteWise AI.

Generates at least 1,250 chronological daily food item records across 10 popular
Indian college canteen items. Clearly tagged as:
SYNTHETIC DEMONSTRATION DATA – NOT REAL CANTEEN RECORDS.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any
import numpy as np
import pandas as pd

from app.config import (
    DATA_DIR,
    DATASET_CSV_PATH,
    SYNTHETIC_DATA_LABEL,
)
from app.database.base import DatabaseRepository

WASTE_REASONS = [
    "Over-preparation",
    "Unexpected attendance drop",
    "Weather / rain disruption",
    "Competing campus event",
    "Late batch preparation",
]

SAMPLE_INVENTORY: list[dict[str, Any]] = [
    {"ingredient_name": "Basmati Rice", "category": "Grains", "available_quantity": 85.0, "unit": "kg", "minimum_stock_level": 40.0, "cost_per_unit": 92.0},
    {"ingredient_name": "Paneer (Fresh Cottage Cheese)", "category": "Dairy", "available_quantity": 9.5, "unit": "kg", "minimum_stock_level": 15.0, "cost_per_unit": 360.0},
    {"ingredient_name": "Refined Sunflower Oil", "category": "Oils & Fats", "available_quantity": 42.0, "unit": "liters", "minimum_stock_level": 20.0, "cost_per_unit": 145.0},
    {"ingredient_name": "Potatoes", "category": "Vegetables", "available_quantity": 65.0, "unit": "kg", "minimum_stock_level": 35.0, "cost_per_unit": 28.0},
    {"ingredient_name": "Onions", "category": "Vegetables", "available_quantity": 18.0, "unit": "kg", "minimum_stock_level": 25.0, "cost_per_unit": 34.0},
    {"ingredient_name": "Tomatoes", "category": "Vegetables", "available_quantity": 28.0, "unit": "kg", "minimum_stock_level": 20.0, "cost_per_unit": 40.0},
    {"ingredient_name": "Dosa & Idli Batter", "category": "Batters", "available_quantity": 14.0, "unit": "liters", "minimum_stock_level": 18.0, "cost_per_unit": 65.0},
    {"ingredient_name": "Whole Wheat Flour (Atta)", "category": "Grains", "available_quantity": 75.0, "unit": "kg", "minimum_stock_level": 30.0, "cost_per_unit": 42.0},
    {"ingredient_name": "Rajma (Red Kidney Beans)", "category": "Pulses", "available_quantity": 32.0, "unit": "kg", "minimum_stock_level": 15.0, "cost_per_unit": 125.0},
    {"ingredient_name": "Kabuli Chana (Chickpeas)", "category": "Pulses", "available_quantity": 26.0, "unit": "kg", "minimum_stock_level": 15.0, "cost_per_unit": 135.0},
    {"ingredient_name": "Poha (Flattened Rice)", "category": "Grains", "available_quantity": 22.0, "unit": "kg", "minimum_stock_level": 12.0, "cost_per_unit": 58.0},
    {"ingredient_name": "Sandwich Bread Loaves", "category": "Bakery", "available_quantity": 12.0, "unit": "packs", "minimum_stock_level": 20.0, "cost_per_unit": 48.0},
    {"ingredient_name": "Besan (Gram Flour)", "category": "Grains", "available_quantity": 24.0, "unit": "kg", "minimum_stock_level": 10.0, "cost_per_unit": 88.0},
    {"ingredient_name": "Mixed Indian Spices", "category": "Spices", "available_quantity": 11.0, "unit": "kg", "minimum_stock_level": 5.0, "cost_per_unit": 420.0},
]

# Weekday multiplier per food item (realistic Indian college canteen patterns)
ITEM_DAY_AFFINITY: dict[str, dict[str, float]] = {
    "Veg Biryani": {"Monday": 0.98, "Tuesday": 1.05, "Wednesday": 1.15, "Thursday": 1.08, "Friday": 1.18, "Saturday": 0.88, "Sunday": 0.72},
    "Masala Dosa": {"Monday": 1.04, "Tuesday": 1.10, "Wednesday": 1.02, "Thursday": 1.08, "Friday": 1.05, "Saturday": 1.12, "Sunday": 0.85},
    "Chole Bhature": {"Monday": 1.12, "Tuesday": 0.94, "Wednesday": 1.10, "Thursday": 0.96, "Friday": 1.14, "Saturday": 1.05, "Sunday": 0.78},
    "Sandwich": {"Monday": 1.05, "Tuesday": 1.08, "Wednesday": 1.04, "Thursday": 1.02, "Friday": 0.98, "Saturday": 0.90, "Sunday": 0.70},
    "Rajma Chawal": {"Monday": 1.02, "Tuesday": 1.12, "Wednesday": 1.00, "Thursday": 1.15, "Friday": 1.04, "Saturday": 0.85, "Sunday": 0.75},
    "Paneer Roll": {"Monday": 0.96, "Tuesday": 1.02, "Wednesday": 1.10, "Thursday": 1.08, "Friday": 1.15, "Saturday": 0.95, "Sunday": 0.75},
    "Samosa": {"Monday": 1.08, "Tuesday": 1.05, "Wednesday": 1.10, "Thursday": 1.08, "Friday": 1.12, "Saturday": 0.95, "Sunday": 0.65},
    "Poha": {"Monday": 1.14, "Tuesday": 1.08, "Wednesday": 1.02, "Thursday": 1.04, "Friday": 0.96, "Saturday": 0.92, "Sunday": 0.70},
    "Idli": {"Monday": 1.06, "Tuesday": 1.12, "Wednesday": 1.04, "Thursday": 1.00, "Friday": 0.98, "Saturday": 0.94, "Sunday": 0.78},
    "Fried Rice": {"Monday": 0.94, "Tuesday": 1.06, "Wednesday": 1.08, "Thursday": 1.14, "Friday": 1.12, "Saturday": 0.96, "Sunday": 0.74},
}


def generate_synthetic_dataset(
    food_items: list[dict[str, Any]],
    num_days: int = 125,
    seed: int = 42,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Generate realistic synthetic canteen sales and waste records.

    Returns (sales_rows, waste_rows).
    Total sales_rows = num_days * len(food_items) = 1,250 records by default.
    """
    rng = np.random.default_rng(seed)
    end_dt = date.today()
    start_dt = end_dt - timedelta(days=num_days - 1)

    sales_rows: list[dict[str, Any]] = []
    waste_rows: list[dict[str, Any]] = []

    # Track previous day's sold quantity per food item (lag-1 feature)
    prev_sales_map: dict[int, float] = {
        item["id"]: round(95.0 * item["base_popularity"]) for item in food_items
    }

    for day_offset in range(num_days):
        current_dt = start_dt + timedelta(days=day_offset)
        date_str = current_dt.isoformat()
        day_name = current_dt.strftime("%A")

        # Realistic campus calendar patterns
        is_sunday = day_name == "Sunday"
        is_saturday = day_name == "Saturday"
        is_holiday = 1 if (is_sunday or (rng.random() < 0.05 and not is_saturday)) else 0
        special_event = 1 if (not is_holiday and rng.random() < 0.11) else 0

        if is_holiday:
            base_att = rng.normal(210, 35)
        elif is_saturday:
            base_att = rng.normal(580, 70)
        else:
            # Mid-week peak (Tue-Thu) slightly higher on a college campus
            weekday_boost = 70 if day_name in ("Tuesday", "Wednesday", "Thursday") else 0
            base_att = rng.normal(1020 + weekday_boost, 95)

        if special_event:
            base_att += rng.normal(320, 65)

        expected_attendance = int(np.clip(round(base_att), 100, 1800))

        for item in food_items:
            item_id = item["id"]
            item_name = item["name"]
            popularity = float(item["base_popularity"])
            cost = float(item["default_cost_per_portion"])
            affinity = ITEM_DAY_AFFINITY.get(item_name, {}).get(day_name, 1.0)
            prev_sales = prev_sales_map[item_id]

            # Realistic demand equation driven by pre-preparation context + lag momentum
            att_share = expected_attendance * 0.105 * popularity * affinity
            event_lift = (28.0 * popularity) if special_event else 0.0
            holiday_damp = 0.55 if is_holiday else 1.0
            momentum = 0.22 * prev_sales
            noise = rng.normal(0, 6.5)

            raw_demand = (att_share * holiday_damp * 0.78) + momentum + event_lift + noise
            actual_demand = int(np.clip(round(raw_demand), 12, 420))

            # Traditional canteen preparation often slightly over-prepares on normal days
            # or misestimates holidays/events
            prep_bias = rng.normal(1.11, 0.06) if not special_event else rng.normal(1.05, 0.07)
            if is_holiday:
                prep_bias = rng.normal(1.18, 0.09)
            prepared_quantity = int(max(actual_demand, round(actual_demand * prep_bias)))
            # Occasional slight under-prep when demand spikes unexpectedly
            if rng.random() < 0.10:
                prepared_quantity = int(max(10, round(actual_demand * rng.uniform(0.90, 0.99))))

            sold_quantity = int(min(prepared_quantity, actual_demand))
            leftover_quantity = int(max(0, prepared_quantity - sold_quantity))

            sales_rows.append(
                {
                    "record_date": date_str,
                    "food_item_id": item_id,
                    "food_item": item_name,
                    "day_of_week": day_name,
                    "expected_attendance": expected_attendance,
                    "special_event": special_event,
                    "holiday": is_holiday,
                    "previous_sales": round(prev_sales, 1),
                    "prepared_quantity": prepared_quantity,
                    "sold_quantity": sold_quantity,
                    "leftover_quantity": leftover_quantity,
                    "cost_per_portion": cost,
                    "is_synthetic": 1,
                    "data_label": SYNTHETIC_DATA_LABEL,
                }
            )

            # Seed waste_records for the most recent 30 days where leftover > 0
            if day_offset >= (num_days - 30) and leftover_quantity > 0:
                waste_pct = round((leftover_quantity / prepared_quantity) * 100, 2)
                waste_cost = round(leftover_quantity * cost, 2)
                if is_holiday:
                    reason = "Unexpected attendance drop"
                elif special_event:
                    reason = "Competing campus event"
                else:
                    reason = str(rng.choice(WASTE_REASONS, p=[0.48, 0.22, 0.12, 0.10, 0.08]))

                waste_rows.append(
                    {
                        "waste_date": date_str,
                        "food_item_id": item_id,
                        "prepared_quantity": prepared_quantity,
                        "sold_quantity": sold_quantity,
                        "leftover_quantity": leftover_quantity,
                        "waste_percentage": waste_pct,
                        "reason": reason,
                        "cost_per_portion": cost,
                        "estimated_waste_cost": waste_cost,
                    }
                )

            prev_sales_map[item_id] = float(sold_quantity)

    return sales_rows, waste_rows


def export_synthetic_csv(sales_rows: list[dict[str, Any]]) -> None:
    """Save synthetic dataset to CSV for inspection and academic evaluation."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(sales_rows)
    columns = [
        "record_date",
        "food_item",
        "day_of_week",
        "expected_attendance",
        "special_event",
        "holiday",
        "previous_sales",
        "prepared_quantity",
        "sold_quantity",
        "leftover_quantity",
        "cost_per_portion",
        "data_label",
    ]
    df[columns].to_csv(DATASET_CSV_PATH, index=False)


def seed_initial_demo_data(db: DatabaseRepository) -> dict[str, int]:
    """Generate and reset synthetic demonstration data in the database."""
    db.seed_food_items()
    food_items = db.list_food_items()
    sales_rows, waste_rows = generate_synthetic_dataset(food_items=food_items, num_days=125, seed=42)
    export_synthetic_csv(sales_rows)
    db.reset_demo_data(sales_rows=sales_rows, waste_rows=waste_rows, inventory_rows=SAMPLE_INVENTORY)
    return {
        "sales_records": len(sales_rows),
        "waste_records": len(waste_rows),
        "inventory_items": len(SAMPLE_INVENTORY),
    }


if __name__ == "__main__":
    from app.database import db as default_db

    default_db.initialize_schema()
    summary = seed_initial_demo_data(default_db)
    print(f"Generated synthetic dataset ({SYNTHETIC_DATA_LABEL}): {summary}")
