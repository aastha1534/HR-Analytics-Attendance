"""
consolidate_attendance.py
--------------------------
Consolidates the raw AtliQ attendance workbook (one sheet per month, with
per-day attendance codes + a monthly summary block) into two clean,
analysis-ready CSVs:

  1. data/attendance_daily.csv    — long format: EmployeeCode, Name, Date, Status
  2. data/attendance_monthly.csv  — one row per employee per month, with
                                     Present/WFH/PaidLeave/SickLeave/etc. totals

Source: data/Attendance-Sheet-2022-2023.xlsx (as uploaded, copied verbatim
into data/ for provenance)

Run:
    python consolidate_attendance.py
"""

import pandas as pd

import datetime as dt

SRC = "../data/Attendance-Sheet-2022-2023.xlsx"
MONTH_SHEETS = ["Apr 2022", "May 2022", "June 2022"]

SUMMARY_COLS = {
    "TPD": "TotalPresentDays",
    "P": "Present",
    "WFH": "WorkFromHome",
    "PL": "PaidLeave",
    "SL": "SickLeave",
    "BL": "BirthdayLeave",
    "FFL": "FloatingFestivalLeave",
    "BRL": "BereavementLeave",
    "LWP": "LeaveWithoutPay",
    "WO": "WeeklyOff",
    "HO": "HolidayOff",
    "ML": "MenstrualLeave",
}

daily_records = []
monthly_records = []

for sheet in MONTH_SHEETS:
    df = pd.read_excel(SRC, sheet_name=sheet, header=1,
                        engine="openpyxl", engine_kwargs={"data_only": True})
    df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]
    df = df.dropna(subset=["Employee Code"]).copy()
    df["Employee Code"] = df["Employee Code"].astype(str).str.strip()
    df["Name"] = df["Name"].astype(str).str.strip()

    date_cols = [c for c in df.columns if isinstance(c, dt.datetime)]
    # The sheet includes one extra trailing date column that rolls into the
    # next month (an artifact of the template) — drop duplicate/out-of-month dates
    month_num = pd.to_datetime(date_cols[0]).month
    date_cols = [c for c in date_cols if pd.to_datetime(c).month == month_num]

    # ---- long-format daily attendance ----
    long_df = df.melt(
        id_vars=["Employee Code", "Name"],
        value_vars=date_cols,
        var_name="Date",
        value_name="Status"
    )
    long_df = long_df.dropna(subset=["Status"])
    long_df["Month"] = sheet
    daily_records.append(long_df)

    # ---- monthly summary ----
    summary_cols_present = [c for c in SUMMARY_COLS if c in df.columns]
    monthly = df[["Employee Code", "Name"] + summary_cols_present].copy()
    monthly = monthly.rename(columns=SUMMARY_COLS)
    monthly["Month"] = sheet
    monthly_records.append(monthly)

daily_df = pd.concat(daily_records, ignore_index=True)
daily_df["Date"] = pd.to_datetime(daily_df["Date"]).dt.date
daily_df = daily_df.rename(columns={"Employee Code": "EmployeeCode"})
daily_df.to_csv("../data/attendance_daily.csv", index=False)

monthly_df = pd.concat(monthly_records, ignore_index=True)
monthly_df = monthly_df.rename(columns={"Employee Code": "EmployeeCode"})
# column order: identifiers, month, then metrics
metric_cols = [c for c in monthly_df.columns if c not in ("EmployeeCode", "Name", "Month")]
monthly_df = monthly_df[["EmployeeCode", "Name", "Month"] + metric_cols]
monthly_df.to_csv("../data/attendance_monthly.csv", index=False)

print(f"Daily records:   {len(daily_df):,} rows -> data/attendance_daily.csv")
print(f"Monthly records: {len(monthly_df):,} rows -> data/attendance_monthly.csv")
print(f"Employees: {daily_df['EmployeeCode'].nunique()}")
print(f"Months: {monthly_df['Month'].unique().tolist()}")
print("\nStatus code distribution:")
print(daily_df["Status"].value_counts())
