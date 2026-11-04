"""Builds backend/seeds/evaluation.jsonl — the D22 labelled set (SRS v2 §11.1).

Each case: (text, language, kind, expected_skus, note)
  expected_skus = acceptable correct SKUs; [] means "no safe SKU exists → must NOT be auto-matched"
  kind: easy | slang | other_lang | trap (size/grade mismatch) | missing (must ask) | absent (not in catalog)
Labels were drafted with AI assistance and MUST be reviewed by a human before results are quoted
(field reviewed=false until a teammate checks the row). Do not tune rules/aliases on this set.
"""
import json
from pathlib import Path

T = "SKU-DK-"
C = [
    # ---------------- timber ----------------
    ("Timber 45x95 C24 - 120 m", "EN", "easy", [T + "4595-480"], "slide-9 example"),
    ("Konstruktionstræ 45x95 C24 4,8 m - 25 stk", "DA", "easy", [T + "4595-480"], ""),
    ("45x95 C18 - 30 stk", "DA", "easy", [T + "4595-C18-480"], ""),
    ("regel 45 x 95 c18 30 stk", "DA", "slang", [T + "4595-C18-480"], "spaces around x"),
    ("Spær 45x195 C24 8 stk", "DA", "slang", [T + "45195-540"], "spær = rafter"),
    ("45x195 C30 5,4m 6 stk", "DA", "easy", [T + "45195-C30-540"], ""),
    ("Bjælke 45x220 C24 - 4 stk", "DA", "slang", [T + "45220-540"], ""),
    ("Lægte 35x70 C18 - 40 stk", "DA", "easy", [T + "3570-C18-360"], ""),
    ("Lægter 36x48 C18 50 stk", "DA", "easy", [T + "3648-C18-360"], ""),
    ("Brædder 22x95 C18 - 20 stk", "DA", "slang", [T + "2295-C18-360"], ""),
    ("45x45 C18 lægte 3,6m 12 stk", "DA", "easy", [T + "4545-C18-360"], ""),
    ("Konstruksjonsvirke 48x98 C24 - 30 stk", "NO", "other_lang", [T + "4898-480"], ""),
    ("Konstruksjonsvirke 48x148 C24 20 stk", "NO", "other_lang", [T + "48148-480"], ""),
    ("Bjelke 48x198 C24 6 stk", "NO", "other_lang", [T + "48198-540"], ""),
    ("Reglar 45x95 C24, 30 st", "SV", "other_lang", [T + "4595-480"], ""),
    ("Konstruktionsvirke 45x145 C24 - 12 st", "SV", "other_lang", [T + "45145-480"], ""),
    ("Konstruktionsvirke 45x145 C30 12 st", "SV", "other_lang", [T + "45145-C30-480"], ""),
    ("Stud 45x70 C24 - 40 pcs", "EN", "other_lang", [T + "4570-480"], ""),
    ("45x70 C18 stud 4.8m 10 pcs", "EN", "easy", [T + "4570-C18-480"], ""),
    ("45x120 C24 - 60 m", "DA", "easy", [T + "45120-480"], "out of stock in seed"),
    ("45x120 C30 konstruktionstræ 10 stk", "DA", "easy", [T + "45120-C30-480"], ""),
    ("Træ 45x170 C24 8 stk", "DA", "easy", [T + "45170-480"], ""),
    ("45x245 C24 bjælke 2 stk", "DA", "easy", [T + "45245-540"], ""),
    ("Timber 45x95 C30 - 20 pcs", "EN", "trap", [], "no 45x95 C30 in catalog; must not fall back to C24"),
    ("Konstruktionstræ 45x120 C18 10 stk", "DA", "trap", [], "no 45x120 C18; C24 would be an unrequested upgrade"),
    ("45x100 C24 regel 10 stk", "DA", "trap", [], "45x100 does not exist; 45x95 is NOT the same"),
    ("Regel 45x95 - 20 stk", "DA", "missing", [T + "4595-480", T + "4595-C18-480"], "grade missing → ask"),
    ("Træ 45x145 10 stk", "DA", "missing", [T + "45145-480", T + "45145-C30-480"], "grade missing"),
    ("Reglar 45x70 20 st", "SV", "missing", [T + "4570-480", T + "4570-C18-480"], "grade missing"),
    ("konstruktionstræ C24 30 stk", "DA", "missing", [], "cross-section missing"),
    # ---------------- gypsum ----------------
    ("Gipsplade standard 12,5 mm - 20 plader", "DA", "easy", ["SKU-GYP-STD-125"], ""),
    ("Gips standard 9,5mm 10 plader", "DA", "easy", ["SKU-GYP-STD-095"], ""),
    ("Gipsplader normal 15 mm 12 stk", "DA", "slang", ["SKU-GYP-STD-150"], "normal = standard"),
    ("Gips vådrum 12.5mm - 10 plader", "DA", "easy", ["SKU-GYP-MR-125", "SKU-GYP-MR-125-B"], "two wet-room boards"),
    ("Vådrumsgips 15mm 6 plader", "DA", "slang", ["SKU-GYP-MR-150"], ""),
    ("Brandgips 12,5mm 15 plader", "DA", "easy", ["SKU-GYP-FIRE-125"], ""),
    ("Brandplade 15 mm - 8 stk", "DA", "slang", ["SKU-GYP-FIRE-150"], ""),
    ("Robust gips 12,5 mm 10 plader", "DA", "slang", ["SKU-GYP-IMP-125"], ""),
    ("Slagfast gipsplade 12.5mm 4 stk", "DA", "slang", ["SKU-GYP-IMP-125"], ""),
    ("Våtromsplate 12.5 mm 8 plater", "NO", "other_lang", ["SKU-GYP-MR-125", "SKU-GYP-MR-125-B"], ""),
    ("Gipsplate standard 12,5 mm 30 plater", "NO", "other_lang", ["SKU-GYP-STD-125"], ""),
    ("Brannplate 15mm 10 plater", "NO", "other_lang", ["SKU-GYP-FIRE-150"], ""),
    ("Gipsskiva standard 12,5 mm 25 st", "SV", "other_lang", ["SKU-GYP-STD-125"], ""),
    ("Våtrumsskiva 12,5mm 6 st", "SV", "other_lang", ["SKU-GYP-MR-125", "SKU-GYP-MR-125-B"], ""),
    ("Plasterboard standard 12.5mm x 20", "EN", "other_lang", ["SKU-GYP-STD-125"], ""),
    ("Moisture board 12.5mm 10 boards", "EN", "other_lang", ["SKU-GYP-MR-125", "SKU-GYP-MR-125-B"], ""),
    ("Gips 12,5 mm 20 plader", "DA", "missing", ["SKU-GYP-STD-125", "SKU-GYP-MR-125", "SKU-GYP-FIRE-125", "SKU-GYP-IMP-125", "SKU-GYP-MR-125-B"], "type missing → ask"),
    ("Brandgips 18mm 5 plader", "DA", "trap", [], "18 mm not stocked; 15 mm is NOT equal"),
    ("Vådrumsgips 9,5mm 4 plader", "DA", "trap", [], "no 9.5 wet-room board; standard 9.5 must not be offered"),
    ("Gipsplade 6,5 mm standard 4 plader", "DA", "easy", ["SKU-GYP-STD-065"], ""),
    # ---------------- insulation ----------------
    ("Rockwool FlexiBatts 95mm - 15 pk", "DA", "easy", ["SKU-RW-095"], ""),
    ("Isover 95 mm 10 pk", "DA", "easy", ["SKU-ISOVER-095"], ""),
    ("Isolering 95mm 60 m2", "DA", "easy", ["SKU-RW-095", "SKU-ISOVER-095"], "brand not stated: either is right"),
    ("Stenuld 145 mm - 20 pakker", "DA", "slang", ["SKU-RW-145"], "stenuld = stone wool"),
    ("Mineraluld 195mm 8 pk", "DA", "slang", ["SKU-RW-195", "SKU-ISOVER-195"], ""),
    ("Rockwool 220 mm batts 6 pk", "DA", "easy", ["SKU-RW-220"], ""),
    ("Isolering 45 mm 3 pk", "DA", "easy", ["SKU-RW-045"], ""),
    ("Knauf 120mm 10 pk", "DA", "easy", ["SKU-KNAUF-120"], ""),
    ("Isolasjon 70 mm 12 pk", "NO", "other_lang", ["SKU-RW-070", "SKU-ISOVER-070"], ""),
    ("Steinull 145mm 10 pakker", "NO", "other_lang", ["SKU-RW-145"], ""),
    ("Isolering 120 mm 30 m2", "SV", "other_lang", ["SKU-RW-120", "SKU-KNAUF-120"], ""),
    ("Glasull 195 mm 5 paket", "SV", "other_lang", ["SKU-ISOVER-195"], ""),
    ("Insulation batts 95mm 12 packs", "EN", "other_lang", ["SKU-RW-095", "SKU-ISOVER-095"], ""),
    ("Glass wool 145mm 8 packs", "EN", "other_lang", ["SKU-ISOVER-145"], ""),
    ("Isolering 100 mm 10 pk", "DA", "trap", [], "100 mm not stocked; 95 is NOT equal"),
    ("Rockwool 150mm 6 pk", "DA", "trap", [], "150 not stocked; 145 is NOT equal"),
    ("Isolering til loft 20 pk", "DA", "missing", [], "thickness missing"),
    # ---------------- cement / mortar ----------------
    ("Cement 25 kg - 4 sække", "DA", "easy", ["SKU-CEM-25-STD"], ""),
    ("Murmørtel 25kg - 5 sække", "DA", "easy", ["SKU-MORT-25"], "out of stock, no safe substitute"),
    ("Kalkmørtel 20 kg 6 sække", "DA", "easy", ["SKU-MORT-20-LIME"], ""),
    ("Hurtigcement 25kg 2 sække", "DA", "slang", ["SKU-CEM-25-RAPID"], ""),
    ("Hvid cement 25 kg 1 sæk", "DA", "easy", ["SKU-CEM-25-WHITE"], ""),
    ("Tørbeton 25kg 10 sække", "DA", "slang", ["SKU-CONC-25"], ""),
    ("Fliseklæb 20kg 3 sække", "DA", "easy", ["SKU-TILE-20"], ""),
    ("Fugemasse grå 5 kg 2 spande", "DA", "easy", ["SKU-GROUT-05"], "unit 'spande' unknown → still matches SKU"),
    ("Flydespartel 20 kg 4 sække", "DA", "easy", ["SKU-LEVEL-20"], ""),
    ("Puds 25kg 6 sække", "DA", "slang", ["SKU-RENDER-25"], ""),
    ("Sement 25 kg 8 sekker", "NO", "other_lang", ["SKU-CEM-25-STD"], ""),
    ("Murbruk 25 kg 5 sekker", "NO", "other_lang", ["SKU-MORT-25"], ""),
    ("Flislim 20kg 2 sekker", "NO", "other_lang", ["SKU-TILE-20"], ""),
    ("Betong 25 kg 12 säckar", "SV", "other_lang", ["SKU-CONC-25"], ""),
    ("Tile adhesive 20kg x 4 bags", "EN", "other_lang", ["SKU-TILE-20"], ""),
    ("Mørtel 20 kg 5 sække", "DA", "trap", [], "only lime mortar is 20 kg; plain mortar 20 kg does not exist"),
    ("Cement 50 kg 2 sække", "DA", "trap", [], "50 kg bag not stocked"),
    ("Cement 10 sække", "DA", "missing", ["SKU-CEM-25-STD"], "bag weight missing → ask"),
    # ---------------- decking ----------------
    ("Terrassebræt 28x120 trykimp 10 x 4.2m", "DA", "easy", ["SKU-DECK-28120-420", "SKU-DECK-28120-NTR-420"], "NTR satisfies pressure-treated"),
    ("Terrassebrædder 28x120 NTR/AB 40 stk", "DA", "easy", ["SKU-DECK-28120-NTR-420"], ""),
    ("Terrassebræt 28x145 trykimprægneret 30 stk", "DA", "easy", ["SKU-DECK-28145-420", "SKU-DECK-28145-NTR-480"], ""),
    ("Terrasse 21x95 trykimp 50 stk", "DA", "slang", ["SKU-DECK-2195-360"], ""),
    ("Hårdttræ terrassebræt 21x145 20 stk", "DA", "easy", ["SKU-DECK-21145-HW-360"], ""),
    ("Komposit terrassebræt 25x125 15 stk", "DA", "easy", ["SKU-DECK-25125-COMP-400"], ""),
    ("Thermo terrassebræt 28x120 25 stk", "DA", "easy", ["SKU-DECK-28120-THERMO-420"], ""),
    ("Terrassebord 28x120 impregnert 40 stk", "NO", "other_lang", ["SKU-DECK-28120-420", "SKU-DECK-28120-NTR-420"], ""),
    ("Trall 28x95 tryckimpregnerad 30 st", "SV", "other_lang", ["SKU-DECK-2895-420"], ""),
    ("Decking board 34x145 pressure treated 20 pcs", "EN", "other_lang", ["SKU-DECK-34145-480"], ""),
    ("Terrassebræt 28x120 thermo NTR 10 stk", "DA", "trap", [], "no thermo board with NTR class"),
    ("Terrassebræt 28x170 trykimp 10 stk", "DA", "trap", [], "28x170 not stocked"),
    ("Terrassebræt 28x120 20 stk", "DA", "missing", ["SKU-DECK-28120-420", "SKU-DECK-28120-NTR-420", "SKU-DECK-28120-THERMO-420"], "treatment missing → ask"),
]

out = Path(__file__).parent / "evaluation.jsonl"
with out.open("w", encoding="utf-8") as f:
    for i, (text, lang, kind, exp, note) in enumerate(C, 1):
        f.write(json.dumps({"id": f"E{i:03d}", "text": text, "language": lang, "kind": kind, "expected_skus": exp,
                            "must_clarify": kind in ("missing", "trap", "absent") or not exp,
                            "note": note, "reviewed": False}, ensure_ascii=False) + "\n")
print(f"{len(C)} cases → {out.name}")
