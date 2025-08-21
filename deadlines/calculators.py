
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import List

from .utils import Period, daterange_excluding, carry_weekend_forward, greek_weekday
from .rules import RuleContext, build_exclusion_periods

@dataclass
class DeadlineItem:
    step: int
    action: str
    legal_basis: str
    deadline: date
    weekday: str
    note: str = ""

class DeadlineCalculator:
    def __init__(self, ctx: RuleContext):
        self.ctx = ctx
        self.exclusions: List[Period] = build_exclusion_periods(ctx)

    def compute(self) -> List[DeadlineItem]:
        return self._compute_regular() if self.ctx.procedure == "regular" else self._compute_small_claims()

    def _finalize(self, items: List[DeadlineItem]) -> List[DeadlineItem]:
        out: List[DeadlineItem] = []
        for it in items:
            d = carry_weekend_forward(it.deadline)
            out.append(DeadlineItem(it.step, it.action, it.legal_basis, d, greek_weekday(d), it.note))
        return out

    def _compute_regular(self) -> List[DeadlineItem]:
        ctx, ex = self.ctx, self.exclusions
        items: List[DeadlineItem] = []
        s = 1

        # 1) Service (215 §2): 30/60 from filing
        sd = daterange_excluding(ctx.filing_date, 60 if ctx.defendant_abroad_or_unknown else 30, ex)
        items.append(DeadlineItem(s, "Επίδοση αγωγής", "ΚΠολΔ 215 §2", sd, "", "Μη εμπρόθεσμη επίδοση: αγωγή μη ασκηθείσα"))
        s += 1

        # 2) Proposals (237): 90/120 from end of service period
        pd = daterange_excluding(sd, 120 if ctx.defendant_abroad_or_unknown else 90, ex)
        items.append(DeadlineItem(s, "Προτάσεις & αποδεικτικά", "ΚΠολΔ 237", pd, "", "Λήξη 12:00"))
        s += 1

        # 3) Addition (237 §2): +15
        ad = daterange_excluding(pd, 15, ex)
        items.append(DeadlineItem(s, "Προσθήκη–αντίκρουση", "ΚΠολΔ 237 §2", ad, "", "Λήξη 12:00"))
        s += 1

        # 4) Ancillary deposit & service (238 §1): 60/90 from filing
        anc1 = daterange_excluding(ctx.filing_date, 90 if ctx.defendant_abroad_or_unknown else 60, ex)
        items.append(DeadlineItem(s, "Παρεμπίπτουσες – κατάθεση & επίδοση", "ΚΠολΔ 238 §1", anc1, ""))
        s += 1

        # 5) Ancillary proposals (238 §1 last): 120/180 from filing
        anc2 = daterange_excluding(ctx.filing_date, 180 if ctx.defendant_abroad_or_unknown else 120, ex)
        items.append(DeadlineItem(s, "Προτάσεις επί παρεμπιπτουσών", "ΚΠολΔ 238 §1 (τελ.)", anc2, "", "Λήξη 12:00"))
        s += 1

        # 6) Ancillary addition: +15
        anc3 = daterange_excluding(anc2, 15, ex)
        items.append(DeadlineItem(s, "Προσθήκη–αντίκρουση επί παρεμπιπτουσών", "ΚΠολΔ 238 §1 → 237 §2", anc3, "", "Λήξη 12:00"))

        return self._finalize(items)

    def _compute_small_claims(self) -> List[DeadlineItem]:
        ctx, ex = self.ctx, self.exclusions
        items: List[DeadlineItem] = []
        s = 1

        # 1) Service (468 §1): 10/30 from filing
        sd = daterange_excluding(ctx.filing_date, 30 if ctx.defendant_abroad_or_unknown else 10, ex)
        items.append(DeadlineItem(s, "Επίδοση αγωγής", "ΚΠολΔ 468 §1", sd, ""))
        s += 1

        # 2) Memo & evidence (468 §2): 20 from end of service period
        md = daterange_excluding(sd, 20, ex)
        items.append(DeadlineItem(s, "Υπόμνημα εναγομένου & αποδεικτικά", "ΚΠολΔ 468 §2", md, ""))
        s += 1

        # 3) Addition (468 §2): +5
        ad = daterange_excluding(md, 5, ex)
        items.append(DeadlineItem(s, "Προσθήκη–αντίκρουση", "ΚΠολΔ 468 §2", ad, ""))
        s += 1

        # 4) Ancillary deposit & service (468 §3): 20/40 from filing
        anc1 = daterange_excluding(ctx.filing_date, 40 if ctx.defendant_abroad_or_unknown else 20, ex)
        items.append(DeadlineItem(s, "Παρεμπίπτουσες – κατάθεση & επίδοση", "ΚΠολΔ 468 §3", anc1, ""))
        s += 1

        # 5) Ancillary memo & evidence (468 §3): 30/50 from filing
        anc2 = daterange_excluding(ctx.filing_date, 50 if ctx.defendant_abroad_or_unknown else 30, ex)
        items.append(DeadlineItem(s, "Αποδεικτικά & υπόμνημα επί παρεμπιπτουσών", "ΚΠολΔ 468 §3", anc2, ""))
        s += 1

        # 6) Ancillary addition: +5
        anc3 = daterange_excluding(anc2, 5, ex)
        items.append(DeadlineItem(s, "Προσθήκη–αντίκρουση επί παρεμπιπτουσών", "ΚΠολΔ 468 §3 → §2", anc3, ""))

        return self._finalize(items)
