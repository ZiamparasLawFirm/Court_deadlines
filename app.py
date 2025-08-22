# -*- coding: utf-8 -*-
import os, sys, shutil
from datetime import date, timedelta
import streamlit as st

# ΠΡΩΤΗ κλήση Streamlit
st.set_page_config(page_title="Greek Civil Deadlines (PyCharm)", page_icon="⚖️", layout="centered")

from deadlines import DeadlineCalculator, DeadlineItem
from deadlines.rules import RuleContext
from deadlines.pdf import GREEK_FONT_PATH

# -----------------------------
# Greek-capable font for PDF
# -----------------------------
def _ensure_greek_font_available():
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    os.makedirs(assets_dir, exist_ok=True)
    target = GREEK_FONT_PATH
    if os.path.exists(target):
        return
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode MS.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Tahoma.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "/Library/Fonts/Arial Unicode MS.ttf",
        "/Library/Fonts/Arial.ttf",
        "/Library/Fonts/Tahoma.ttf",
        os.path.expanduser("~/Library/Fonts/Arial Unicode.ttf"),
        os.path.expanduser("~/Library/Fonts/Arial.ttf"),
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                shutil.copyfile(c, target)
                break
            except Exception:
                pass

_ensure_greek_font_available()

# -----------------------------
# Global CSS (με creative "chip" κουμπιά)
# -----------------------------
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] * { font-size: 20px !important; }

/* Τίτλοι */
h1.big-title { font-size: 2.4rem !important; line-height: 1.18 !important; margin: 0 0 0.25rem 0 !important; }
p.subnote { font-size: 1.0rem !important; color: #444; margin: 0 0 1.0rem 0 !important; }

/* Default buttons (π.χ. PDF) */
.stButton > button {
  font-size: 16px !important;
  padding: 0.50rem 0.90rem !important;
  font-weight: 600;
  width: 100%;
}

/* Κύριο CTA */
button[data-testid="baseButton-primary"] {
  font-size: 20px !important;
  font-weight: 800 !important;
  padding: 0.75rem 1.6rem !important;
}

/* === Creative "Chip" buttons για τις γραμμές === */
.chip-col { display:flex; align-items:center; }
.chip-col--left { justify-content:flex-start; }
.chip-col--right { justify-content:flex-end; }

/* Βασικό στυλ κουμπιών-πινακίδων */
.chip-col .stButton > button {
  width: auto !important;
  font-size: 11px !important;         /* μικρότερα από τη γραμμή */
  font-weight: 800 !important;
  letter-spacing: .2px;
  padding: 0.22rem 0.55rem !important; /* compact */
  border-radius: 9999px !important;    /* full pill */
  border: 1px solid #d0d7de !important;
  background: linear-gradient(180deg,#ffffff,#f6f8fa) !important;
  color: #0a0a0a !important;
  box-shadow: 0 1px 0 rgba(0,0,0,.04), inset 0 -1px 0 rgba(0,0,0,.03) !important;
  transition: transform .08s ease, box-shadow .15s ease, background .15s ease;
  white-space: nowrap !important;
  line-height: 1.1 !important;
}

/* Hover effects */
.chip-col .stButton > button:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(0,0,0,.10);
}

/* Εξειδίκευση ανά κουμπί */
.chip-calc .stButton > button {
  border-color: #b6d3ff !important;
  background: linear-gradient(180deg,#f7fbff,#eaf3ff) !important;
}
.chip-calc .stButton > button:hover {
  background: linear-gradient(180deg,#e9f3ff,#d7e9ff) !important;
}

.chip-law .stButton > button {
  border-color: #d1c4f3 !important;
  background: linear-gradient(180deg,#fbf9ff,#f3f0ff) !important;
}
.chip-law .stButton > button:hover {
  background: linear-gradient(180deg,#eee9ff,#e5deff) !important;
}

/* Κατάσταση ενεργό (όταν είναι ανοικτή η επεξήγηση) */
.chip-calc.active .stButton > button {
  background: linear-gradient(180deg,#3b82f6,#1d4ed8) !important;
  color: #fff !important;
  border-color: #1e40af !important;
}
.chip-law.active .stButton > button {
  background: linear-gradient(180deg,#8b5cf6,#6d28d9) !important;
  color: #fff !important;
  border-color: #5b21b6 !important;
}

/* Διακριτικές ετικέτες emoji μέσα στο κουμπί */
.chip-col .stButton > button span.emoji {
  filter: saturate(120%);
  margin-right: .35rem;
}

/* Διαχωριστικές γραμμές του πίνακα */
hr { margin: 0.5rem 0; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Title + subnote
# -----------------------------
st.markdown('<h1 class="big-title">⚖️ Υπολογισμός Προθεσμιών ΚΠολΔ — Τακτική & Μικροδιαφορές</h1>', unsafe_allow_html=True)
st.markdown('<p class="subnote">(Με το νομοθετικό πλαίσιο μέχρι 31-12-2025)</p>', unsafe_allow_html=True)

with st.expander("Πληροφορίες", expanded=False):
    st.markdown("""
- **Αναστολή Αυγούστου (1–31/8)** και, αν υπάρχει **Δημόσιο/ΝΠΔΔ**, επιπλέον **1/7–15/9**.
- Μεταφορά λήξης που πέφτει **Σ/Κ** στην **επόμενη εργάσιμη**.
- **Τακτική**: 215(30/60), 237(90/120 από λήξη επίδοσης +15), 238(60/90 & 120/180 +15).
- **Μικροδιαφορές**: 468 → 10/30, μετά 20 + 5· Παρεμπίπτουσες 20/40 + 30/50 + 5.
- Για ελληνικές ονομασίες μηνών/ημερών και εβδομάδα που **ξεκινά Δευτέρα**, το ημερολόγιο του browser καθορίζει τη γλώσσα/έναρξη εβδομάδας.
""")

# -----------------------------
# Helpers
# -----------------------------
def _next_monday(d: date) -> date:
    while d.weekday() >= 5:  # 5=Σάββατο, 6=Κυριακή
        d += timedelta(days=1)
    return d

_default_filing = _next_monday(date.today())

# -----------------------------
# Date widget state orchestration (χωρίς conflicts)
# -----------------------------
# 1) Πρώτη φορά: αρχικοποίηση πριν δημιουργηθεί το widget
if "filing_date_widget" not in st.session_state:
    st.session_state["filing_date_widget"] = _default_filing

# 2) Αν εκκρεμεί διόρθωση από προηγούμενο run (επιλέχθηκε Σ/Κ):
if st.session_state.get("pending_adjust", False):
    adj = st.session_state.get("pending_adjust_value", None)
    if isinstance(adj, date):
        st.session_state["filing_date_widget"] = adj
        st.session_state["filing_adjusted_note"] = f"Επιλέχθηκε Σ/Κ. Η ημερομηνία κατάθεσης μεταφέρθηκε αυτόματα στη **Δευτέρα {adj:%d-%m-%Y}**."
    st.session_state["pending_adjust"] = False
    st.session_state.pop("pending_adjust_value", None)

# -----------------------------
# Inputs (παλιός datepicker, ΧΩΡΙΣ value=..., μόνο key)
# -----------------------------
c1, c2 = st.columns(2)
with c1:
    abroad = st.selectbox("1) Εναγόμενος εξωτερικού/αγνώστου;", ["Όχι","Ναι"])=="Ναι"
    public = st.selectbox("2) Υπάρχει Δημόσιο/ΝΠΔΔ διάδικος;", ["Όχι","Ναι"])=="Ναι"
with c2:
    procedure = st.selectbox("3) Διαδικασία;", ["Τακτική","Μικροδιαφορές"])
    filing = st.date_input(
        "4) Ημερομηνία κατάθεσης αγωγής",
        format="DD/MM/YYYY",
        key="filing_date_widget"  # ΔΕΝ δίνουμε value=...
    )

# 3) Αν επιλέχθηκε Σ/Κ, προγραμμάτισε Δευτέρα για το επόμενο run ΧΩΡΙΣ να πειράξεις το widget key τώρα
if filing.weekday() >= 5:
    adjusted = _next_monday(filing)
    if adjusted != filing:
        st.session_state["pending_adjust"] = True
        st.session_state["pending_adjust_value"] = adjusted
        st.rerun()

# 4) Μήνυμα ενημέρωσης (εμφανίζεται στο run μετά τη διόρθωση)
note = st.session_state.pop("filing_adjusted_note", None)
if note:
    st.info(note)

# «Καθαρή» ημερομηνία για υπολογισμούς (είναι εργάσιμη πλέον)
sanitized_filing = st.session_state["filing_date_widget"]

# Invalidate results on input change
sig = (abroad, public, procedure, sanitized_filing)
if "last_sig" not in st.session_state:
    st.session_state["last_sig"] = sig
    st.session_state["rows"] = None
elif st.session_state["last_sig"] != sig:
    st.session_state["last_sig"] = sig
    st.session_state["rows"] = None

# -----------------------------
# Compute
# -----------------------------
compute_pressed = st.button("Υπολογισμός", type="primary")

if compute_pressed:
    ctx = RuleContext(
        filing_date=sanitized_filing,
        defendant_abroad_or_unknown=abroad,
        public_entity_party=public,
        procedure="regular" if procedure=="Τακτική" else "small_claims",
    )
    calc = DeadlineCalculator(ctx)
    rows_full = calc.compute()
    # Κόβουμε οριστικά τις 2 τελευταίες γραμμές (και από πίνακα και από PDF)
    rows = rows_full[:-2] if len(rows_full) >= 2 else rows_full
    st.session_state["rows"] = rows
else:
    rows = st.session_state.get("rows", None)

# -----------------------------
# Helpers (κειμενικά)
# -----------------------------
def _explain_calc_text(it, rows_all):
    lb = it.legal_basis
    end_str = it.deadline.strftime("%d-%m-%Y")
    weekday = it.weekday
    if "215" in lb:
        n = 60 if abroad else 30
        return f"Από την κατάθεση ({sanitized_filing:%d-%m-%Y}) + **{n} ημέρες**, εξαιρώντας **Αύγουστο**{', και **1/7–15/9**' if public else ''}. Αν πέσει Σ/Κ, μεταφορά σε εργάσιμη. Τελική: **{weekday} {end_str}**."
    if lb.startswith("ΚΠολΔ 237") and "§2" not in lb:
        n = 120 if abroad else 90
        service = rows_all[0].deadline
        return f"Από τη **λήξη επίδοσης** ({service:%d-%m-%Y}) + **{n} ημέρες**, ίδιες εξαιρέσεις· **λήξη 12:00**. Τελική: **{weekday} {end_str}**."
    if "237 §2" in lb:
        return f"**+15 ημέρες** από την προθεσμία προτάσεων ({rows_all[1].deadline:%d-%m-%Y}); **λήξη 12:00**. Τελική: **{weekday} {end_str}**."
    if "238 §1" in lb and "τελ" not in lb:
        n = 90 if abroad else 60
        return f"Παρεμπίπτουσες: από **κατάθεση** ({sanitized_filing:%d-%m-%Y}) + **{n} ημέρες**. Τελική: **{weekday} {end_str}**."
    if "468 §1" in lb:
        n = 30 if abroad else 10
        return f"Μικροδιαφορές: από κατάθεση ({sanitized_filing:%d-%m-%Y}) + **{n} ημέρες**. Τελική: **{weekday} {end_str}**."
    if "468 §2" in lb and "Υπόμνημα" in it.action:
        return f"Μικροδιαφορές: **20 ημέρες** από τη **λήξη επίδοσης** ({rows_all[0].deadline:%d-%m-%Y}). Τελική: **{weekday} {end_str}**."
    if "468 §2" in lb and "Προσθήκη" in it.action:
        return f"Μικροδιαφορές: **+5 ημέρες** από το 20ήμερο ({rows_all[1].deadline:%d-%m-%Y}). Τελική: **{weekday} {end_str}**."
    if "468 §3" in lb and "κατάθεση" in it.action:
        n = 40 if abroad else 20
        return f"Μικροδιαφορές — παρεμπίπτουσες: από κατάθεση ({sanitized_filing:%d-%m-%Y}) + **{n} ημέρες**. Τελική: **{weekday} {end_str}**."
    return f"Υπολογισμός βάσει **{lb}**. Τελική: **{weekday} {end_str}**."

def _law_text(it):
    lb = it.legal_basis
    if "215" in lb:
        return "ΚΠολΔ **215 §2** — Επίδοση αγωγής εντός **30** ημερών (**60** αν εξωτερικού/αγνώστου). Μη εμπρόθεσμη επίδοση: αγωγή **μη ασκηθείσα**."
    if lb.startswith("ΚΠολΔ 237") and "§2" not in lb:
        return "ΚΠολΔ **237** — Προτάσεις & αποδεικτικά **90** ημέρες (**120** αν εξωτερικού/αγνώστου) **από τη λήξη της προθεσμίας επίδοσης**. Λήξη **12:00**."
    if "237 §2" in lb:
        return "ΚΠολΔ **237 §2** — **Προσθήκη–αντίκρουση** **15** ημέρες μετά την προθεσμία προτάσεων. Λήξη **12:00**."
    if "238 §1" in lb and "τελ" not in lb:
        return "ΚΠολΔ **238 §1** — Παρεμπίπτουσες: κατάθεση & επίδοση **60** ημέρες (**90** αν εξωτερικού/αγνώστου) από **κατάθεση αγωγής**."
    if "468 §1" in lb:
        return "ΚΠολΔ **468 §1** — Επίδοση αγωγής μικροδιαφορών **10** ημέρες (**30** αν εξωτερικού/αγνώστου) από κατάθεση."
    if "468 §2" in lb and "Υπόμνημα" in it.action:
        return "ΚΠολΔ **468 §2** — **Υπόμνημα εναγομένου & αποδεικτικά** **20** ημέρες από τη **λήξη προθεσμίας επίδοσης**."
    if "468 §2" in lb and "Προσθήκη" in it.action:
        return "ΚΠολΔ **468 §2** — **Προσθήκη–αντίκρουση** **5** ημέρες μετά το 20ήμερο."
    if "468 §3" in lb and "κατάθεση" in it.action:
        return "ΚΠολΔ **468 §3** — Παρεμπίπτουσες: κατάθεση & επίδοση **20** ημέρες (**40** αν εξωτερικού/αγνώστου) από κατάθεση."
    return f"Σχετική νομοθεσία: **{lb}**."

# -----------------------------
# Full list για επεξηγήσεις (δεν κόβουμε εδώ)
# -----------------------------
def _compute_full_for_explanations():
    ctx_tmp = RuleContext(
        filing_date=sanitized_filing,
        defendant_abroad_or_unknown=abroad,
        public_entity_party=public,
        procedure="regular" if procedure=="Τακτική" else "small_claims",
    )
    return DeadlineCalculator(ctx_tmp).compute()

# -----------------------------
# Results table
# -----------------------------
if not rows:
    st.info("Πατήστε **Υπολογισμός** για να υπολογιστούν οι προθεσμίες.")
else:
    st.success("Υπολογισμός ολοκληρώθηκε.")
    # Headers: ΕΝΕΡΓΕΙΕΣ | ΠΡΟΘΕΣΜΙΕΣ | [Τρόπος] | [Νομική Βάση]
    hdr = st.columns([6, 3, 2, 2])
    with hdr[0]: st.markdown("**ΕΝΕΡΓΕΙΕΣ**")
    with hdr[1]: st.markdown("**ΠΡΟΘΕΣΜΙΕΣ**")
    with hdr[2]: st.markdown("&nbsp;", unsafe_allow_html=True)
    with hdr[3]: st.markdown("&nbsp;", unsafe_allow_html=True)

    rows_full_for_calc = _compute_full_for_explanations()

    for i, it in enumerate(rows):
        disp_action = it.action
        if "προτάσε" in disp_action.lower(): disp_action = "Κατάθεση Προτάσεων"
        if "προσθήκ" in disp_action.lower(): disp_action = "Κατάθεση Προσθήκης-Αντίκρουσης"
        if "παρεμπίπτουσ" in disp_action.lower(): disp_action = "Άσκηση Παρέμβασης, Ανταγωγής κτλ"

        # Ενεργές καταστάσεις για styling (όταν είναι ανοιχτές οι εξηγήσεις)
        calc_open = st.session_state.get(f"show_calc_{i}", False)
        law_open  = st.session_state.get(f"show_law_{i}", False)

        row = st.columns([6, 3, 2, 2], vertical_alignment="center")
        with row[0]:
            st.markdown(f"**{i+1}. {disp_action}**")
        with row[1]:
            st.markdown(f"**{it.weekday} {it.deadline:%d-%m-%Y}**")

        # --- Creative "chip" κουμπί Τρόπος Υπολογισμού (αριστερά)
        with row[2]:
            st.markdown(
                f'<div class="chip-col chip-col--left chip-calc {"active" if calc_open else ""}">',
                unsafe_allow_html=True
            )
            if st.button("🧮 Τρόπος Υπολογισμού", key=f"calc_btn_{i}", help="Δείξε/κρύψε τον τρόπο υπολογισμού"):
                st.session_state[f"show_calc_{i}"] = not calc_open
            st.markdown('</div>', unsafe_allow_html=True)

        # --- Creative "chip" κουμπί Νομική Βάση (δεξιά)
        with row[3]:
            st.markdown(
                f'<div class="chip-col chip-col--right chip-law {"active" if law_open else ""}">',
                unsafe_allow_html=True
            )
            if st.button("📜 Νομική Βάση", key=f"law_btn_{i}", help="Δείξε/κρύψε τη νομική βάση"):
                st.session_state[f"show_law_{i}"] = not law_open
            st.markdown('</div>', unsafe_allow_html=True)

        # Περιοχή επεξηγήσεων (ανοίγει κάτω από τη γραμμή)
        if st.session_state.get(f"show_calc_{i}", False) or st.session_state.get(f"show_law_{i}", False):
            with st.container():
                if st.session_state.get(f"show_calc_{i}", False):
                    st.info(_explain_calc_text(it, rows_full_for_calc), icon="ℹ️")
                if st.session_state.get(f"show_law_{i}", False):
                    st.code(_law_text(it), language="markdown")
        st.markdown("<hr/>", unsafe_allow_html=True)

# -----------------------------
# PDF (ΜΟΝΟ τα εμφανιζόμενα rows)
# -----------------------------
st.subheader("📄 Εξαγωγή σε PDF (μόνο αποθήκευση σε Downloads)")
client = st.text_input("Πελάτης (προαιρετικό)", key="client_input")
opponent = st.text_input("Αντίδικος (προαιρετικό)", key="opponent_input")

def _make_pdf_custom(path: str, title: str, meta: dict, rows_list):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import os

    font_name = "DejaVuSans"
    try:
        if os.path.exists(GREEK_FONT_PATH) and "DejaVuSans" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("DejaVuSans", GREEK_FONT_PATH))
    except Exception:
        font_name = "Helvetica"

    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    margin = 16 * mm
    x = margin
    y = height - margin

    c.setFont(font_name, 18)
    c.drawString(x, y, title); y -= 10 * mm

    c.setFont(font_name, 12)
    c.drawString(x, y, f"Πελάτης: {meta.get('client','-')}"); y -= 6 * mm
    c.drawString(x, y, f"Αντίδικος: {meta.get('opponent','-')}"); y -= 8 * mm

    c.setFont(font_name, 11)
    c.drawString(x, y, f"Ημερομηνία Κατάθεσης: {meta.get('filing','-')}"); y -= 6 * mm
    c.drawString(x, y, f"Διαδικασία: {meta.get('procedure','-')}"); y -= 6 * mm
    c.drawString(x, y, f"Εναγόμενος Εξωτερικού/Αγνώστου: {meta.get('abroad','-')}"); y -= 6 * mm
    c.drawString(x, y, f"Διάδικος Δημόσιο: {meta.get('public','-')}"); y -= 10 * mm

    headers = ["#", "ΕΝΕΡΓΕΙΕΣ", "Νομική Βάση", "ΠΡΟΘΕΣΜΙΕΣ"]
    col_widths = [10*mm, 88*mm, 35*mm, 45*mm]

    c.setFont(font_name, 12)
    c.rect(x, y-8*mm, sum(col_widths), 8*mm, stroke=1, fill=0)
    cx = x + 2
    for i, h in enumerate(headers):
        c.drawString(cx, y-6*mm, h)
        cx += col_widths[i]
    y -= 8*mm

    c.setFont(font_name, 11)
    for idx, it in enumerate(rows_list, start=1):
        if y < margin + 25*mm:
            c.showPage(); y = height - margin
            c.setFont(font_name, 12)
            c.rect(x, y-8*mm, sum(col_widths), 8*mm, stroke=1, fill=0)
            cx = x + 2
            for i, h in enumerate(headers):
                c.drawString(cx, y-6*mm, h)
                cx += col_widths[i]
            y -= 8*mm
            c.setFont(font_name, 11)
        c.rect(x, y-12*mm, sum(col_widths), 12*mm, stroke=1, fill=0)
        cx = x + 2

        disp_action = it.action
        if "προτάσε" in disp_action.lower(): disp_action = "Κατάθεση Προτάσεων"
        if "προσθήκ" in disp_action.lower(): disp_action = "Κατάθεση Προσθήκης-Αντίκρουσης"
        if "παρεμπίπτουσ" in disp_action.lower(): disp_action = "Άσκηση Παρέμβασης, Ανταγωγής κτλ"

        vals = [
            str(idx),
            disp_action,
            it.legal_basis,
            f"{it.weekday} {it.deadline.strftime('%d-%m-%Y')}",
        ]
        for i, v in enumerate(vals):
            c.drawString(cx, y-8*mm, v[:80])
            cx += col_widths[i]
        y -= 12*mm

    c.setFont(font_name, 9)
    c.drawString(x, margin, "Generated with Greek Civil Deadlines Web App")
    c.save()

if st.button("Αποθήκευση PDF στο Downloads"):
    rows = st.session_state.get("rows", None)
    if not rows:
        st.warning("Δεν υπάρχουν αποτελέσματα. Πάτησε πρώτα **Υπολογισμός**.")
    else:
        pdf_items = []
        for idx, it in enumerate(rows, start=1):
            pdf_items.append(DeadlineItem(idx, it.action, it.legal_basis, it.deadline, it.weekday, ""))

        downloads = os.path.expanduser("~/Downloads")
        os.makedirs(downloads, exist_ok=True)
        client = st.session_state.get("client_input", "")
        opponent = st.session_state.get("opponent_input", "")
        fname = f"Προθεσμίες Αγωγής {client.strip() or 'Χωρίς_Όνομα'} vs {opponent.strip() or 'Χωρίς_Όνομα'}.pdf"
        path = os.path.join(downloads, fname)

        meta = {
            "client": client,
            "opponent": opponent,
            "filing": sanitized_filing.strftime("%d-%m-%Y"),
            "procedure": procedure,
            "abroad": "Ναι" if abroad else "Όχι",
            "public": "Ναι" if public else "Όχι",
        }
        _make_pdf_custom(path, "Πίνακας Προθεσμιών", meta, pdf_items)

        st.success(f"Το PDF αποθηκεύτηκε στον φάκελο **Downloads** ως: `{fname}`")
        st.info(f"Πλήρης διαδρομή: `{path}`")

# -----------------------------
# PyCharm bootstrap guard (τρέχει αυτόματα Streamlit)
# -----------------------------
if __name__ == "__main__":
    if (os.environ.get("STREAMLIT_BOOTSTRAPPED") != "1") and all("streamlit" not in arg for arg in sys.argv):
        os.environ["STREAMLIT_BOOTSTRAPPED"] = "1"
        from streamlit.web import cli as stcli
        sys.argv = ["streamlit", "run", os.path.abspath(__file__)]
        stcli.main()
