"""Idempotent demo catalog seed. Replace this data with the IS catalog import later."""

from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine
from .models import Product


PRODUCTS = [
    ("CEM-001", "Portland Cement 25 kg", "cement", "bag", 8.95, 120, {"type": "portland", "strength": "42.5", "weight_kg": 25}),
    ("CEM-002", "Rapid Set Cement 25 kg", "cement", "bag", 10.50, 0, {"type": "rapid", "strength": "42.5", "weight_kg": 25}),
    ("CEM-003", "Portland Cement Premium 25 kg", "cement", "bag", 10.10, 45, {"type": "portland", "strength": "42.5", "weight_kg": 25}),
    ("TIM-001", "C24 Timber 45 x 95 mm 3.6 m", "timber", "piece", 12.40, 80, {"grade": "C24", "width_mm": 95, "thickness_mm": 45, "length_m": 3.6}),
    ("TIM-002", "C24 Timber 45 x 95 mm 4.8 m", "timber", "piece", 16.20, 0, {"grade": "C24", "width_mm": 95, "thickness_mm": 45, "length_m": 4.8}),
    ("TIM-003", "C24 Timber Premium 45 x 95 mm 4.8 m", "timber", "piece", 17.10, 35, {"grade": "C24", "width_mm": 95, "thickness_mm": 45, "length_m": 4.8}),
    ("PLS-001", "Standard Plasterboard 12.5 x 1200 x 2400 mm", "plasterboard", "sheet", 11.75, 90, {"type": "standard", "thickness_mm": 12.5, "width_mm": 1200, "length_mm": 2400}),
    ("PLS-002", "Moisture Resistant Plasterboard 12.5 x 1200 x 2400 mm", "plasterboard", "sheet", 18.90, 0, {"type": "moisture_resistant", "thickness_mm": 12.5, "width_mm": 1200, "length_mm": 2400}),
    ("PLS-003", "Moisture Resistant Board 12.5 x 1200 x 2400 mm", "plasterboard", "sheet", 19.20, 24, {"type": "moisture_resistant", "thickness_mm": 12.5, "width_mm": 1200, "length_mm": 2400}),
    ("INS-001", "Mineral Wool Insulation 100 mm", "insulation", "pack", 39.00, 42, {"material": "mineral_wool", "thickness_mm": 100, "thermal_lambda": 0.037}),
    ("INS-002", "Glass Wool Insulation 100 mm", "insulation", "pack", 35.50, 0, {"material": "glass_wool", "thickness_mm": 100, "thermal_lambda": 0.037}),
    ("INS-003", "Glass Wool Insulation Eco 100 mm", "insulation", "pack", 36.25, 31, {"material": "glass_wool", "thickness_mm": 100, "thermal_lambda": 0.037}),
    ("SCR-001", "Wood Screws 5 x 80 mm Box 200", "fasteners", "box", 14.30, 70, {"use": "wood", "diameter_mm": 5, "length_mm": 80, "count": 200}),
    ("SCR-002", "Decking Screws 5 x 80 mm Box 200", "fasteners", "box", 18.20, 0, {"use": "outdoor_wood", "diameter_mm": 5, "length_mm": 80, "count": 200}),
    ("SCR-003", "Outdoor Wood Screws 5 x 80 mm Box 200", "fasteners", "box", 19.10, 18, {"use": "outdoor_wood", "diameter_mm": 5, "length_mm": 80, "count": 200}),
    ("BRK-001", "Red Clay Brick 228 x 108 x 54 mm", "masonry", "piece", 1.25, 600, {"material": "clay", "length_mm": 228, "width_mm": 108, "height_mm": 54}),
    ("BLK-001", "Aerated Concrete Block 100 x 200 x 600 mm", "masonry", "piece", 4.80, 0, {"material": "aac", "thickness_mm": 100, "height_mm": 200, "length_mm": 600}),
    ("BLK-002", "AAC Building Block 100 x 200 x 600 mm", "masonry", "piece", 5.05, 160, {"material": "aac", "thickness_mm": 100, "height_mm": 200, "length_mm": 600}),
    ("PNT-001", "Interior Wall Paint White 10 L", "paint", "bucket", 46.00, 28, {"use": "interior", "colour": "white", "volume_l": 10, "finish": "matt"}),
    ("PNT-002", "Exterior Paint White 10 L", "paint", "bucket", 61.00, 0, {"use": "exterior", "colour": "white", "volume_l": 10, "finish": "matt"}),
    ("PNT-003", "Exterior Wall Paint White 10 L", "paint", "bucket", 63.50, 14, {"use": "exterior", "colour": "white", "volume_l": 10, "finish": "matt"}),
    ("PLY-001", "Structural Plywood 18 x 1220 x 2440 mm", "sheet_material", "sheet", 42.00, 33, {"material": "plywood", "thickness_mm": 18, "width_mm": 1220, "length_mm": 2440}),
    ("OSB-001", "OSB3 Board 18 x 1220 x 2440 mm", "sheet_material", "sheet", 31.50, 0, {"material": "osb3", "thickness_mm": 18, "width_mm": 1220, "length_mm": 2440}),
    ("OSB-002", "OSB3 Construction Board 18 x 1220 x 2440 mm", "sheet_material", "sheet", 32.40, 55, {"material": "osb3", "thickness_mm": 18, "width_mm": 1220, "length_mm": 2440}),
    ("ADH-001", "Tile Adhesive Flexible 20 kg", "adhesive", "bag", 22.50, 40, {"use": "tile", "type": "flexible", "weight_kg": 20}),
    ("MOR-001", "Masonry Mortar 25 kg", "mortar", "bag", 9.80, 65, {"use": "masonry", "strength": "M5", "weight_kg": 25}),
]


def seed_products(db: Session) -> int:
    existing = {sku for (sku,) in db.query(Product.sku).all()}
    rows = [Product(sku=sku, name=name, category=category, selling_unit=unit,
                    price=price, stock_qty=stock, technical_specs=specs)
            for sku, name, category, unit, price, stock, specs in PRODUCTS if sku not in existing]
    db.add_all(rows)
    db.commit()
    return len(rows)


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        print(f"Seeded {seed_products(session)} products.")
