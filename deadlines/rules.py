
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import List
from .utils import Period

@dataclass
class RuleContext:
    filing_date: date
    defendant_abroad_or_unknown: bool
    public_entity_party: bool
    procedure: str  # 'regular' or 'small_claims'

def august_suspension_periods(year: int) -> List[Period]:
    return [Period(date(year,8,1), date(year,8,31))]

def state_vacation_periods(year: int) -> List[Period]:
    return [Period(date(year,7,1), date(year,9,15))]

def build_exclusion_periods(ctx: RuleContext) -> List[Period]:
    ex: List[Period] = []
    y0 = ctx.filing_date.year
    for y in (y0, y0+1, y0+2):
        ex.extend(august_suspension_periods(y))
        if ctx.public_entity_party:
            ex.extend(state_vacation_periods(y))
    return ex
