
# -*- coding: utf-8 -*-
"""
deadlines.rules
Core deadline computation for Τακτική & Μικροδιαφορές.
Fix: For small-claims 468 §2 the 20 days anchor to the rolled expiry of service under 468 §1.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import List

WEEKDAYS_GR = ["Δευτέρα","Τρίτη","Τετάρτη","Πέμπτη","Παρασκευή","Σάββατο","Κυριακή"]

@dataclass
class RuleContext:
    filing_date: date
    defendant_abroad_or_unknown: bool = False
    public_entity_party: bool = False
    procedure: str = "regular"  # "regular" or "small_claims"

@dataclass
class DeadlineItem:
    index: int
    action: str
    legal_basis: str
    deadline: date
    weekday: str
    notes: str = ""

# -----------------------------
# Suspension & helpers
# -----------------------------

def _in_public_suspension(d: date) -> bool:
    y = d.year
    return date(y, 7, 1) <= d <= date(y, 9, 15)

def _in_august(d: date) -> bool:
    return d.month == 8

def _is_suspended(d: date, ctx: RuleContext) -> bool:
    if _in_august(d):
        return True
    if ctx.public_entity_party and _in_public_suspension(d):
        return True
    return False

def _roll_to_next_business_day(d: date, ctx: RuleContext) -> date:
    # Move forward if Saturday/Sunday or inside suspension window
    res = d
    while res.weekday() >= 5 or _is_suspended(res, ctx):
        res += timedelta(days=1)
    return res

def add_procedural_days(base: date, days: int, ctx: RuleContext, start_from_next_day: bool = True) -> date:
    """
    Add `days` procedural days to `base`, skipping suspended days (Aug and, if public, 1/7–15/9).
    Start count from next day (144 ΚΠολΔ) by default.
    Always roll forward to next business (non-weekend, non-suspended) day.
    """
    cur = base + timedelta(days=1) if start_from_next_day else base
    remaining = days
    while remaining > 0:
        if not _is_suspended(cur, ctx):
            remaining -= 1
        cur += timedelta(days=1)
    res = cur - timedelta(days=1)
    # Roll forward if end on weekend or suspended day
    if res.weekday() >= 5 or _is_suspended(res, ctx):
        res = _roll_to_next_business_day(res, ctx)
    return res

# -----------------------------
# Regular procedure
# -----------------------------

def _regular_deadlines(ctx: RuleContext) -> List[DeadlineItem]:
    items: List[DeadlineItem] = []
    i = 1

    # 1) Επίδοση αγωγής — 215 §2 (30/60 από κατάθεση)
    days_service = 60 if ctx.defendant_abroad_or_unknown else 30
    d1 = add_procedural_days(ctx.filing_date, days_service, ctx, start_from_next_day=True)
    items.append(DeadlineItem(i, "Επίδοση αγωγής στον εναγόμενο", "ΚΠολΔ 215 §2", d1, WEEKDAYS_GR[d1.weekday()])); i += 1

    # 2) Προτάσεις — 237 (90/120 από ΛΗΞΗ προθεσμίας επίδοσης)
    days_proposals = 120 if ctx.defendant_abroad_or_unknown else 90
    d2 = add_procedural_days(d1, days_proposals, ctx, start_from_next_day=True)
    items.append(DeadlineItem(i, "Κατάθεση προτάσεων & αποδεικτικών", "ΚΠολΔ 237", d2, WEEKDAYS_GR[d2.weekday()])); i += 1

    # 3) Προσθήκη–αντίκρουση — 237 §2 (+15)
    d3 = add_procedural_days(d2, 15, ctx, start_from_next_day=True)
    items.append(DeadlineItem(i, "Προσθήκη–αντίκρουση", "ΚΠολΔ 237 §2", d3, WEEKDAYS_GR[d3.weekday()])); i += 1

    # 4) Παρεμπίπτουσες — 238 §1 (60/90 από κατάθεση)
    days_inc = 90 if ctx.defendant_abroad_or_unknown else 60
    d4 = add_procedural_days(ctx.filing_date, days_inc, ctx, start_from_next_day=True)
    items.append(DeadlineItem(i, "Παρεμπίπτουσες: κατάθεση & επίδοση", "ΚΠολΔ 238 §1", d4, WEEKDAYS_GR[d4.weekday()])); i += 1

    # 5) Ενδεικτικά
    days_prop_inc = 180 if ctx.defendant_abroad_or_unknown else 120
    d5 = add_procedural_days(d4, days_prop_inc, ctx, start_from_next_day=True)
    items.append(DeadlineItem(i, "Προτάσεις επί παρεμπιπτουσών (ενδεικτικό)", "ΚΠολΔ 237 (κατ’ αναλογία)", d5, WEEKDAYS_GR[d5.weekday()])); i += 1

    d6 = add_procedural_days(d5, 15, ctx, start_from_next_day=True)
    items.append(DeadlineItem(i, "Προσθήκη–αντίκρουση επί παρεμπιπτουσών (ενδεικτικό)", "ΚΠολΔ 237 §2 (κατ’ αναλογία)", d6, WEEKDAYS_GR[d6.weekday()]))

    return items

# -----------------------------
# Small claims (Μικροδιαφορές)
# -----------------------------

def _small_claims_deadlines(ctx: RuleContext) -> List[DeadlineItem]:
    items: List[DeadlineItem] = []
    i = 1

    # 1) Επίδοση αγωγής — 468 §1 (10/30 από κατάθεση)
    days_service = 30 if ctx.defendant_abroad_or_unknown else 10
    d1 = add_procedural_days(ctx.filing_date, days_service, ctx, start_from_next_day=True)
    d1 = _roll_to_next_business_day(d1, ctx)  # ensure legal expiry anchor
    items.append(DeadlineItem(i, "Επίδοση αγωγής στον εναγόμενο", "ΚΠολΔ 468 §1", d1, WEEKDAYS_GR[d1.weekday()])); i += 1

    # 2) Υπόμνημα εναγομένου & αποδεικτικά — 468 §2 (20 από τη λήξη της επίδοσης)
    d2 = add_procedural_days(d1, 20, ctx, start_from_next_day=True)
    items.append(DeadlineItem(i, "Υπόμνημα εναγομένου & αποδεικτικά", "ΚΠολΔ 468 §2", d2, WEEKDAYS_GR[d2.weekday()])); i += 1

    # 3) Προσθήκη–αντίκρουση — +5 από λήξη 20ημέρου
    d3 = add_procedural_days(d2, 5, ctx, start_from_next_day=True)
    items.append(DeadlineItem(i, "Προσθήκη–αντίκρουση", "ΚΠολΔ 468 §2", d3, WEEKDAYS_GR[d3.weekday()])); i += 1

    # 4) Παρεμπίπτουσες — 468 §3 (20/40 από κατάθεση)
    days_inc = 40 if ctx.defendant_abroad_or_unknown else 20
    d4 = add_procedural_days(ctx.filing_date, days_inc, ctx, start_from_next_day=True)
    items.append(DeadlineItem(i, "Παρεμπίπτουσες: κατάθεση & επίδοση", "ΚΠολΔ 468 §3", d4, WEEKDAYS_GR[d4.weekday()])); i += 1

    # 5–6) Ενδεικτικά
    days_memo_inc = 50 if ctx.defendant_abroad_or_unknown else 30
    d5 = add_procedural_days(d4, days_memo_inc, ctx, start_from_next_day=True)
    items.append(DeadlineItem(i, "Υπόμνημα επί παρεμπιπτουσών (ενδεικτικό)", "ΚΠολΔ 468 §3 (κατ’ αναλογία §2)", d5, WEEKDAYS_GR[d5.weekday()])); i += 1

    d6 = add_procedural_days(d5, 5, ctx, start_from_next_day=True)
    items.append(DeadlineItem(i, "Προσθήκη επί παρεμπιπτουσών (ενδεικτικό)", "ΚΠολΔ 468 §2 (κατ’ αναλογία)", d6, WEEKDAYS_GR[d6.weekday()]))

    return items

# -----------------------------
# Public API
# -----------------------------

class DeadlineCalculator:
    def __init__(self, ctx: RuleContext):
        self.ctx = ctx

    def compute(self) -> List[DeadlineItem]:
        if self.ctx.procedure == "regular":
            return _regular_deadlines(self.ctx)
        if self.ctx.procedure == "small_claims":
            return _small_claims_deadlines(self.ctx)
        raise ValueError("Unknown procedure: expected 'regular' or 'small_claims'")
