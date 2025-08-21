
# -*- coding: utf-8 -*-
import os, sys, shutil
from datetime import date
import streamlit as st

# First Streamlit call
st.set_page_config(page_title="Greek Civil Deadlines (PyCharm)", page_icon="⚖️", layout="centered")

from deadlines import DeadlineCalculator, DeadlineItem
from deadlines.rules import RuleContext
from deadlines.pdf import GREEK_FONT_PATH

# -----------------------------
# Ensure Greek PDF font
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
# Global CSS (title size, base font, and button-specific sizes)
# -----------------------------
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] * { font-size: 20px !important; }
h1.big-title { font-size: 2.6rem !important; line-height: 1.18 !important; margin: 0 0 0.25rem 0 !important; }
p.subnote { font-size: 1.0rem !important; color: #444; margin: 0 0 1.0rem 0 !important; }

/* Default: make Streamlit buttons slightly smaller than base text */
.stButton > button {
  font-size: 16px !important;
  padding-top: 0.65rem; padding-bottom: 0.65rem;
  padding-left: 1.2rem; padding-right: 1.2rem;
  font-weight: 600;
  width: 100%;
}

/* Keep the main CTA ("Υπολογισμός") large and prominent */
button[data-testid="baseButton-primary"] {
  font-size: 20px !important;
  font-weight: 800 !important;
  padding-top: 0.75rem !important; padding-bottom: 0.75rem !important;
  padding-left: 1.6rem !important; padding-right: 1.6rem !important;
}

hr { margin: 0.7rem 0; }
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
""")

# -----------------------------
# Inputs (compute only on button; filing defaults to today)
# -----------------------------
c1, c2 = st.columns(2)
with c1:
    abroad = st.selectbox("1) Εναγόμενος εξωτερικού/αγνώστου;", ["Όχι","Ναι"])=="Ναι"
    public = st.selectbox("2) Υπάρχει Δημόσιο/ΝΠΔΔ διάδικος;", ["Όχι","Ναι"])=="Ναι"
with c2:
    procedure = st.selectbox("3) Διαδικασία;", ["Τακτική","Μικροδιαφορές"])
    filing = st.date_input("4) Ημερομηνία κατάθεσης αγωγής", value=date.today(), format="DD/MM/YYYY")

# Invalidate results on input change
sig = (abroad, public, procedure, filing)
if "last_sig" not in st.session_state:
    st.session_state["last_sig"] = sig
    st.session_state["rows"] = None
elif st.session_state["last_sig"] != sig:
    st.session_state["last_sig"] = sig
    st.session_state["rows"] = None

# Compute button
compute_pressed = st.button("Υπολογισμός", type="primary")

if compute_pressed:
    ctx = RuleContext(
        filing_date=filing,
        defendant_abroad_or_unknown=abroad,
        public_entity_party=public,
        procedure="regular" if procedure=="Τακτική" else "small_claims",
    )
    calc = DeadlineCalculator(ctx)
    rows_full = calc.compute()
    rows = rows_full[:-2] if len(rows_full) >= 4 else rows_full
    st.session_state["rows"] = rows
else:
    rows = st.session_state.get("rows", None)

# -----------------------------
# Results
# -----------------------------
if rows is None or len(rows) == 0:
    st.info("Πατήστε **Υπολογισμός** για να υπολογιστούν οι προθεσμίες.")
else:
    st.success("Υπολογισμός ολοκληρώθηκε.")
    # Uppercase headers as requested
    hdr = st.columns([5, 3])
    with hdr[0]: st.markdown("**ΕΝΕΡΓΕΙΕΣ**")
    with hdr[1]: st.markdown("**ΠΡΟΘΕΣΜΙΕΣ**")

    # Helper texts
    def _explain_calc_text(it, rows_all):
        lb = it.legal_basis
        end_str = it.deadline.strftime("%d-%m-%Y")
        weekday = it.weekday
        if "215" in lb:
            n = 60 if abroad else 30
            return f"Από την κατάθεση ({filing:%d-%m-%Y}) + **{n} ημέρες**, εξαιρώντας **Αύγουστο**{', και **1/7–15/9**' if public else ''}. Αν πέσει Σ/Κ, μεταφορά σε εργάσιμη. Τελική: **{weekday} {end_str}**."
        if lb.startswith("ΚΠολΔ 237") and "§2" not in lb:
            n = 120 if abroad else 90
            service = rows_all[0].deadline
            return f"Από τη **λήξη επίδοσης** ({service:%d-%m-%Y}) + **{n} ημέρες**, ίδιες εξαιρέσεις· **λήξη 12:00**. Τελική: **{weekday} {end_str}**."
        if "237 §2" in lb:
            return f"**+15 ημέρες** από την προθεσμία προτάσεων ({rows_all[1].deadline:%d-%m-%Y}); **λήξη 12:00**. Τελική: **{weekday} {end_str}**."
        if "238 §1" in lb and "τελ" not in lb:
            n = 90 if abroad else 60
            return f"Παρεμπίπτουσες: από **κατάθεση** ({filing:%d-%m-%Y}) + **{n} ημέρες**. Τελική: **{weekday} {end_str}**."
        if "468 §1" in lb:
            n = 30 if abroad else 10
            return f"Μικροδιαφορές: από κατάθεση ({filing:%d-%m-%Y}) + **{n} ημέρες**. Τελική: **{weekday} {end_str}**."
        if "468 §2" in lb and "Υπόμνημα" in it.action:
            return f"Μικροδιαφορές: **20 ημέρες** από τη **λήξη επίδοσης** ({rows_all[0].deadline:%d-%m-%Y}). Τελική: **{weekday} {end_str}**."
        if "468 §2" in lb and "Προσθήκη" in it.action:
            return f"Μικροδιαφορές: **+5 ημέρες** από το 20ήμερο ({rows_all[1].deadline:%d-%m-%Y}). Τελική: **{weekday} {end_str}**."
        if "468 §3" in lb and "κατάθεση" in it.action:
            n = 40 if abroad else 20
            return f"Μικροδιαφορές — παρεμπίπτουσες: από κατάθεση ({filing:%d-%m-%Y}) + **{n} ημέρες**. Τελική: **{weekday} {end_str}**."
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
            return "ΚΠολΔ **238 §1** — Παρεμπίπτουσες: **κατάθεση & επίδοση** **60** ημέρες (**90** αν εξωτερικού/αγνώστου) από **κατάθεση αγωγής**."
        if "468 §1" in lb:
            return "ΚΠολΔ **468 §1** — Επίδοση αγωγής μικροδιαφορών **10** ημέρες (**30** αν εξωτερικού/αγνώστου) από κατάθεση."
        if "468 §2" in lb and "Υπόμνημα" in it.action:
            return "ΚΠολΔ **468 §2** — **Υπόμνημα εναγομένου & αποδεικτικά** **20** ημέρες από τη **λήξη προθεσμίας επίδοσης**."
        if "468 §2" in lb and "Προσθήκη" in it.action:
            return "ΚΠολΔ **468 §2** — **Προσθήκη–αντίκρουση** **5** ημέρες μετά το 20ήμερο."
        if "468 §3" in lb and "κατάθεση" in it.action:
            return "ΚΠολΔ **468 §3** — Παρεμπίπτουσες: κατάθεση & επίδοση **20** ημέρες (**40** αν εξωτερικού/αγνώστου) από κατάθεση."
        return f"Σχετική νομοθεσία: **{lb}**."

    # Full list for explanations
    ctx_tmp = RuleContext(
        filing_date=filing,
        defendant_abroad_or_unknown=abroad,
        public_entity_party=public,
        procedure="regular" if procedure=="Τακτική" else "small_claims",
    )
    rows_full_for_calc = DeadlineCalculator(ctx_tmp).compute()

    for i, it in enumerate(rows):
        dcols = st.columns([5, 3])
        with dcols[0]:
            st.markdown(f"**{i+1}. {it.action}**")
        with dcols[1]:
            st.markdown(f"**{it.weekday} {it.deadline:%d-%m-%Y}**")

        # Row buttons (now small fonts by CSS; left/right alignment with wide columns)
        outer = st.columns([0.0001, 6, 0.5, 6, 0.0001])
        calc_key = f"show_calc_{i}"
        law_key = f"show_law_{i}"

        with outer[1]:
            if st.button("Τρόπος Υπολογισμού", key=f"calc_btn_{i}"):
                st.session_state[calc_key] = not st.session_state.get(calc_key, False)
        with outer[3]:
            if st.button("Νομική Βάση", key=f"law_btn_{i}"):
                st.session_state[law_key] = not st.session_state.get(law_key, False)

        if st.session_state.get(calc_key, False) or st.session_state.get(law_key, False):
            full = st.container()
            with full:
                if st.session_state.get(calc_key, False):
                    st.info(_explain_calc_text(it, rows_full_for_calc), icon="ℹ️")
                if st.session_state.get(law_key, False):
                    st.code(_law_text(it), language="markdown")
        st.markdown("<hr/>", unsafe_allow_html=True)

# -----------------------------
# PDF Export — save ONLY to ~/Downloads; include extra metadata; remove Ημέρα column;
# and append weekday to ΠΡΟΘΕΣΜΙΕΣ cell.
# -----------------------------
st.subheader("📄 Εξαγωγή σε PDF (μόνο αποθήκευση σε Downloads)")
client = st.text_input("Πελάτης (προαιρετικό)", key="client_input")
opponent = st.text_input("Αντίδικος (προαιρετικό)", key="opponent_input")

def _sanitize(s: str) -> str:
    for ch in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        s = s.replace(ch, ' ')
    return s.strip() or "Χωρίς_Όνομα"

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

    # Parties
    c.setFont(font_name, 12)
    c.drawString(x, y, f"Πελάτης: {meta.get('client','-')}"); y -= 6 * mm
    c.drawString(x, y, f"Αντίδικος: {meta.get('opponent','-')}"); y -= 8 * mm

    # Extra calculation settings
    c.setFont(font_name, 11)
    c.drawString(x, y, f"Ημερομηνία Κατάθεσης: {meta.get('filing','-')}"); y -= 6 * mm
    c.drawString(x, y, f"Διαδικασία: {meta.get('procedure','-')}"); y -= 6 * mm
    c.drawString(x, y, f"Εναγόμενος Εξωτερικού/Αγνώστου: {meta.get('abroad','-')}"); y -= 6 * mm
    c.drawString(x, y, f"Διάδικος Δημόσιο: {meta.get('public','-')}"); y -= 10 * mm

    # Headers (Ημέρα removed; ΠΡΟΘΕΣΜΙΕΣ includes weekday)
    headers = ["#", "ΕΝΕΡΓΕΙΕΣ", "Νομική Βάση", "ΠΡΟΘΕΣΜΙΕΣ"]
    col_widths = [10*mm, 88*mm, 35*mm, 45*mm]  # total 178mm (fits A4 margins)

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
        vals = [
            str(idx),
            it.action,
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
    if rows is None or len(rows) == 0:
        st.warning("Δεν υπάρχουν αποτελέσματα. Πάτησε πρώτα **Υπολογισμός**.")
    else:
        # Build items from visible rows
        pdf_items = []
        step = 1
        for it in rows:
            pdf_items.append(DeadlineItem(step, it.action, it.legal_basis, it.deadline, it.weekday, ""))
            step += 1

        downloads = os.path.expanduser("~/Downloads")
        os.makedirs(downloads, exist_ok=True)
        client = st.session_state.get("client_input", "")
        opponent = st.session_state.get("opponent_input", "")
        fname = f"Προθεσμίες Αγωγής {client.strip() or 'Χωρίς_Όνομα'} vs {opponent.strip() or 'Χωρίς_Όνομα'}.pdf"
        path = os.path.join(downloads, fname)

        meta = {
            "client": client,
            "opponent": opponent,
            "filing": filing.strftime("%d-%m-%Y"),
            "procedure": procedure,
            "abroad": "Ναι" if abroad else "Όχι",
            "public": "Ναι" if public else "Όχι",
        }
        _make_pdf_custom(path, "Πίνακας Προθεσμιών", meta, pdf_items)

        st.success(f"Το PDF αποθηκεύτηκε στον φάκελο **Downloads** ως: `{fname}`")
        st.info(f"Πλήρης διαδρομή: `{path}`")

# -----------------------------
# PyCharm bootstrap guard
# -----------------------------
if __name__ == "__main__":
    if (os.environ.get("STREAMLIT_BOOTSTRAPPED") != "1") and all("streamlit" not in arg for arg in sys.argv):
        os.environ["STREAMLIT_BOOTSTRAPPED"] = "1"
        from streamlit.web import cli as stcli
        sys.argv = ["streamlit", "run", os.path.abspath(__file__)]
        stcli.main()
