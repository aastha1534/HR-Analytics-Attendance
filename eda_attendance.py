"""
eda_attendance.py
-------------------
Exploratory analysis of the AtliQ employee attendance dataset
(Apr-Jun 2022, 74 employees). Produces charts answering:
  - What does the overall attendance mix look like?
  - How does attendance/leave change month over month?
  - Who are the top leave-takers and highest WFH users?
  - Which weekdays see the most leave/WFH?

Run:
    python eda_attendance.py
Outputs (written to ../images/):
    attendance_mix.png
    monthly_trend.png
    top_leave_takers.png
    wfh_leaders.png
    leave_by_weekday.png
    leave_type_breakdown.png
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")
IMG_DIR = "../images/"

daily = pd.read_csv("../data/attendance_daily.csv", parse_dates=["Date"])
monthly = pd.read_csv("../data/attendance_monthly.csv")

MONTH_ORDER = ["Apr 2022", "May 2022", "June 2022"]
monthly["Month"] = pd.Categorical(monthly["Month"], categories=MONTH_ORDER, ordered=True)
daily["Month"] = pd.Categorical(daily["Month"], categories=MONTH_ORDER, ordered=True)

print(f"Employees: {daily['EmployeeCode'].nunique()}  |  Daily records: {len(daily):,}  |  Months: {MONTH_ORDER}")

# ---------------------------------------------------- 1. Attendance mix
status_counts = daily["Status"].value_counts()
top_statuses = status_counts.head(8)
plt.figure(figsize=(7, 5))
sns.barplot(x=top_statuses.values, y=top_statuses.index, color="#3aa0ff")
plt.title("Attendance Status Mix (Apr-Jun 2022)")
plt.xlabel("Days logged")
plt.tight_layout()
plt.savefig(IMG_DIR + "attendance_mix.png", dpi=150)
plt.close()

# ---------------------------------------------------- 2. Monthly trend
trend = monthly.groupby("Month", observed=True).agg(
    avg_present=("Present", "mean"),
    avg_wfh=("WorkFromHome", "mean"),
    avg_leave=("PaidLeave", "mean"),
    avg_sick=("SickLeave", "mean"),
).reset_index()

plt.figure(figsize=(7, 5))
x = np.arange(len(trend))
width = 0.2
plt.bar(x - 1.5*width, trend["avg_present"], width, label="Present", color="#31c48d")
plt.bar(x - 0.5*width, trend["avg_wfh"], width, label="WFH", color="#3aa0ff")
plt.bar(x + 0.5*width, trend["avg_leave"], width, label="Paid Leave", color="#ffb547")
plt.bar(x + 1.5*width, trend["avg_sick"], width, label="Sick Leave", color="#ef5675")
plt.xticks(x, trend["Month"])
plt.ylabel("Avg days per employee")
plt.title("Monthly Attendance Trend (Average per Employee)")
plt.legend()
plt.tight_layout()
plt.savefig(IMG_DIR + "monthly_trend.png", dpi=150)
plt.close()

# ---------------------------------------------------- 3. Top leave-takers
leave_cols = ["PaidLeave", "SickLeave", "LeaveWithoutPay", "BereavementLeave",
              "BirthdayLeave", "FloatingFestivalLeave", "MenstrualLeave"]
monthly["TotalLeave"] = monthly[leave_cols].sum(axis=1)
top_leave = monthly.groupby(["EmployeeCode", "Name"], observed=True)["TotalLeave"].sum().sort_values(ascending=False).head(10)

plt.figure(figsize=(7, 5))
sns.barplot(x=top_leave.values, y=[n for _, n in top_leave.index], color="#ef5675")
plt.title("Top 10 Employees by Total Leave Days (Apr-Jun 2022)")
plt.xlabel("Total leave days")
plt.tight_layout()
plt.savefig(IMG_DIR + "top_leave_takers.png", dpi=150)
plt.close()

# ---------------------------------------------------- 4. WFH leaders
monthly["DaysWorked"] = monthly["Present"] + monthly["WorkFromHome"]
monthly["WFHPct"] = (monthly["WorkFromHome"] / monthly["DaysWorked"].replace(0, np.nan)) * 100
wfh_summary = monthly.groupby(["EmployeeCode", "Name"], observed=True).agg(
    total_wfh=("WorkFromHome", "sum"), total_present=("Present", "sum")
).reset_index()
wfh_summary["wfh_pct"] = 100 * wfh_summary["total_wfh"] / (wfh_summary["total_wfh"] + wfh_summary["total_present"]).replace(0, np.nan)
top_wfh = wfh_summary.sort_values("wfh_pct", ascending=False).head(10)

plt.figure(figsize=(7, 5))
sns.barplot(x=top_wfh["wfh_pct"], y=top_wfh["Name"], color="#3aa0ff")
plt.title("Top 10 Employees by Work-From-Home %")
plt.xlabel("WFH % of days worked")
plt.tight_layout()
plt.savefig(IMG_DIR + "wfh_leaders.png", dpi=150)
plt.close()

# ---------------------------------------------------- 5. Leave by weekday
non_wo = daily[~daily["Status"].isin(["WO", "HO"])].copy()
non_wo["DayOfWeek"] = non_wo["Date"].dt.day_name()
leave_statuses = ["PL", "SL", "LWP", "BRL", "BL", "FFL", "ML", "HPL", "HSL", "HLWP"]
leave_by_day = non_wo[non_wo["Status"].isin(leave_statuses)]["DayOfWeek"].value_counts()
day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
leave_by_day = leave_by_day.reindex(day_order).fillna(0)

plt.figure(figsize=(7, 5))
sns.barplot(x=leave_by_day.index, y=leave_by_day.values, color="#ffb547")
plt.title("Leave Requests by Day of Week")
plt.ylabel("Leave instances")
plt.tight_layout()
plt.savefig(IMG_DIR + "leave_by_weekday.png", dpi=150)
plt.close()

# ---------------------------------------------------- 6. Leave type breakdown
leave_totals = monthly[leave_cols].sum().sort_values(ascending=False)
leave_totals = leave_totals[leave_totals > 0]
plt.figure(figsize=(6, 6))
plt.pie(leave_totals.values, labels=leave_totals.index, autopct="%1.1f%%",
        colors=sns.color_palette("Set2", len(leave_totals)))
plt.title("Leave Type Breakdown (Apr-Jun 2022)")
plt.tight_layout()
plt.savefig(IMG_DIR + "leave_type_breakdown.png", dpi=150)
plt.close()

# ---------------------------------------------------- Summary file
with open("../images/attendance_summary.txt", "w") as f:
    f.write("HR ATTENDANCE ANALYSIS SUMMARY\n")
    f.write("================================\n\n")
    f.write(f"Employees tracked: {daily['EmployeeCode'].nunique()}\n")
    f.write(f"Months covered: {', '.join(MONTH_ORDER)}\n\n")
    f.write("Top 5 leave-takers:\n")
    for (code, name), val in top_leave.head(5).items():
        f.write(f"  {name} ({code}): {val} days\n")
    f.write("\nTop 5 WFH users:\n")
    for _, row in top_wfh.head(5).iterrows():
        f.write(f"  {row['Name']} ({row['EmployeeCode']}): {row['wfh_pct']:.1f}%\n")
    f.write("\nMonthly average days present per employee:\n")
    for _, row in trend.iterrows():
        f.write(f"  {row['Month']}: {row['avg_present']:.1f} present, {row['avg_wfh']:.1f} WFH\n")

print("\nAll charts saved to ../images/")
