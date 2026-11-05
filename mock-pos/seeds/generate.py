"""Deterministic seed generator (SRS v2 §6.3): 60-80 SKU in 5 groups, DK/DKK, simulated prices/stock.

Run:  python mock-pos/seeds/generate.py      → rewrites catalog.json + stock_customers.json
Rules kept on purpose:
  * one standard length per timber (cross-section, grade) so "45x95 C24 - 120 m" has exactly one safe SKU
  * stockout / low-stock cases WITH a safe substitute and WITHOUT one (validator below checks this)
  * no accessories / screws
"""
import json
import random
from pathlib import Path

HERE = Path(__file__).parent
RNG = random.Random(2026)
VERSION = "seed-2026-11-04"

items: list[dict] = []
stock: dict[str, float] = {}


def add(sku, name, category, selling_unit, pack_size, price, specs, aliases=None, on_hand=None):
    items.append({"sku": sku, "name": name, "category": category, "selling_unit": selling_unit, "pack_size": pack_size,
                  "unit_price": round(price, 2), "currency": "DKK", "technical_specs": specs, "aliases": aliases or {}})
    if on_hand is None:
        r = RNG.random()
        on_hand = 0 if r < 0.08 else RNG.randint(3, 12) if r < 0.2 else RNG.randint(30, 400)
    stock[sku] = on_hand


# ---------------- timber (must: cross_section_mm, strength_grade) ----------------
TIMBER = [  # w, h, grade, length, on_hand(None=random)
    (45, 45, "C18", 3.6, None), (45, 70, "C18", 4.8, None), (45, 70, "C24", 4.8, None),
    (45, 95, "C18", 4.8, 200), (45, 95, "C24", 4.8, 140), (45, 120, "C24", 4.8, 0), (45, 120, "C30", 4.8, 60),
    (45, 145, "C24", 4.8, None), (45, 145, "C30", 4.8, None), (45, 170, "C24", 4.8, None),
    (45, 195, "C24", 5.4, 8), (45, 195, "C30", 5.4, None), (45, 220, "C24", 5.4, None), (45, 245, "C24", 5.4, 0),
    (35, 70, "C18", 3.6, None), (48, 98, "C24", 4.8, None), (48, 148, "C24", 4.8, None), (48, 198, "C24", 5.4, None),
    (22, 95, "C18", 3.6, None), (36, 48, "C18", 3.6, None),
]
for w, h, g, ln, oh in TIMBER:
    cs = f"{w}x{h}"
    sku = f"SKU-DK-{w}{h}{'' if g == 'C24' else '-' + g}-{int(ln * 100)}"
    price = w * h / 4275 * ln / 4.8 * 100 * {"C18": 0.85, "C24": 1.0, "C30": 1.09}[g]
    kind = "Lægte" if w <= 36 or h <= 48 else "Konstruktionstræ"
    aliases = {"da": [f"træ {cs}", f"regel {cs}", f"{kind.lower()} {cs} {g.lower()}"], "no": [f"konstruksjonsvirke {cs}"],
               "sv": [f"konstruktionsvirke {cs}", f"regel {cs}"], "en": [f"timber {cs} {g}", f"stud {cs}"]}
    add(sku, f"{kind} {cs} {g} {ln}m", "timber", f"piece_{ln}m", ln, price,
        {"cross_section_mm": cs, "strength_grade": g, "length_m": ln}, aliases, oh)

# ---------------- gypsum (must: thickness_mm, board_type) ----------------
GYP = [  # sku, name, thickness, type, brand, price, on_hand
    ("SKU-GYP-STD-095", "Gipsplade standard 9.5mm 1200x2400", 9.5, "standard", "Gyproc", 59, None),
    ("SKU-GYP-STD-125", "Gipsplade standard 12.5mm 1200x2400", 12.5, "standard", "Gyproc", 69, 300),
    ("SKU-GYP-STD-150", "Gipsplade standard 15mm 1200x2400", 15, "standard", "Gyproc", 89, None),
    ("SKU-GYP-MR-125", "Gipsplade vådrum 12.5mm 1200x2400", 12.5, "moisture", "Gyproc", 95, 0),
    ("SKU-GYP-MR-125-B", "Vådrumsplade Brand B 12.5mm 1200x2400", 12.5, "moisture", "B", 99, 40),
    ("SKU-GYP-MR-150", "Gipsplade vådrum 15mm 1200x2400", 15, "moisture", "Gyproc", 115, None),
    ("SKU-GYP-FIRE-125", "Brandgipsplade 12.5mm 1200x2400", 12.5, "fire", "Gyproc", 92, 0),
    ("SKU-GYP-FIRE-150", "Brandgipsplade 15mm 1200x2400", 15, "fire", "Gyproc", 112, None),
    ("SKU-GYP-IMP-125", "Gipsplade robust (slagfast) 12.5mm 1200x2400", 12.5, "impact", "Gyproc", 129, None),
    ("SKU-GYP-STD-065", "Gipsplade buet 6.5mm 1200x2400", 6.5, "standard", "Gyproc", 79, None),
]
TYPE_ALIAS = {"standard": ["gips", "gipsplade", "gipsplate", "gipsskiva", "plasterboard"],
              "moisture": ["vådrumsgips", "våtromsplate", "våtrumsskiva", "moisture board"],
              "fire": ["brandgips", "brannplate", "brandskiva", "fire board"],
              "impact": ["robust gips", "slagfast gips"]}
for sku, name, th, t, brand, price, oh in GYP:
    add(sku, name, "gypsum", "sheet", None, price,
        {"thickness_mm": th, "board_type": t, "moisture_resistant": t == "moisture", "brand": brand},
        {"da": [f"{a} {th:g}" for a in TYPE_ALIAS[t][:2]], "en": [f"{TYPE_ALIAS[t][-1]} {th:g}mm"]}, oh)

# ---------------- insulation (must: thickness_mm) ----------------
INS = [  # sku, brand, material, thickness, m2/pack, price, on_hand
    ("SKU-RW-045", "Rockwool", "stone_wool", 45, 7.2, 189, None), ("SKU-RW-070", "Rockwool", "stone_wool", 70, 4.5, 165, None),
    ("SKU-RW-095", "Rockwool", "stone_wool", 95, 2.88, 120.5, 5), ("SKU-RW-120", "Rockwool", "stone_wool", 120, 2.7, 139, None),
    ("SKU-RW-145", "Rockwool", "stone_wool", 145, 1.8, 135, 30), ("SKU-RW-195", "Rockwool", "stone_wool", 195, 1.35, 142, None),
    ("SKU-RW-220", "Rockwool", "stone_wool", 220, 1.2, 149, None),
    ("SKU-ISOVER-070", "Isover", "glass_wool", 70, 4.68, 159, None), ("SKU-ISOVER-095", "Isover", "glass_wool", 95, 2.88, 125.5, 42),
    ("SKU-ISOVER-145", "Isover", "glass_wool", 145, 2.16, 149, 0), ("SKU-ISOVER-195", "Isover", "glass_wool", 195, 1.56, 155, None),
    ("SKU-KNAUF-120", "Knauf", "glass_wool", 120, 3.0, 136, None),
]
for sku, brand, mat, th, pk, price, oh in INS:
    nm = {"Rockwool": "Rockwool FlexiBatts", "Isover": "Isover Plus", "Knauf": "Knauf Unifit"}[brand]
    add(sku, f"{nm} {th}mm ({pk:g} m2/pk)", "insulation", "pack", pk, price,
        {"thickness_mm": th, "material": mat, "brand": brand},
        {"da": [f"isolering {th}mm", f"{'stenuld' if mat == 'stone_wool' else 'glasuld'} {th}"], "no": [f"isolasjon {th}mm"],
         "sv": [f"isolering {th} mm"], "en": [f"insulation batts {th}mm"]}, oh)

# ---------------- cement / mortar (must: bag_weight_kg, product_type) ----------------
CEM = [  # sku, name, kg, type, price, on_hand
    ("SKU-CEM-25-STD", "Cement standard 25kg", 25, "cement", 55, 80),
    ("SKU-CEM-25-RAPID", "Cement rapid 25kg", 25, "rapid_cement", 79, None),
    ("SKU-CEM-25-WHITE", "Cement hvid 25kg", 25, "white_cement", 129, None),
    ("SKU-MORT-25", "Murmørtel KC 50/700 25kg", 25, "mortar", 62, 0),
    ("SKU-MORT-20-LIME", "Kalkmørtel 20kg", 20, "lime_mortar", 69, None),
    ("SKU-CONC-25", "Betonblanding (tørbeton) 25kg", 25, "concrete", 49, None),
    ("SKU-TILE-20", "Fliseklæb 20kg", 20, "tile_adhesive", 189, None),
    ("SKU-GROUT-05", "Fugemasse grå 5kg", 5, "grout", 119, None),
    ("SKU-LEVEL-20", "Flydespartel 20kg", 20, "levelling", 239, 0),
    ("SKU-RENDER-25", "Puds/filtsand 25kg", 25, "render", 89, None),
]
CEM_ALIAS = {"cement": ["cement", "sement", "cement sæk"], "rapid_cement": ["hurtigcement", "rapid cement"],
             "white_cement": ["hvid cement", "white cement"], "mortar": ["mørtel", "murmørtel", "murbruk"],
             "lime_mortar": ["kalkmørtel", "kalkbruk"], "concrete": ["beton", "tørbeton", "betong"],
             "tile_adhesive": ["fliseklæb", "flislim", "tile adhesive"], "grout": ["fugemasse", "fug"],
             "levelling": ["flydespartel", "avrettingsmasse", "flytspackel"], "render": ["puds", "filtsand"]}
for sku, name, kg, t, price, oh in CEM:
    add(sku, name, "cement", "bag", None, price, {"bag_weight_kg": kg, "product_type": t},
        {"da": CEM_ALIAS[t][:2], "en": [CEM_ALIAS[t][-1]]}, oh)

# ---------------- decking (must: cross_section_mm, treatment[]) ----------------
DECK = [  # sku, name, cs, treatment, length, price, on_hand
    ("SKU-DECK-28120-420", "Terrassebræt trykimprægneret 28x120 4.2m", "28x120", ["pressure_treated"], 4.2, 48, 400),
    ("SKU-DECK-28120-NTR-420", "Terrassebræt NTR/AB 28x120 4.2m", "28x120", ["pressure_treated", "ntr_ab"], 4.2, 55, 120),
    ("SKU-DECK-28145-420", "Terrassebræt trykimprægneret 28x145 4.2m", "28x145", ["pressure_treated"], 4.2, 59, 12),
    ("SKU-DECK-28145-NTR-480", "Terrassebræt NTR/AB 28x145 4.8m", "28x145", ["pressure_treated", "ntr_ab"], 4.8, 74, None),
    ("SKU-DECK-2195-360", "Terrassebræt trykimprægneret 21x95 3.6m", "21x95", ["pressure_treated"], 3.6, 26, None),
    ("SKU-DECK-34145-480", "Terrassebræt trykimprægneret 34x145 4.8m", "34x145", ["pressure_treated"], 4.8, 89, 0),
    ("SKU-DECK-28120-THERMO-420", "Terrassebræt thermo-fyr 28x120 4.2m", "28x120", ["thermo"], 4.2, 79, None),
    ("SKU-DECK-21145-HW-360", "Terrassebræt hårdttræ 21x145 3.6m", "21x145", ["hardwood"], 3.6, 149, None),
    ("SKU-DECK-2895-420", "Terrassebræt trykimprægneret 28x95 4.2m", "28x95", ["pressure_treated"], 4.2, 39, None),
    ("SKU-DECK-25125-COMP-400", "Komposit terrassebræt 25x125 4.0m", "25x125", ["composite"], 4.0, 169, None),
]
for sku, name, cs, tr, ln, price, oh in DECK:
    add(sku, name, "decking", f"piece_{ln}m", ln, price, {"cross_section_mm": cs, "treatment": tr, "length_m": ln},
        {"da": [f"terrassebrædder {cs}", f"terrasse {cs}"], "no": [f"terrassebord {cs}"], "sv": [f"trall {cs}"],
         "en": [f"decking board {cs}"]}, oh)

# ---------------- customers / tiers ----------------
extra = {
    "_note": "Generated by generate.py (seed 2026). Simulated stock, pseudonymous customers (no PII), simulated tiers.",
    "store_id": "DK-CPH-04",
    "stock": stock,
    "customers": [
        {"client_id": "C-88921", "type": "B2B", "discount_tier": "TRADE_2", "market": "DK"},
        {"client_id": "C-77310", "type": "B2B", "discount_tier": "TRADE_1", "market": "DK"},
        {"client_id": "C-65002", "type": "B2B", "discount_tier": "TRADE_3", "market": "DK"},
        {"client_id": "DK-CPH-04-WALKIN", "type": "B2C_WalkIn", "discount_tier": "NONE", "market": "DK"},
    ],
    "discount_tiers": [
        {"tier_code": "NONE", "market": "DK", "discount_rate": 0.0, "valid_from": "2026-01-01", "simulated": True},
        {"tier_code": "TRADE_1", "market": "DK", "discount_rate": 0.05, "valid_from": "2026-01-01", "simulated": True},
        {"tier_code": "TRADE_2", "market": "DK", "discount_rate": 0.10, "valid_from": "2026-01-01", "simulated": True},
        {"tier_code": "TRADE_3", "market": "DK", "discount_rate": 0.15, "valid_from": "2026-01-01", "simulated": True},
    ],
}


def validate() -> None:
    cats = {i["category"] for i in items}
    assert cats == {"timber", "gypsum", "insulation", "cement", "decking"}, cats
    assert 60 <= len(items) <= 80, len(items)
    assert len({i["sku"] for i in items}) == len(items), "duplicate sku"
    seen = set()
    for i in items:
        if i["category"] == "timber":
            key = (i["technical_specs"]["cross_section_mm"], i["technical_specs"]["strength_grade"])
            assert key not in seen, f"timber cross-section+grade must be unique: {key}"
            seen.add(key)
    assert any(v == 0 for v in stock.values()) and any(0 < v < 15 for v in stock.values())
    assert stock["SKU-GYP-MR-125"] == 0 and stock["SKU-GYP-MR-125-B"] > 0, "stockout WITH safe substitute"
    assert stock["SKU-MORT-25"] == 0, "stockout WITHOUT safe substitute"
    assert sum(c["type"] == "B2B" for c in extra["customers"]) == 3


validate()
(HERE / "catalog.json").write_text(json.dumps({"_note": "Generated by generate.py — simulated catalog, prices in DKK.",
                                               "catalog_version": VERSION, "items": items}, ensure_ascii=False, indent=1), encoding="utf-8")
(HERE / "stock_customers.json").write_text(json.dumps(extra, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{len(items)} SKU · " + ", ".join(f"{c}={sum(i['category'] == c for i in items)}" for c in sorted({i['category'] for i in items})))
