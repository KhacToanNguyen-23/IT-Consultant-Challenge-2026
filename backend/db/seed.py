"""Idempotent 65-product demo catalog covering the five MVP category groups."""

from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine
from .models import Product


PRODUCTS: list[tuple[str, str, str, str, float, int, dict]] = []

# Timber / gỗ xẻ (15)
for index, (section, grade, length, price, stock) in enumerate([
    ("45x95", "C14", 3.6, 9.40, 55), ("45x95", "C16", 3.6, 10.20, 42),
    ("45x95", "C18", 3.6, 11.10, 35), ("45x95", "C24", 3.6, 12.40, 80),
    ("45x95", "C24", 4.8, 16.20, 0), ("45x95", "C30", 4.8, 18.90, 28),
    ("45x145", "C16", 3.6, 15.80, 34), ("45x145", "C18", 3.6, 16.90, 22),
    ("45x145", "C24", 3.6, 18.50, 48), ("45x145", "C24", 4.8, 24.60, 19),
    ("45x195", "C18", 3.6, 22.10, 15), ("45x195", "C24", 3.6, 24.80, 31),
    ("45x195", "C30", 4.8, 35.60, 12), ("38x89", "C16", 3.0, 8.75, 44),
    ("38x89", "C24", 3.0, 10.30, 26),
], 1):
    width, height = map(int, section.split("x"))
    PRODUCTS.append((f"TIM-{index:03d}", f"Sawn Timber {grade} {width} x {height} mm {length:g} m",
                     "timber", "piece", price, stock,
                     {"cross_section": section, "width_mm": width, "thickness_mm": height,
                      "strength_grade": grade, "length_m": length, "type": "sawn"}))

# Gypsum / thạch cao (12)
for index, (thickness, board_type, moisture, width, length, price, stock) in enumerate([
    (9.5, "standard", False, 1200, 2400, 9.20, 65), (12.5, "standard", False, 1200, 2400, 11.75, 90),
    (12.5, "standard", False, 900, 2400, 10.40, 38), (15, "standard", False, 1200, 2400, 14.80, 27),
    (12.5, "moisture_resistant", True, 1200, 2400, 18.90, 0),
    (12.5, "moisture_resistant", True, 900, 2400, 17.10, 24),
    (15, "moisture_resistant", True, 1200, 2400, 22.30, 16),
    (12.5, "fire_resistant", False, 1200, 2400, 20.60, 29),
    (15, "fire_resistant", False, 1200, 2400, 24.90, 14),
    (12.5, "acoustic", False, 1200, 2400, 23.50, 18),
    (15, "acoustic", False, 1200, 2400, 27.20, 11),
    (6.5, "flexible", False, 1200, 2400, 16.40, 20),
], 1):
    label = board_type.replace("_", " ").title()
    PRODUCTS.append((f"GYP-{index:03d}", f"{label} Gypsum Board {thickness:g} x {width} x {length} mm",
                     "gypsum", "sheet", price, stock,
                     {"thickness_mm": thickness, "type": board_type, "moisture_resistant": moisture,
                      "width_mm": width, "length_mm": length}))

# Cement and mortar / xi măng và vữa (14)
for index, (kind, grade, weight, price, stock) in enumerate([
    ("portland_cement", "42.5N", 25, 8.95, 120), ("portland_cement", "42.5N", 20, 7.60, 52),
    ("portland_cement", "52.5N", 25, 10.80, 35), ("rapid_cement", "42.5R", 25, 10.50, 0),
    ("rapid_cement", "42.5R", 20, 9.20, 28), ("white_cement", "32.5N", 25, 14.70, 19),
    ("masonry_mortar", "M5", 25, 9.80, 65), ("masonry_mortar", "M5", 20, 8.40, 32),
    ("masonry_mortar", "M10", 25, 11.60, 36), ("repair_mortar", "R3", 25, 18.20, 23),
    ("repair_mortar", "R4", 25, 23.90, 17), ("render_mortar", "GP", 25, 10.90, 41),
    ("floor_screed", "CT-C25", 25, 12.40, 30), ("floor_screed", "CT-C30", 25, 14.10, 21),
], 1):
    label = kind.replace("_", " ").title()
    PRODUCTS.append((f"CEM-{index:03d}", f"{label} {grade} {weight} kg",
                     "cement_mortar", "bag", price, stock,
                     {"type": kind, "grade": grade, "bag_weight": weight}))

# Insulation / cách nhiệt (12). INS-012 deliberately has no safe same-thickness substitute.
for index, (material, thickness, thermal_lambda, price, stock) in enumerate([
    ("mineral_wool", 50, 0.037, 24.00, 44), ("glass_wool", 50, 0.037, 21.50, 31),
    ("pir", 50, 0.022, 39.00, 25), ("mineral_wool", 75, 0.037, 31.50, 37),
    ("glass_wool", 75, 0.037, 28.80, 20), ("mineral_wool", 100, 0.037, 39.00, 42),
    ("glass_wool", 100, 0.037, 35.50, 0), ("pir", 100, 0.022, 61.00, 18),
    ("mineral_wool", 150, 0.037, 55.00, 26), ("glass_wool", 150, 0.037, 49.50, 22),
    ("pir", 150, 0.022, 86.00, 10), ("pir", 200, 0.022, 112.00, 0),
], 1):
    label = material.replace("_", " ").title()
    PRODUCTS.append((f"INS-{index:03d}", f"{label} Insulation {thickness} mm",
                     "insulation", "pack", price, stock,
                     {"type": material, "thickness_mm": thickness, "thermal_lambda": thermal_lambda}))

# Decking / ván sàn ngoài trời (12)
for index, (material, section, treatment, length, price, stock) in enumerate([
    ("pine", "28x120", ["pressure_treated", "fungal_resistant"], 3.6, 14.20, 46),
    ("pine", "28x120", ["pressure_treated", "fungal_resistant"], 4.8, 18.90, 0),
    ("pine", "28x120", ["pressure_treated", "fungal_resistant", "water_repellent"], 4.8, 20.40, 24),
    ("spruce", "28x120", ["untreated"], 3.6, 12.10, 33),
    ("spruce", "28x145", ["pressure_treated", "fungal_resistant"], 3.6, 17.80, 21),
    ("pine", "28x145", ["pressure_treated", "fungal_resistant", "water_repellent"], 4.8, 24.60, 18),
    ("composite", "25x140", ["water_repellent", "rot_resistant"], 3.6, 31.50, 29),
    ("composite", "25x140", ["water_repellent", "rot_resistant", "uv_resistant"], 4.0, 36.80, 16),
    ("composite", "23x138", ["water_repellent", "rot_resistant", "uv_resistant"], 3.6, 30.20, 22),
    ("larch", "27x142", ["untreated", "rot_resistant"], 4.0, 28.90, 14),
    ("thermowood", "26x117", ["heat_treated", "rot_resistant"], 3.6, 34.50, 20),
    ("thermowood", "26x140", ["heat_treated", "rot_resistant"], 4.2, 42.00, 12),
], 1):
    width, height = map(int, section.split("x"))
    PRODUCTS.append((f"DEK-{index:03d}", f"{material.title()} Decking {width} x {height} mm {length:g} m",
                     "decking", "piece", price, stock,
                     {"type": material, "cross_section": section, "width_mm": width,
                      "thickness_mm": height, "treatment": treatment, "length_m": length}))


def seed_products(db: Session) -> int:
    existing = {product.sku: product for product in db.query(Product).all()}
    rows = []
    for sku, name, category, unit, price, stock, specs in PRODUCTS:
        product = existing.get(sku)
        if product is None:
            rows.append(Product(sku=sku, name=name, category=category, selling_unit=unit,
                                price=price, stock_qty=stock, technical_specs=specs))
            continue
        new_values = (name, category, unit, price, stock, specs)
        old_values = (product.name, product.category, product.selling_unit,
                      product.price, product.stock_qty, product.technical_specs)
        if old_values != new_values:
            product.name, product.category, product.selling_unit = name, category, unit
            product.price, product.stock_qty, product.technical_specs = price, stock, specs
            product.embedding = None
    db.add_all(rows)
    db.commit()
    return len(rows)


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        print(f"Seeded {seed_products(session)} products.")
