# Patel Logistics – Daily Operations Recap (Cloud-safe)
# - Saves rows to local CSV on Streamlit Cloud (ephemeral) أو على جهازك محليًا
# - Excel export works only if an engine is available; otherwise CSV download is shown.

import io
from datetime import date
from typing import Dict, List

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Patel Logistics – Daily Recap", page_icon="📦", layout="centered")

# -------------------- Storage --------------------
CSV_FILE = "daily_recap.csv"

COLUMNS: List[str] = [
    "Date",
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
# We never reference an engine unless its import succeeded.
EXCEL_ENGINE = None
try:
    import openpyxl  # noqa
    EXCEL_ENGINE = "openpyxl"
except Exception:
    try:
        import xlsxwriter  # noqa
        EXCEL_ENGINE = "xlsxwriter"
    except Exception:
        EXCEL_ENGINE = None  # No excel engine; we will fall back to CSV download


# -------------------- Helpers --------------------
def load_data() -> pd.DataFrame:
    try:
        df = pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=COLUMNS)
    # ensure column order
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = ""
    return df[COLUMNS]


def save_row(entry: Dict):
    df = load_data()
    df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)


def export_excel_row(entry: Dict) -> bytes:
    """
    Build a one-row Excel file. Uses openpyxl/xlsxwriter only if the module is available.
    If no engine available, caller should skip offering Excel.
    """
    if not EXCEL_ENGINE:
        raise RuntimeError("No Excel engine available (openpyxl/xlsxwriter).")
    buf = io.BytesIO()
    df = pd.DataFrame([entry])[COLUMNS]
    with pd.ExcelWriter(buf, engine=EXCEL_ENGINE) as writer:
        df.to_excel(writer, index=False, sheet_name="Daily Recap")
    buf.seek(0)
    return buf.getvalue()


def export_csv_row(entry: Dict) -> bytes:
    buf = io.StringIO()
    pd.DataFrame([entry])[COLUMNS].to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


# -------------------- UI --------------------
def main():
    st.title("📦 Patel Logistics – Daily Operations Recap")

    st.subheader("🗓️ General")
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

    # Build entry dict
    entry: Dict = {
        "Date": str(the_date),
        "Total Routes": total_routes,
        "AMZL Late Cancels": amzl_late,
        "Additional Routes Picked Up": add_routes,
        "Total Trainings": total_trainings,
        "Total Packages": total_packages,
        "Packages Delivered": packages_delivered,
        "Rescues Completed": rescues_completed,
        "Rescue Drivers": rescuing_das,
        "Packages Returned": returned_total,
        "UTA": returned_uta, "BC": returned_bc, "OODT": returned_oodt, "Other": returned_other,
        "Violations": violations, "Seatbelt": seatbelt, "Speeding": speeding, "Hard Braking": hard_braking,
        "Injuries": injuries,
        "Drivers Needing Coaching": drivers_coaching, "Coaching Reasons": coaching_reasons,
        "DAs Exceeding 4 Days": das_exceeding, "ADP vs Paid Hours": adp_vs_paid,
        "Grounded Vehicles": grounded, "Grounded Reasons": grounded_reasons, "Damages": damages,
        "Customer Complaints": complaints, "Amazon Station Feedback": station_feedback,
        "Route Failures": route_failures,
    }

    st.divider()

    # Actions row
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

    st.divider()
    st.subheader("Recent Entries")
    df = load_data()
    if df.empty:
        st.info("No rows saved yet.")
    else:
        st.dataframe(df.tail(20), use_container_width=True)


if __name__ == "__main__":
    main()
