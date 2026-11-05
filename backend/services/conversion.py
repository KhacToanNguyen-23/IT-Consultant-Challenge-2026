"""MVP-FR-012/013: convert requested qty → selling unit of the SKU. Ceil, no waste factor, never guess."""
from decimal import ROUND_CEILING, Decimal
from typing import Optional

from i18n import code


def _d(x) -> Decimal:
    return Decimal(str(x))


def _fmt(x: Decimal) -> str:
    s = format(x.normalize(), "f")
    return s


def convert(qty: Optional[float], unit: Optional[str], product: dict, length_hint: Optional[float] = None) -> dict:
    su = product["selling_unit"]
    pack = product.get("pack_size")
    out = {"selling_qty": None, "selling_unit": su, "formula": None, "rounded": False, "blocked_reason": None}
    if qty is None or qty <= 0:
        out["blocked_reason"] = code("conv_missing_qty")
        return out
    if unit is None:
        out["blocked_reason"] = code("conv_missing_unit")
        return out
    q = _d(qty)

    def ceil_div(divisor, unit_label):
        exact = q / _d(divisor)
        n = exact.to_integral_value(rounding=ROUND_CEILING)
        out.update(selling_qty=float(n), rounded=(n != exact),
                   formula=f"{_fmt(q)} {unit_label} ÷ {_fmt(_d(divisor))} = {_fmt(exact.quantize(Decimal('0.01')))}" + (f" → {n}" if n != exact else ""))

    def direct():
        if q != q.to_integral_value():
            out["blocked_reason"] = code("conv_fractional")
            return
        out.update(selling_qty=float(q), formula=f"{_fmt(q)} {su} (1:1)")

    if su.startswith("piece_") and pack:
        if unit == "linear_metre":
            if not pack:
                out["blocked_reason"] = code("conv_sku_no_length")
            else:
                ceil_div(pack, "m")
        elif unit == "piece":
            if length_hint and abs(float(length_hint) - float(pack)) > 1e-6:
                out["blocked_reason"] = code("conv_length_mismatch", hint=length_hint, pack=pack)
            else:
                direct()
        else:
            out["blocked_reason"] = code("conv_unconvertible", unit=unit, su=su)
    elif su == "pack":
        if unit == "square_metre":
            if not pack:
                out["blocked_reason"] = code("conv_no_pack_size")
            else:
                ceil_div(pack, "m²")
        elif unit in ("pack", "piece"):
            direct()
        else:
            out["blocked_reason"] = code("conv_unconvertible", unit=unit, su="pack")
    elif su in ("board", "bag"):
        if unit in (su, "piece"):
            direct()
        else:
            out["blocked_reason"] = code("conv_unconvertible", unit=unit, su=su)
    else:
        out["blocked_reason"] = code("conv_unsupported", su=su)
    return out
