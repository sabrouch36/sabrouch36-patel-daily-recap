# Patel Logistics – Daily Operations Recap (Sheets + CSV fallback, no charts)
# Run locally:  python -m streamlit run app.py

import io
import os
import traceback
from datetime import date
from typing import Dict, List

import pandas as pd
import streamlit as st

# -------- PDF (optional on cloud) --------
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

# -------- Google Sheets (optional via secrets) --------
try:
    from google.oauth2.service_account import Credentials
    import gspread
    from gspread_dataframe import get_as_dataframe, set_with_dataframe
    GS_LIBS_OK = True
except Exception:
    GS_LIBS_OK = False

st.set_page_config(page_title="Patel Logistics – Daily Recap", page_icon="📢", layout="wide")

# ---------- Config ----------
DATA_FILE = "daily_recap.csv"
SHEET_TAB = "entries"

COLUMNS: List[str] = [
    "day","the_date",
    "total_routes","amzl_late","add_routes","total_trainings","total_packages",
    "packages_delivered","rescues_completed","rescuing_das",
    "returned_total","returned_uta","returned_bc","returned_oodt","returned_other",
    "violations","seatbelt","speeding","hard_braking","injuries","coaching",
    "das_exceeding_4_days","adp_vs_paid_hours",
    "grounded","damages",
    "complaints","station_feedback","route_failures"
]

# ---------- Utilities ----------
def safe_int(x) -> int:
    try:
        return int(x)
    except Exception:
        return 0

def pct(n, d) -> float:
    n = safe_int(n); d = safe_int(d)
    return 0.0 if d == 0 else (n / d) * 100.0

def empty_row() -> Dict:
    return {k: "" for k in COLUMNS}

# ---------- Storage: Sheets or CSV ----------
def sheets_enabled() -> bool:
    if not GS_LIBS_OK:
        return False
    try:
        _ = st.secrets["gcp_service_account"]
        _ = st.secrets["google"]["sheet_id"]
        return True
    except Exception:
        return False

@st.cache_resource(show_spinner=False)
def _get_ws():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(st.secrets["google"]["sheet_id"])
    try:
        ws = sh.worksheet(SHEET_TAB)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=SHEET_TAB, rows=1000, cols=50)
        ws.append_row(COLUMNS, value_input_option="RAW")
    return ws

def load_all() -> pd.DataFrame:
    # Prefer Sheets
    if sheets_enabled():
        try:
            ws = _get_ws()
            df = get_as_dataframe(ws, evaluate_formulas=True, header=1).dropna(how="all")
            if df.empty:
                return pd.DataFrame(columns=COLUMNS)
            # keep only known columns in order
            cols = [c for c in COLUMNS if c in df.columns]
            return df[cols]
        except Exception:
            st.warning("Google Sheets unavailable, using local CSV temporarily.")
            st.caption(traceback.format_exc())

    # Fallback to CSV
    if not os.path.exists(DATA_FILE):
        pd.DataFrame(columns=COLUMNS).to_csv(DATA_FILE, index=False)
    try:
        df = pd.read_csv(DATA_FILE)
    except Exception:
        df = pd.DataFrame(columns=COLUMNS)
    return df

def save_entry(entry: Dict):
    # Try Sheets first
    if sheets_enabled():
        try:
            ws = _get_ws()
            row = [entry.get(c, "") for c in COLUMNS]
            ws.append_row(row, value_input_option="USER_ENTERED")
            return
        except Exception:
            st.error("Save failed to Google Sheets. Falling back to CSV.")
            st.caption(traceback.format_exc())

    # CSV fallback
    df = load_all()
    df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

def backup_all():
    if not sheets_enabled():
        st.info("Backups available only when Google Sheets is enabled.")
        return
    try:
        ws = _get_ws()
        sh = ws.spreadsheet
        try:
            bk = sh.worksheet("backups")
        except gspread.exceptions.WorksheetNotFound:
            bk = sh.add_worksheet(title="backups", rows=2000, cols=50)
        df = load_all()
        bk.clear()
        set_with_dataframe(bk, df)
        st.success("Backup completed to 'backups' tab.")
    except Exception:
        st.error("Backup failed.")
        st.caption(traceback.format_exc())

# ---------- Auth (optional) ----------
def auth_gate():
    try:
        required = st.secrets["security"]["app_password"]
    except Exception:
        return  # no password configured
    with st.expander("Sign in", expanded=True):
        pwd = st.text_input("App password", type="password", placeholder="Enter app password")
        if pwd != required:
            st.stop()

# ---------- UI ----------
def collect_inputs() -> Dict:
    st.subheader("Header")
    c1, c2 = st.columns(2)
    with c1:
        day = st.selectbox("Day", ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"])
    with c2:
        the_date = st.date_input("Date", value=date.today())

    st.divider()
    st.subheader("📦 Volume & Routes")
    c1, c2, c3 = st.columns(3)
    with c1:
        total_routes = st.number_input("Total Routes", min_value=0, step=1)
        amzl_late = st.number_input("AMZL Late Cancels", min_value=0, step=1)
    with c2:
        add_routes = st.number_input("Additional Routes Picked Up", min_value=0, step=1)
        total_trainings = st.text_input("Total Trainings (Name DayX)")
    with c3:
        total_packages = st.number_input("Total Packages", min_value=0, step=1)

    st.subheader("🚛 Driver Performance")
    c1, c2, c3 = st.columns(3)
    with c1:
        packages_delivered = st.number_input("Packages Delivered", min_value=0, step=1)
        rescues_completed = st.number_input("Rescues Completed", min_value=0, step=1)
    with c2:
        rescuing_das = st.text_input("Rescues By (Names)")
        returned_total = st.number_input("Packages Returned (Total)", min_value=0, step=1)
    with c3:
        returned_uta = st.number_input("Returned - UTA", min_value=0, step=1)
        returned_bc = st.number_input("Returned - BC", min_value=0, step=1)
        returned_oodt = st.number_input("Returned - OODT", min_value=0, step=1)
        returned_other = st.number_input("Returned - Other", min_value=0, step=1)

    st.subheader("⚠ Safety & Compliance")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        violations = st.number_input("Violations (Total)", min_value=0, step=1)
    with c2:
        seatbelt = st.number_input("Seatbelt", min_value=0, step=1)
    with c3:
        speeding = st.number_input("Speeding", min_value=0, step=1)
    with c4:
        hard_braking = st.number_input("Hard Braking", min_value=0, step=1)
    c1, c2 = st.columns(2)
    with c1:
        injuries = st.number_input("Injuries", min_value=0, step=1)
    with c2:
        coaching = st.text_area("Drivers Needing Coaching (Names & brief reasons)")

    st.subheader("💰 Labor & Cost Metrics")
    c1, c2 = st.columns(2)
    with c1:
        das_exceeding_4_days = st.text_area("DAS EXCEEDING 4 DAYS")
    with c2:
        adp_vs_paid_hours = st.text_area("ADP vs. Paid Hours Discrepancies (Drivers >10h)")

    st.subheader("🚐 Fleet & Vehicle Health")
    c1, c2 = st.columns(2)
    with c1:
        grounded = st.text_area("Grounded – Names (Reasons)")
    with c2:
        damages = st.number_input("Damages", min_value=0, step=1)

    st.subheader("📌 Escalations & Issues")
    c1, c2, c3 = st.columns(3)
    with c1:
        complaints = st.number_input("Customer Complaints", min_value=0, step=1)
    with c2:
        station_feedback = st.text_area("Amazon Station Feedback (Key issues)")
    with c3:
        route_failures = st.number_input("Route Failures", min_value=0, step=1)

    return {
        "day": day, "the_date": str(the_date),
        "total_routes": total_routes, "amzl_late": amzl_late, "add_routes": add_routes,
        "total_trainings": total_trainings, "total_packages": total_packages,
        "packages_delivered": packages_delivered, "rescues_completed": rescues_completed,
        "rescuing_das": rescuing_das,
        "returned_total": returned_total, "returned_uta": returned_uta,
        "returned_bc": returned_bc, "returned_oodt": returned_oodt, "returned_other": returned_other,
        "violations": violations, "seatbelt": seatbelt, "speeding": speeding, "hard_braking": hard_braking,
        "injuries": injuries, "coaching": coaching,
        "das_exceeding_4_days": das_exceeding_4_days, "adp_vs_paid_hours": adp_vs_paid_hours,
        "grounded": grounded, "damages": damages,
        "complaints": complaints, "station_feedback": station_feedback, "route_failures": route_failures
    }

# ---------- Validation ----------
def validate(entry: Dict) -> List[str]:
    errs = []
    tp = safe_int(entry["total_packages"])
    pdv = safe_int(entry["packages_delivered"])
    rtot = safe_int(entry["returned_total"])
    parts = safe_int(entry["returned_uta"]) + safe_int(entry["returned_bc"]) + safe_int(entry["returned_oodt"]) + safe_int(entry["returned_other"])

    if pdv + rtot > tp:
        errs.append("Packages Delivered + Packages Returned cannot exceed Total Packages.")
    if rtot != parts:
        errs.append(f"Return breakdown ({parts}) must equal Returned total ({rtot}).")
    return errs

# ---------- Exports ----------
def export_excel_row(entry: dict) -> bytes:
    output = io.BytesIO()
    df = pd.DataFrame([entry])[COLUMNS]
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Daily Recap")
    return output.getvalue()


def export_pdf(entry: Dict) -> bytes:
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab not available on this server")
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    y = h - 72
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, f"Daily Operations Recap – {entry['day']} {entry['the_date']}")
    y -= 18
    c.setFont("Helvetica", 10)
    for line in render_message(entry).splitlines():
        if not line.strip():
            y -= 6; continue
        c.drawString(50, y, line[:110]); y -= 12
        if y < 50:
            c.showPage(); c.setFont("Helvetica", 10); y = h - 72
    c.showPage(); c.save()
    return buffer.getvalue()

# ---------- Overview & Message ----------
def render_overview(entry: Dict) -> str:
    total = safe_int(entry["total_packages"])
    delivered = safe_int(entry["packages_delivered"])
    returned = safe_int(entry["returned_total"])
    uta = safe_int(entry["returned_uta"])
    bc = safe_int(entry["returned_bc"])
    oodt = safe_int(entry["returned_oodt"])
    other = safe_int(entry["returned_other"])

    delivery_rate = pct(delivered, total)
    return_rate = pct(returned, total)

    uta_p = pct(uta, max(returned, 1))
    bc_p = pct(bc, max(returned, 1))
    oodt_p = pct(oodt, max(returned, 1))
    other_p = pct(other, max(returned, 1))

    vio_tot = safe_int(entry["violations"])
    seatbelt_p = pct(entry["seatbelt"], max(vio_tot, 1))
    speeding_p = pct(entry["speeding"], max(vio_tot, 1))
    hard_p = pct(entry["hard_braking"], max(vio_tot, 1))

    lines = [
        f"OVERVIEW – {entry['day']} {entry['the_date']}",
        f"• Delivery Rate: {delivery_rate:.1f}%  |  Return Rate: {return_rate:.1f}%  (Delivered {delivered:,} / Total {total:,})",
        f"• Return Breakdown: UTA {uta} ({uta_p:.1f}%) | BC {bc} ({bc_p:.1f}%) | OODT {oodt} ({oodt_p:.1f}%) | Other {other} ({other_p:.1f}%)",
        f"• Violations: {vio_tot}  → Seatbelt {entry['seatbelt']} ({seatbelt_p:.1f}%) | Speeding {entry['speeding']} ({speeding_p:.1f}%) | Hard Braking {entry['hard_braking']} ({hard_p:.1f}%)",
    ]
    return "\n".join(lines)

def render_message(entry: Dict) -> str:
    return f"""📢 Daily Operations Recap – {entry['day']} {entry['the_date']} 📢

📦 Volume & Routes
🔹 Total Routes:  {entry['total_routes']}
🔹 AMZL Late Cancels: {entry['amzl_late']}
🔹 Additional Routes Picked Up:  {entry['add_routes']}
🔹 Total Trainings: {entry['total_trainings']}
🔹 Total Packages: {entry['total_packages']}

🚛 Driver Performance
✅ Packages Delivered: {entry['packages_delivered']}
🔄 Rescues Completed: {entry['rescues_completed']} (By: {entry['rescuing_das']})
📦 Packages Returned: {entry['returned_total']} (UTA: {entry['returned_uta']} | BC: {entry['returned_bc']} | OODT: {entry['returned_oodt']} | Other: {entry['returned_other']})

⚠ Safety & Compliance
🚦 Violations: {entry['violations']} (Seatbelt: {entry['seatbelt']} | Speeding: {entry['speeding']} | Hard Braking: {entry['hard_braking']})
🚑 Injuries: {entry['injuries']} 
📋 Drivers Needing Coaching: {entry['coaching']}

💰 Labor & Cost Metrics
⏳ DAS EXCEEDING 4 DAYS: {entry['das_exceeding_4_days']}
📊 ADP vs. Paid Hours Discrepancies: {entry['adp_vs_paid_hours']}

🚐 Fleet & Vehicle Health
🛑 Grounded: {entry['grounded']}
⚠ Damages: {entry['damages']}

📌 Escalations & Issues
📞 Customer Complaints: {entry['complaints']}
📍 Amazon Station Feedback: {entry['station_feedback']}
⚠ Route Failures: {entry['route_failures']}
"""

# ---------- App ----------
def main():
    st.title("📢 Patel Logistics – Daily Operations Recap")
    auth_gate()

    entry = collect_inputs()

    st.divider()
    # Validate & Save
    save_col, exp_xlsx, exp_pdf, backup_col = st.columns([1,1,1,1])

    with save_col:
        if st.button("💾 Save"):
            errs = validate(entry)
            if errs:
                for e in errs:
                    st.error(e)
            else:
                save_entry(entry)
                st.success("Saved successfully.")

    with exp_xlsx:
        st.download_button(
            "⬇️ Excel (.xlsx)",
            data=export_excel_row(entry),
            file_name=f"daily_recap_{entry['the_date']}.xlsx"
        )

    with exp_pdf:
        if REPORTLAB_AVAILABLE:
            try:
                st.download_button(
                    "⬇️ PDF (.pdf)",
                    data=export_pdf(entry),
                    file_name=f"daily_recap_{entry['the_date']}.pdf"
                )
            except Exception as e:
                st.warning(f"PDF export failed: {e}")
        else:
            st.info("PDF export is unavailable on this server.")

    with backup_col:
        if st.button("🗄 Backup (Sheets)"):
            backup_all()

    st.divider()
    st.subheader("Overview (Percentages)")
    st.text(render_overview(entry))

    st.subheader("Formatted Recap (copy/paste)")
    st.code(render_message(entry))

    st.divider()
    st.subheader("Saved Entries")
    df_all = load_all()
    if not df_all.empty:
        st.dataframe(df_all.tail(15))
    else:
        st.info("No saved rows yet.")

if __name__ == "__main__":
    main()
