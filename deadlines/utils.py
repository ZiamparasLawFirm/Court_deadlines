
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List

GREEK_WEEKDAYS = {0:"Δευτέρα",1:"Τρίτη",2:"Τετάρτη",3:"Πέμπτη",4:"Παρασκευή",5:"Σάββατο",6:"Κυριακή"}

@dataclass(frozen=True)
class Period:
    start: date
    end: date
    def contains(self, d: date) -> bool:
        return self.start <= d <= self.end

def daterange_excluding(start: date, days: int, excluded: List[Period]) -> date:
    d = start + timedelta(days=1)
    remaining = days
    while remaining > 0:
        if not any(p.contains(d) for p in excluded):
            remaining -= 1
            if remaining == 0:
                break
        d += timedelta(days=1)
    return d

def carry_weekend_forward(d: date) -> date:
    if d.weekday() == 5: return d + timedelta(days=2)
    if d.weekday() == 6: return d + timedelta(days=1)
    return d

def greek_weekday(d: date) -> str:
    return GREEK_WEEKDAYS[d.weekday()]
