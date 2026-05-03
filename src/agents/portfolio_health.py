from typing import Any


async def run(user: dict, llm: Any = None) -> dict:
    """
    Portfolio Health Agent.
    Calculates concentration risk and performance from provided holdings.
    Does NOT hardcode any market data or benchmark returns.
    """

    # ── Helpers ───────────────────────────────────────────────────────────
    def _flag(top_pct: float) -> str:
        if top_pct > 40:
            return "high"
        if top_pct >= 25:
            return "moderate"
        return "low"

    def _get_value(p: dict) -> float:
        if "current_value" in p:
            return float(p["current_value"])
        return float(p.get("quantity", 0)) * float(p.get("avg_cost", 0))

    def _get_cost(p: dict) -> float:
        if "cost_basis" in p:
            return float(p["cost_basis"])
        return 0.0

    def _benchmark_name(user: dict) -> str:
        currency = (user.get("currency") or "").upper()
        market = (user.get("market") or "").upper()
        if currency == "INR" or market in ("INDIA", "IN"):
            return "Nifty 50"
        if market in ("US", "USA") or currency == "USD":
            return "S&P 500"
        if "GLOBAL" in market or "MULTI" in market:
            return "MSCI World"
        return "Broad market benchmark"

    # ── Load positions ────────────────────────────────────────────────────
    positions = user.get("portfolio", {}).get("holdings", [])
    if not positions:
        positions = user.get("positions", [])

    # ── Empty portfolio ───────────────────────────────────────────────────
    if not positions:
        return {
            "concentration_risk": {
                "flag": "low",
                "note": "No holdings found."
            },
            "performance": {
                "total_return_pct": None,
                "annualized_return_pct": None,
                "note": "Performance requires current value and cost basis data."
            },
            "benchmark_comparison": {
                "benchmark": _benchmark_name(user),
                "benchmark_return_pct": None,
                "alpha_pct": None,
                "note": "Benchmark return requires an external market data feed."
            },
            "observations": [
                {"severity": "info", "text": "Your portfolio is empty. Here's how to start building it:"},
                {"severity": "info", "text": "1️⃣  Define your goals — retirement, house, education?"},
                {"severity": "info", "text": "2️⃣  Set your time horizon — when do you need the money?"},
                {"severity": "info", "text": "3️⃣  Know your risk profile — how much loss can you tolerate?"},
                {"severity": "info", "text": "4️⃣  Keep 3–6 months of expenses as an emergency fund before investing."},
                {"severity": "info", "text": "5️⃣  Consider low-cost, diversified index funds as a starting point (educational direction only)."},
            ],
            "disclaimer": (
                "This is educational guidance only, not investment advice. "
                "Please consult a registered financial advisor before making any investment decisions."
            ),
        }

    # ── Concentration risk ────────────────────────────────────────────────
    total_value = sum(_get_value(p) for p in positions)

    if total_value > 0:
        sorted_pos = sorted(positions, key=_get_value, reverse=True)
        top = sorted_pos[0]
        top_pct = (_get_value(top) / total_value) * 100
        top_3_pct = sum(_get_value(p) for p in sorted_pos[:3]) / total_value * 100
        top_name = top.get("symbol") or top.get("name") or "Unknown"
    else:
        top_pct = 0.0
        top_3_pct = 0.0
        top_name = "—"

    flag = _flag(top_pct)

    concentration_risk = {
        "top_holding": top_name,
        "top_position_pct": round(top_pct, 2),
        "top_3_positions_pct": round(top_3_pct, 2),
        "flag": flag,
    }

    # ── Performance (calculated, not hardcoded) ───────────────────────────
    total_cost = sum(_get_cost(p) for p in positions)
    if total_cost > 0:
        total_return_pct = round(((total_value - total_cost) / total_cost) * 100, 2)
        performance = {
            "total_current_value": round(total_value, 2),
            "total_cost_basis": round(total_cost, 2),
            "total_return_pct": total_return_pct,
            "annualized_return_pct": None,
            "note": (
                "Annualized return requires a purchase-date time period "
                "which was not provided."
            ),
        }
    else:
        performance = {
            "total_return_pct": None,
            "annualized_return_pct": None,
            "note": "Performance requires current value and cost basis data.",
        }

    # ── Benchmark (no external feed, so we declare it explicitly) ─────────
    benchmark_comparison = {
        "benchmark": _benchmark_name(user),
        "benchmark_return_pct": None,
        "alpha_pct": None,
        "note": "Benchmark return requires an external market data feed.",
    }

    # ── Observations ──────────────────────────────────────────────────────
    observations = []

    if flag == "high":
        observations.append({
            "severity": "warning",
            "text": (
                f"⚠️  {top_name} represents {top_pct:.1f}% of your portfolio — "
                "this is high concentration risk. Consider diversifying."
            ),
        })
    elif flag == "moderate":
        observations.append({
            "severity": "warning",
            "text": (
                f"{top_name} represents {top_pct:.1f}% of your portfolio — "
                "moderate concentration. Monitor closely."
            ),
        })
    else:
        observations.append({
            "severity": "info",
            "text": (
                f"Top holding ({top_name}) is {top_pct:.1f}% — "
                "concentration risk appears manageable."
            ),
        })

    if total_cost > 0:
        ret = performance["total_return_pct"]
        if ret is not None and ret > 0:
            observations.append({"severity": "info",
                                  "text": f"Overall portfolio return: +{ret:.1f}% based on cost basis."})
        elif ret is not None and ret <= 0:
            observations.append({"severity": "warning",
                                  "text": f"Overall portfolio return: {ret:.1f}% — below cost basis."})

    # ── Result ────────────────────────────────────────────────────────────
    return {
        "concentration_risk": concentration_risk,
        "performance": performance,
        "benchmark_comparison": benchmark_comparison,
        "observations": observations,
        "disclaimer": (
            "This is educational guidance only, not investment advice. "
            "Please consult a registered financial advisor before making any investment decisions."
        ),
    }
