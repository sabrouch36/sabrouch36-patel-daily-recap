# Patel Logistics – Daily Operations Recap (Cloud-safe, no charts/PDF)
# - Day field, Overview (percentages), and Final Recap text included
# - Excel export if an engine is available, otherwise CSV export
# - Local CSV storage (on cloud it is ephemeral; for persistence use Google Sheets later)

import io
from datetime import date
from typing import Dict, List

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Patel Logistics – Daily Recap", page_icon="📦", layout="centered")

# -------------------- Storage --------------------
CSV_FILE = "daily_recap.csv"

COLUMNS: List[str] = [
    "Day", "Date",
    "Total Routes", "AMZL Late Cancels", "Additional Routes Picked Up",
    "Total Trainings", "Total Packages",
    "Packages Delivered", "Rescues Completed", "Rescue Drivers",
    "Packages Returned", "UTA", "BC", "OODT", "Other",
    "Violations", "Seatbelt", "Speeding", "Hard Braking",
    "Injuries", "Drivers Needing Coaching", "Coaching Reasons",
    "DAs Exceeding 4 Days", "ADP vs Paid Hours",
    "Grounded Vehicles", "Grounded Reasons", "Damages",
    "Customer Complaints", "Amazon Station Feedback", "Route Failures",
]

# -------------------- Excel engine detection --------------------
EXCEL_ENGINE = None
try:
    import openpyxl  # noqa
    EXCEL_ENGINE = "openpyxl"
except Exception:
    try:
        import xlsxwriter  # noqa
        EXCEL_ENGINE = "xlsxwriter"
    except Exception:
        EXCEL_ENGINE = None  # We'll fall back to CSV download

# -------------------- Helpers --------------------
def safe_int(x) -> int:
    try:
        return int(x)
    except Exception:
        return 0

def pct(n, d) -> float:
    n = safe_int(n); d = safe_int(d)
    return 0.0 if d == 0 else (n / d) * 100.0

def load_data() -> pd.DataFrame:
    try:
        df = pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=COLUMNS)
    # ensure column order/superset
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = ""
    return df[COLUMNS]

def save_row(entry: Dict):
    df = load_data()
    df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)

def export_excel_row(entry: Dict) -> bytes:
    if not EXCEL_ENGINE:
        raise RuntimeError("No Excel engine available (openpyxl/xlsxwriter).")
    buf = io.BytesIO()
    pd.DataFrame([entry])[COLUMNS].to_excel(
        pd.ExcelWriter(buf, engine=EXCEL_ENGINE),
        index=False, sheet_name="Daily Recap"
    )
    # Close writer by exiting context:
    # Using explicit context to avoid ResourceWarning on some hosts
    buf.seek(0)
    return buf.getvalue()

def export_csv_row(entry: Dict) -> bytes:
    s = io.StringIO()
    pd.DataFrame([entry])[COLUMNS].to_csv(s, index=False)
    return s.getvalue().encode("utf-8")

def build_overview(entry: Dict) -> str:
    total = safe_int(entry["Total Packages"])
    delivered = safe_int(entry["Packages Delivered"])
    returned = safe_int(entry["Packages Returned"])
    uta = safe_int(entry["UTA"]); bc = safe_int(entry["BC"])
    oodt = safe_int(entry["OODT"]); other = safe_int(entry["Other"])

    delivery_rate = pct(delivered, total)
    return_rate = pct(returned, total)

    uta_p = pct(uta, max(returned, 1))
    bc_p = pct(bc, max(returned, 1))
    oodt_p = pct(oodt, max(returned, 1))
    other_p = pct(other, max(returned, 1))

    vio = safe_int(entry["Violations"])
    seatbelt_p = pct(entry["Seatbelt"], max(vio, 1))
    speeding_p = pct(entry["Speeding"], max(vio, 1))
    hard_p = pct(entry["Hard Braking"], max(vio, 1))

    lines = [
        f"OVERVIEW – {entry['Day']} {entry['Date']}",
        f"• Delivery Rate: {delivery_rate:.1f}%  |  Return Rate: {return_rate:.1f}%  "
        f"(Delivered {delivered:,} / Total {total:,})",
        f"• Return Breakdown: UTA {uta} ({uta_p:.1f}%) | BC {bc} ({bc_p:.1f}%) | "
        f"OODT {oodt} ({oodt_p:.1f}%) | Other {other} ({other_p:.1f}%)",
        f"• Violations: {vio} → Seatbelt {entry['Seatbelt']} ({seatbelt_p:.1f}%) | "
        f"Speeding {entry['Speeding']} ({speeding_p:.1f}%) | Hard Braking {entry['Hard Braking']} ({hard_p:.1f}%)",
    ]
    return "\n".join(lines)

def build_recap_text(entry: Dict) -> str:
    # Copy/paste friendly message exactly in your template
    return f"""📢 Daily Operations Recap – {entry['Day']} {entry['Date']} 📢

📦 Volume & Routes
🔹 Total Routes:  {entry['Total Routes']}
🔹 AMZL Late Cancels: {entry['AMZL Late Cancels']}
🔹 Additional Routes Picked Up:  {entry['Additional Routes Picked Up']}
🔹 Total Trainings: {entry['Total Trainings']}
🔹 Total Packages: {entry['Total Packages']}

🚛 Driver Performance
✅ Packages Delivered: {entry['Packages Delivered']}
🔄 Rescues Completed: {entry['Rescues Completed']} (By: {entry['Rescue Drivers']})
📦 Packages Returned: {entry['Packages Returned']} (UTA: {entry['UTA']} | BC: {entry['BC']} | OODT: {entry['OODT']} | Other: {entry['Other']})

⚠ Safety & Compliance
🚦 Violations: {entry['Violations']} (Seatbelt: {entry['Seatbelt']} | Speeding: {entry['Speeding']} | Hard Braking: {entry['Hard Braking']})
🚑 Injuries: {entry['Injuries']} 
📋 Drivers Needing Coaching: {entry['Drivers Needing Coaching']} (Reasons: {entry['Coaching Reasons']})

💰 Labor & Cost Metrics
⏳ DAS EXCEEDING 4 DAYS: {entry['DAs Exceeding 4 Days']}
📊 ADP vs. Paid Hours Discrepancies: {entry['ADP vs Paid Hours']}

🚐 Fleet & Vehicle Health
🛑 Grounded: {entry['Grounded Vehicles']} (Reasons: {entry['Grounded Reasons']})
⚠ Damages: {entry['Damages']}

📌 Escalations & Issues
📞 Customer Complaints: {entry['Customer Complaints']}
📍 Amazon Station Feedback: {entry['Amazon Station Feedback']}
⚠ Route Failures: {entry['Route Failures']}
"""

# -------------------- App --------------------
def main():
    st.title("📦 Patel Logistics – Daily Operations Recap")

    # Header
    st.subheader("🗓️ General")
    day = st.selectbox("Day", ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    the_date = st.date_input("Date", value=date.today())

    st.subheader("🚛 Volume & Routes")
    total_routes = st.number_input("Total Routes", min_value=0, step=1)
    amzl_late = st.number_input("AMZL Late Cancels", min_value=0, step=1)
    add_routes = st.number_input("Additional Routes Picked Up", min_value=0, step=1)
    total_trainings = st.text_input("Total Trainings (names/dayX)")
    total_packages = st.number_input("Total Packages", min_value=0, step=1)

    st.subheader("👷 Driver Performance")
    packages_delivered = st.number_input("Packages Delivered", min_value=0, step=1)
    rescues_completed = st.number_input("Rescues Completed", min_value=0, step=1)
    rescuing_das = st.text_input("Rescue Drivers (names)")
    returned_total = st.number_input("Packages Returned (Total)", min_value=0, step=1)
    returned_uta = st.number_input("Returned – UTA", min_value=0, step=1)
    returned_bc = st.number_input("Returned – BC", min_value=0, step=1)
    returned_oodt = st.number_input("Returned – OODT", min_value=0, step=1)
    returned_other = st.number_input("Returned – Other", min_value=0, step=1)

    st.subheader("⚠️ Safety & Compliance")
    violations = st.number_input("Violations (Total)", min_value=0, step=1)
    seatbelt = st.number_input("Seatbelt", min_value=0, step=1)
    speeding = st.number_input("Speeding", min_value=0, step=1)
    hard_braking = st.number_input("Hard Braking", min_value=0, step=1)
    injuries = st.number_input("Injuries", min_value=0, step=1)
    drivers_coaching = st.text_input("Drivers Needing Coaching")
    coaching_reasons = st.text_input("Coaching Reasons")

    st.subheader("💰 Labor & Cost Metrics")
    das_exceeding = st.text_input("DAs Exceeding 4 Days")
    adp_vs_paid = st.text_input("ADP vs. Paid Hours Discrepancies (>10h)")

    st.subheader("🚐 Fleet & Vehicle Health")
    grounded = st.text_input("Grounded Vehicles (names)")
    grounded_reasons = st.text_input("Grounded Reasons")
    damages = st.number_input("Damages", min_value=0, step=1)

    st.subheader("📌 Escalations & Issues")
    complaints = st.number_input("Customer Complaints", min_value=0, step=1)
    station_feedback = st.text_area("Amazon Station Feedback (key issues)")
    route_failures = st.number_input("Route Failures", min_value=0, step=1)

    # Build entry
    entry: Dict = {
        "Day": day, "Date": str(the_date),
        "Total Routes": total_routes, "AMZL Late Cancels": amzl_late, "Additional Routes Picked Up": add_routes,
        "Total Trainings": total_trainings, "Total Packages": total_packages,
        "Packages Delivered": packages_delivered, "Rescues Completed": rescues_completed, "Rescue Drivers": rescuing_das,
        "Packages Returned": returned_total, "UTA": returned_uta, "BC": returned_bc, "OODT": returned_oodt, "Other": returned_other,
        "Violations": violations, "Seatbelt": seatbelt, "Speeding": speeding, "Hard Braking": hard_braking,
        "Injuries": injuries, "Drivers Needing Coaching": drivers_coaching, "Coaching Reasons": coaching_reasons,
        "DAs Exceeding 4 Days": das_exceeding, "ADP vs Paid Hours": adp_vs_paid,
        "Grounded Vehicles": grounded, "Grounded Reasons": grounded_reasons, "Damages": damages,
        "Customer Complaints": complaints, "Amazon Station Feedback": station_feedback, "Route Failures": route_failures,
    }

    st.divider()

    # Actions: Save / Export
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💾 Save"):
            save_row(entry)
            st.success("Saved successfully.")

    with c2:
        if EXCEL_ENGINE:
            st.download_button(
                "⬇️ Download Excel (.xlsx)",
                data=export_excel_row(entry),
                file_name=f"daily_recap_{entry['Date']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.info("Excel export is unavailable on this server. Use CSV below.")

    with c3:
        st.download_button(
            "⬇️ Download CSV (.csv)",
            data=export_csv_row(entry),
            file_name=f"daily_recap_{entry['Date']}.csv",
            mime="text/csv",
        )

    # Overview (percentages)
    st.divider()
    st.subheader("Overview (Percentages)")
    st.text(build_overview(entry))

    # Final recap text (copy/paste)
    st.subheader("Formatted Recap (copy & paste)")
    st.code(build_recap_text(entry))

    # Recent entries
    st.divider()
    st.subheader("Recent Entries")
    df = load_data()
    if df.empty:
        st.info("No rows saved yet.")
    else:
        st.dataframe(df.tail(20), use_container_width=True)


if __name__ == "__main__":
    main()
