# -*- coding: utf-8 -*-
import os
import io
import shutil
from datetime import date, datetime, timedelta

from dash import Dash, html, dcc, Output, Input, State, MATCH, callback, no_update
import dash_bootstrap_components as dbc

# =========================================================
#  Base path: ρίζα για τοπικό, υπο-μονοπάτι για Plesk
#  Σε Plesk ορίζεις env var: DEADLINES_BASE_PATH=/deadlines/
# =========================================================
BASE_PATH = os.environ.get("DEADLINES_BASE_PATH", "/")

# -----------------------------
# Dash (WSGI πάνω σε Flask)
# -----------------------------
THEME = dbc.themes.FLATLY  # καθαρό, επαγγελματικό

app = Dash(
    __name__,
    requests_pathname_prefix=BASE_PATH,
    routes_pathname_prefix=BASE_PATH,
    external_stylesheets=[THEME]
)
server = app.server  # για Plesk/Passenger

# -----------------------------
# ΔΙΚΕΣ ΣΟΥ ΒΙΒΛΙΟΘΗΚΕΣ deadlines
# -----------------------------
from deadlines import DeadlineCalculator
from deadlines.rules import RuleContext
from deadlines.pdf import GREEK_FONT_PATH

# ==========================
#  Utils
# ==========================
def ensure_greek_font_available():
    """Εξασφαλίζει TTF με ελληνικά για το PDF (deadlines.pdf περιμένει GREEK_FONT_PATH)."""
    try:
        os.makedirs(os.path.dirname(GREEK_FONT_PATH), exist_ok=True)
        if os.path.exists(GREEK_FONT_PATH):
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
                    shutil.copyfile(c, GREEK_FONT_PATH)
                    break
                except Exception:
                    pass
    except Exception:
        pass

WEEKDAYS_GR = ["Δευτέρα","Τρίτη","Τετάρτη","Πέμπτη","Παρασκευή","Σάββατο","Κυριακή"]

def weekday_gr(dt: date) -> str:
    return WEEKDAYS_GR[dt.weekday()]

def next_monday(d: date) -> date:
    while d.weekday() >= 5:  # 5=Σ, 6=Κ
        d += timedelta(days=1)
    return d

def parse_date_str(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()

# -----------------------------
# Creative CSS -> assets/inline.css
# -----------------------------
BRAND_CSS = r"""
:root{
  /* Προσαρμογή για το ziamparas.gr – άλλαξε εδώ αν έχεις συγκεκριμένα hex */
  --brand-primary: #1f3b73;    /* deep blue */
  --brand-primary-dark: #152a54;
  --brand-accent:  #5fa8ff;    /* light accent */
  --brand-muted:   #f2f6fc;    /* light background */
}

/* Βασικά */
body { font-size: 18px; background: #ffffff; }
.container-fluid { max-width: 1280px; }

/* Bootstrap primary override */
.btn-primary {
  background-color: var(--brand-primary) !important;
  border-color: var(--brand-primary) !important;
}
.btn-primary:hover {
  background-color: var(--brand-primary-dark) !important;
  border-color: var(--brand-primary-dark) !important;
}

/* Κεφαλίδα */
.app-title { font-weight: 800; line-height: 1.15; letter-spacing: .2px; }
.app-subtitle { font-size: 0.98rem; color:#4b5563; margin-top:-8px; margin-bottom:16px; }

/* Κάρτες */
.card-clean { border:1px solid #e9ecef; border-radius:14px; box-shadow: 0 2px 10px rgba(0,0,0,.03); }
.card-clean .card-header { background: var(--brand-muted); font-weight:700; }

/* Πίνακας προθεσμιών (flex rows) */
.deadline-row { border-bottom: 1px solid #eef2f7; padding: .55rem .4rem; }
.deadline-row .row-flex { display:flex; align-items:center; gap: .8rem; }
.cell-action { flex: 1 1 50%; font-weight: 700; }
.cell-date   { flex: 0 0 35%; font-weight: 700; white-space: nowrap; }  /* περισσότερο πλάτος + no wrap */
.cell-buttons{ flex: 0 0 15%; display:flex; gap:.35rem; justify-content:flex-end; }

/* Micro buttons (chips) – μικρότερα από τα fonts της γραμμής */
.btn-chip {
  font-size: 11px; font-weight: 800; padding: .18rem .5rem; border-radius: 9999px;
  border:1px solid var(--bs-border-color);
  background: linear-gradient(180deg,#ffffff,#f6f8fa);
  color:#0a0a0a;
}
.btn-chip:hover { background: linear-gradient(180deg,#f2f6ff,#e9f1ff); }
.btn-chip.calc { border-color:#b6d3ff; }
.btn-chip.law  { border-color:#d1c4f3; }

/* Εμφάνιση κρυφών panels */
.panel { background:#fafbfe; border:1px solid #e6e8f0; border-radius: 10px; padding:.6rem .8rem; margin-top:.35rem; }

/* Header row */
.header-row { background:#f7f9fc; border-top-left-radius:10px; border-top-right-radius:10px; }
.header-row .cell-action, .header-row .cell-date { font-weight:800; }
"""

def ensure_assets_css():
    try:
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        os.makedirs(assets_dir, exist_ok=True)
        css_path = os.path.join(assets_dir, "inline.css")
        write = True
        if os.path.exists(css_path):
            try:
                with open(css_path, "r", encoding="utf-8") as f:
                    if f.read() == BRAND_CSS:
                        write = False
            except Exception:
                pass
        if write:
            with open(css_path, "w", encoding="utf-8") as f:
                f.write(BRAND_CSS)
    except Exception:
        pass

ensure_greek_font_available()
ensure_assets_css()

# ==========================
#  Layout
# ==========================
controls_card = dbc.Card(
    dbc.CardBody([
        html.Div("⚙️ Ρυθμίσεις", className="h5 mb-3"),
        dbc.Row([
            dbc.Col([
                dbc.Label("1) Εναγόμενος εξωτερικού/αγνώστου"),
                dcc.Dropdown(
                    id="in-abroad",
                    options=[{"label":"Όχι","value":"no"},{"label":"Ναι","value":"yes"}],
                    value="no", clearable=False
                ),
            ], md=6),
            dbc.Col([
                dbc.Label("2) Υπάρχει Δημόσιο/ΝΠΔΔ διάδικος"),
                dcc.Dropdown(
                    id="in-public",
                    options=[{"label":"Όχι","value":"no"},{"label":"Ναι","value":"yes"}],
                    value="no", clearable=False
                ),
            ], md=6),
        ], className="g-3"),
        dbc.Row([
            dbc.Col([
                dbc.Label("3) Διαδικασία"),
                dcc.Dropdown(
                    id="in-procedure",
                    options=[{"label":"Τακτική","value":"regular"},{"label":"Μικροδιαφορές","value":"small_claims"}],
                    value="regular", clearable=False
                ),
            ], md=6),
            dbc.Col([
                dbc.Label("4) Ημερομηνία κατάθεσης αγωγής"),
                dcc.DatePickerSingle(
                    id="in-filing-date",
                    display_format="DD/MM/YYYY",
                    date=date.today().strftime("%Y-%m-%d"),
                ),
                html.Div(id="filing-note", className="text-secondary mt-1", style={"fontSize":"0.95rem"})
            ], md=6),
        ], className="g-3"),
        html.Hr(),
        dbc.Row([
            dbc.Col(dbc.Button("Υπολογισμός", id="btn-compute",
                               color="primary", className="w-100 fw-bold", size="lg"), md=12),
        ], className="g-3"),
        html.Hr(),
        dbc.Row([
            dbc.Col(dbc.Input(id="in-client", placeholder="Πελάτης (προαιρετικό)"), md=6),
            dbc.Col(dbc.Input(id="in-opponent", placeholder="Αντίδικος (προαιρετικό)"), md=6),
        ], className="g-2"),
        dbc.Row([
            dbc.Col(dbc.Button("Αποθήκευση PDF", id="btn-pdf",
                               color="secondary", className="w-100 mt-2"), md=12),
        ]),
    ]),
    className="card-clean"
)

results_card = dbc.Card(
    dbc.CardBody([
        html.Div("📋 Προθεσμίες", className="h5 mb-3"),
        html.Div(id="banner", className="text-info mb-2", style={"fontSize":"0.98rem"}),
        dcc.Store(id="rows-store"),  # σειρές για render & PDF
        dcc.Store(id="meta-store"),
        html.Div(id="rows-container"),
        dcc.Download(id="pdf-download"),
        html.Div(id="pdf-message", className="text-success mt-2", style={"fontSize":"0.95rem"}),
    ]),
    className="card-clean"
)

app.layout = dbc.Container([
    html.Br(),
    html.H2("⚖️ Υπολογισμός Προθεσμιών ΚΠολΔ — Τακτική & Μικροδιαφορές",
            className="app-title"),
    html.Div("(Με το νομοθετικό πλαίσιο μέχρι 31-12-2025)", className="app-subtitle"),
    dbc.Row([
        dbc.Col(controls_card, md=5),
        dbc.Col(results_card, md=7),
    ], className="g-4"),
    html.Br()
], fluid=True)

# ==========================
#  Callbacks
# ==========================
@callback(
    Output("rows-store","data"),
    Output("meta-store","data"),
    Output("banner","children"),
    Output("filing-note","children"),
    Input("btn-compute","n_clicks"),
    State("in-abroad","value"),
    State("in-public","value"),
    State("in-procedure","value"),
    State("in-filing-date","date"),
    prevent_initial_call=True
)
def compute_deadlines(n_clicks, abroad_val, public_val, procedure_val, filing_date_str):
    """Υπολογισμός προθεσμιών. Αν η επιλεγμένη κατάθεση είναι Σ/Κ, μεταφέρεται στη Δευτέρα
    και εμφανίζεται ενημερωτικό μήνυμα."""
    if not filing_date_str:
        return no_update, no_update, "Βάλε ημερομηνία κατάθεσης.", no_update

    filing = parse_date_str(filing_date_str)
    adjusted_note = ""
    if filing.weekday() >= 5:
        adj = next_monday(filing)
        adjusted_note = f"Επιλέχθηκε Σ/Κ· η ημερομηνία κατάθεσης μεταφέρθηκε αυτόματα στη Δευτέρα {adj.strftime('%d-%m-%Y')}."
        filing = adj

    abroad = (abroad_val == "yes")
    public = (public_val == "yes")

    ctx = RuleContext(
        filing_date=filing,
        defendant_abroad_or_unknown=abroad,
        public_entity_party=public,
        procedure=procedure_val
    )
    calc = DeadlineCalculator(ctx)
    all_rows = calc.compute()

    # Αφαιρούμε τις 2 τελευταίες, όπως είχες ζητήσει παλαιότερα
    rows = all_rows[:-2] if len(all_rows) >= 2 else all_rows

    def rename_action(a: str) -> str:
        low = a.lower()
        if "προτάσε" in low: return "Κατάθεση Προτάσεων"
        if "προσθήκ" in low: return "Κατάθεση Προσθήκης-Αντίκρουσης"
        if "παρεμπίπτουσ" in low: return "Άσκηση Παρέμβασης, Ανταγωγής κτλ"
        return a

    def explain_calc(it, rows_all):
        lb = it.legal_basis
        end_str = it.deadline.strftime("%d-%m-%Y")
        wd = weekday_gr(it.deadline)
        if "215" in lb:
            n = 60 if abroad else 30
            extra = ", και 1/7–15/9" if public else ""
            return f"Από την κατάθεση ({filing:%d-%m-%Y}) + {n} ημέρες, εξαιρώντας Αύγουστο{extra}. Μεταφορά αν Σ/Κ. Τελική: {wd} {end_str}."
        if lb.startswith("ΚΠολΔ 237") and "§2" not in lb:
            n = 120 if abroad else 90
            service = rows_all[0].deadline
            return f"Από τη λήξη επίδοσης ({service:%d-%m-%Y}) + {n} ημέρες (λήξη 12:00). Τελική: {wd} {end_str}."
        if "237 §2" in lb:
            return f"+15 ημέρες από την προθεσμία προτάσεων ({rows_all[1].deadline:%d-%m-%Y}) (λήξη 12:00). Τελική: {wd} {end_str}."
        if "238 §1" in lb and "τελ" not in lb:
            n = 90 if abroad else 60
            return f"Παρεμπίπτουσες: από κατάθεση ({filing:%d-%m-%Y}) + {n} ημέρες. Τελική: {wd} {end_str}."
        if "468 §1" in lb:
            n = 30 if abroad else 10
            return f"Μικροδιαφορές: από κατάθεση ({filing:%d-%m-%Y}) + {n} ημέρες. Τελική: {wd} {end_str}."
        if "468 §2" in lb and "Υπόμνημα" in it.action:
            return f"Μικροδιαφορές: 20 ημέρες από λήξη επίδοσης ({rows_all[0].deadline:%d-%m-%Y}). Τελική: {wd} {end_str}."
        if "468 §2" in lb and "Προσθήκη" in it.action:
            return f"Μικροδιαφορές: +5 ημέρες από το 20ήμερο ({rows_all[1].deadline:%d-%m-%Y}). Τελική: {wd} {end_str}."
        if "468 §3" in lb and "κατάθεση" in it.action:
            n = 40 if abroad else 20
            return f"Μικροδιαφορές — παρεμπίπτουσες: από κατάθεση ({filing:%d-%m-%Y}) + {n} ημέρες. Τελική: {wd} {end_str}."
        return f"Υπολογισμός βάσει {lb}. Τελική: {wd} {end_str}."

    def law_text(it):
        lb = it.legal_basis
        if "215" in lb:
            return "ΚΠολΔ 215 §2 — Επίδοση αγωγής εντός 30 ημερών (60 αν εξωτερικού/αγνώστου)."
        if lb.startswith("ΚΠολΔ 237") and "§2" not in lb:
            return "ΚΠολΔ 237 — Προτάσεις & αποδεικτικά 90 ημέρες (120 αν εξωτερικού/αγνώστου) από τη λήξη προθεσμίας επίδοσης. Λήξη 12:00."
        if "237 §2" in lb:
            return "ΚΠολΔ 237 §2 — Προσθήκη–αντίκρουση 15 ημέρες μετά την προθεσμία προτάσεων. Λήξη 12:00."
        if "238 §1" in lb and "τελ" not in lb:
            return "ΚΠολΔ 238 §1 — Παρεμπίπτουσες: κατάθεση & επίδοση 60 ημέρες (90 αν εξωτερικού/αγνώστου) από κατάθεση αγωγής."
        if "468 §1" in lb:
            return "ΚΠολΔ 468 §1 — Επίδοση αγωγής μικροδιαφορών 10 ημέρες (30 αν εξωτερικού/αγνώστου) από κατάθεση."
        if "468 §2" in lb and "Υπόμνημα" in it.action:
            return "ΚΠολΔ 468 §2 — Υπόμνημα εναγομένου & αποδεικτικά 20 ημέρες από τη λήξη προθεσμίας επίδοσης."
        if "468 §2" in lb and "Προσθήκη" in it.action:
            return "ΚΠολΔ 468 §2 — Προσθήκη–αντίκρουση 5 ημέρες μετά το 20ήμερο."
        if "468 §3" in lb and "κατάθεση" in it.action:
            return "ΚΠολΔ 468 §3 — Παρεμπίπτουσες: κατάθεση & επίδοση 20 ημέρες (40 αν εξωτερικού/αγνώστου) από κατάθεση."
        return f"Σχετική νομοθεσία: {lb}."

    rows_out = []
    for idx, it in enumerate(rows, start=1):
        rows_out.append({
            "idx": idx,
            "action": rename_action(it.action),
            "legal_basis": it.legal_basis,
            "deadline_iso": it.deadline.isoformat(),
            "deadline_str": f"{weekday_gr(it.deadline)} {it.deadline.strftime('%d-%m-%Y')}",
            "calc_text": explain_calc(it, all_rows),
            "law_text": law_text(it),
        })

    banner = f"Υπολογισμός ολοκληρώθηκε για Ημερ. κατάθεσης {filing.strftime('%d-%m-%Y')}" if rows_out else "Δεν προέκυψαν προθεσμίες."
    filing_note = adjusted_note if adjusted_note else ""

    meta = {
        "filing": filing.strftime("%d-%m-%Y"),
        "procedure": "Τακτική" if procedure_val=="regular" else "Μικροδιαφορές",
        "abroad": "Ναι" if abroad else "Όχι",
        "public": "Ναι" if public else "Όχι",
    }
    return rows_out, meta, banner, filing_note


@callback(
    Output("rows-container","children"),
    Input("rows-store","data"),
)
def render_rows(rows):
    if not rows:
        return html.Div("Πατήστε «Υπολογισμός» για να εμφανιστούν προθεσμίες.", style={"color":"#555"})
    out = []
    # header row
    out.append(
        html.Div(className="deadline-row header-row", children=[
            html.Div(className="row-flex", children=[
                html.Div("ΕΝΕΡΓΕΙΕΣ", className="cell-action"),
                html.Div("ΠΡΟΘΕΣΜΙΕΣ", className="cell-date"),
                html.Div("", className="cell-buttons"),
            ])
        ])
    )
    # data rows
    for r in rows:
        i = r["idx"]
        out.append(
            html.Div([
                html.Div(className="row-flex", children=[
                    html.Div(f"{i}. {r['action']}", className="cell-action"),
                    html.Div(r["deadline_str"], className="cell-date"),
                    html.Div(className="cell-buttons", children=[
                        dbc.Button("🧮 Τρόπος Υπολογισμού", id={"type":"calc-btn","index":i},
                                   className="btn-chip calc", n_clicks=0),
                        dbc.Button("📜 Νομική Βάση", id={"type":"law-btn","index":i},
                                   className="btn-chip law", n_clicks=0),
                    ])
                ]),
                html.Div(r["calc_text"], id={"type":"calc-panel","index":i},
                         className="panel", style={"display":"none"}),
                html.Div(r["law_text"], id={"type":"law-panel","index":i},
                         className="panel", style={"display":"none"}),
            ], className="deadline-row")
        )
    return out


# Toggle panels
@callback(
    Output({"type":"calc-panel","index":MATCH}, "style"),
    Input({"type":"calc-btn","index":MATCH}, "n_clicks"),
    prevent_initial_call=True
)
def toggle_calc_panel(n):
    opened = n and (n % 2 == 1)
    return {"display":"block"} if opened else {"display":"none"}


@callback(
    Output({"type":"law-panel","index":MATCH}, "style"),
    Input({"type":"law-btn","index":MATCH}, "n_clicks"),
    prevent_initial_call=True
)
def toggle_law_panel(n):
    opened = n and (n % 2 == 1)
    return {"display":"block"} if opened else {"display":"none"}


# --------- PDF export ----------
def build_pdf_bytes(title: str, meta: dict, rows_list: list) -> bytes:
    """Φτιάχνει PDF σε bytes (και γράφει και σε ~/Downloads)."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    buf = io.BytesIO()

    font_name = "DejaVuSans"
    try:
        if os.path.exists(GREEK_FONT_PATH) and "DejaVuSans" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("DejaVuSans", GREEK_FONT_PATH))
    except Exception:
        font_name = "Helvetica"

    c = canvas.Canvas(buf, pagesize=A4)
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

    # Πλάτη πίνακα
    headers = ["#", "ΕΝΕΡΓΕΙΕΣ", "Νομική Βάση", "ΠΡΟΘΕΣΜΙΕΣ"]
    col_widths = [10*mm, 80*mm, 33*mm, 55*mm]

    c.setFont(font_name, 12)
    c.rect(x, y-8*mm, sum(col_widths), 8*mm, stroke=1, fill=0)
    cx = x + 2
    for i, h in enumerate(headers):
        c.drawString(cx, y-6*mm, h); cx += col_widths[i]
    y -= 8*mm

    c.setFont(font_name, 11)
    for row in rows_list:
        if y < margin + 25*mm:
            c.showPage(); y = height - margin
            c.setFont(font_name, 12)
            c.rect(x, y-8*mm, sum(col_widths), 8*mm, stroke=1, fill=0)
            cx = x + 2
            for i, h in enumerate(headers):
                c.drawString(cx, y-6*mm, h); cx += col_widths[i]
            y -= 8*mm
            c.setFont(font_name, 11)

        c.rect(x, y-12*mm, sum(col_widths), 12*mm, stroke=1, fill=0)
        cx = x + 2
        vals = [str(row["idx"]), row["action"], row["legal_basis"], row["deadline_str"]]
        for i, v in enumerate(vals):
            c.drawString(cx, y-8*mm, (v or "")[:110]); cx += col_widths[i]
        y -= 12*mm

    c.setFont(font_name, 9)
    c.drawString(x, margin, "Generated with Greek Civil Deadlines — Dash App")
    c.save()

    data = buf.getvalue()
    buf.close()

    # γράψε και στο ~/Downloads (αν υπάρχει)
    try:
        downloads = os.path.expanduser("~/Downloads")
        os.makedirs(downloads, exist_ok=True)
        # --- ΝΕΟ ΟΝΟΜΑ ---
        fname = f"Προθεσμίες {meta.get('client','Χωρίς_Όνομα')} vs {meta.get('opponent','Χωρίς_Όνομα')}.pdf"
        with open(os.path.join(downloads, fname), "wb") as f:
            f.write(data)
    except Exception:
        pass

    return data


@callback(
    Output("pdf-download","data"),
    Output("pdf-message","children"),
    Input("btn-pdf","n_clicks"),
    State("rows-store","data"),
    State("meta-store","data"),
    State("in-client","value"),
    State("in-opponent","value"),
    prevent_initial_call=True
)
def export_pdf(n_clicks, rows, meta, client, opponent):
    if not rows:
        return no_update, "Δεν υπάρχουν αποτελέσματα. Πάτησε πρώτα «Υπολογισμός»."
    meta = dict(meta or {})
    meta["client"] = (client or "").strip() or "Χωρίς_Όνομα"
    meta["opponent"] = (opponent or "").strip() or "Χωρίς_Όνομα"

    data = build_pdf_bytes("Πίνακας Προθεσμιών", meta, rows)
    # --- ΝΕΟ ΟΝΟΜΑ ---
    filename = f"Προθεσμίες {meta['client']} vs {meta['opponent']}.pdf"
    # --- ΝΕΟ ΜΗΝΥΜΑ ---
    msg = f'Το PDF αποθηκεύτηκε στον φάκελο Downloads με όνομα αρχείου: "{filename}".'
    return dcc.send_bytes(lambda b: b.write(data), filename=filename), msg


# ==========================
#  Main (τοπική εκτέλεση)
# ==========================
if __name__ == "__main__":
    # Τοπικά: με BASE_PATH="/", άνοιξε http://127.0.0.1:8050/
    app.run(debug=False, host="127.0.0.1", port=8050)
