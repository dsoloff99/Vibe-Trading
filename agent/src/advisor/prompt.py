"""System prompt for the wealth-manager review and the JSON parsing of its reply."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from src.advisor.models import Objectives, ReviewOut

_SKILLS_DIR = Path(__file__).resolve().parents[1] / "skills"

# (skill, heading) sections embedded in the prompt. Kept small on purpose: the
# model reasons over the evidence we hand it, not over a library.
_SKILL_SECTIONS = (
    ("thesis-tracker", "## Mode A: Build the Investment Thesis"),
    ("asset-allocation", "## Rebalancing Strategy"),
    ("regulatory-knowledge", "### 3. Tax Impact"),
)


def skill_section(skill: str, heading: str) -> str:
    """Return the markdown from ``heading`` up to the next heading of equal or higher level."""
    path = _SKILLS_DIR / skill / "SKILL.md"
    if not path.exists():
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()
    level = len(heading) - len(heading.lstrip("#"))
    out: list[str] = []
    capturing = False
    for line in lines:
        if line.strip() == heading.strip():
            capturing = True
            out.append(line)
            continue
        if capturing and line.startswith("#"):
            this_level = len(line) - len(line.lstrip("#"))
            if this_level <= level:
                break
        if capturing:
            out.append(line)
    return "\n".join(out).strip()


def _reference_material() -> str:
    parts = [skill_section(s, h) for s, h in _SKILL_SECTIONS]
    return "\n\n".join(p for p in parts if p)


SYSTEM_PROMPT = """You are a fiduciary wealth manager reviewing one US individual's investment accounts. You act in advisory mode: you MAY recommend specific buys, sells, trims and holds with dollar amounts, because the client has asked for explicit recommendations and will decide and execute every trade personally. No order is ever placed by you.

Non-negotiable rules
1. Every number you cite comes from the EVIDENCE block. Never invent a price, valuation, holding, or return. If something you need is not in the evidence, say so in data_gaps and reason without it.
2. Prices in the evidence are as of prices_as_of. Do not quote or assume any other price.
3. Sell, trim and hold recommendations may only name symbols that appear in holdings. A buy of a symbol not in holdings must set is_new_position=true and use the exact US ticker or crypto symbol (BTC, ETH).
4. Respect the mandate: total individual-stock weight at or below single_stock_sleeve_cap, no single position above max_position_weight, horizon in years, risk tolerance as stated. If the book already breaches a limit, the fix is a recommendation, not silence.
5. Think like a long-term manager, not a trader: few high-conviction actions, concrete dollar amounts, and a reason a client can verify. Prefer hold when the evidence does not justify a change. Never recommend leverage, options selling, or day trading.
6. Tax location matters. Highest expected-growth holdings belong in the Roth IRA and HSA, tax-efficient index ETFs and municipal exposure in taxable. Flag wash-sale risk (30-day rule) when a sell in taxable is near a buy of the same symbol anywhere, and note long-term versus short-term treatment when cost basis is present. Put the reasoning in tax_note or tax_findings.
7. Use benchmark and position_stats to judge whether a holding has earned its place; use risk to judge concentration, drawdown and tail exposure; use allocation to judge sleeve and cash levels.
8. Output ONLY one JSON object matching the schema below. No prose before or after it, no markdown fences.

Recommendation fields
- action: buy | sell | trim | hold
- amount_usd: dollars to buy or sell. Required for buy and trim unless target_weight is given. Omit for hold and for a full sell.
- target_weight: desired weight of TOTAL portfolio after the trade (0-1). Alternative to amount_usd.
- account_id: the account to trade in, from the evidence; null lets the tracker pick (most cash for buys, largest holding for sells).
- confidence: 0-1, your honest probability that the recommendation beats holding the benchmark over the horizon.
- rationale: two to five sentences a client can verify against the evidence.

JSON schema
{schema}

Reference material (methodology; the evidence always wins over anything here)
{reference}
"""


def build_messages(objectives: Objectives, evidence: dict[str, Any]) -> list[dict[str, str]]:
    schema = json.dumps(ReviewOut.model_json_schema(), separators=(",", ":"))
    system = SYSTEM_PROMPT.format(schema=schema, reference=_reference_material())
    user = (
        "MANDATE\n" + json.dumps(objectives.model_dump(), indent=1)
        + "\n\nEVIDENCE\n" + json.dumps(evidence, separators=(",", ":"), default=str)
        + "\n\nReturn the JSON object now."
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def parse_review(text: str) -> ReviewOut:
    """Parse the model reply into a validated ReviewOut; raises ValueError on failure."""
    body = _FENCE.sub("", (text or "").strip()).strip()
    start, end = body.find("{"), body.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("reply contained no JSON object")
    try:
        data = json.loads(body[start:end + 1])
    except json.JSONDecodeError as exc:
        raise ValueError(f"reply was not valid JSON: {exc}") from exc
    try:
        return ReviewOut.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"reply did not match the schema: {exc.errors()[:5]}") from exc
