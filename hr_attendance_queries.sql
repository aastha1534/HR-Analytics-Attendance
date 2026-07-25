/* =====================================================================
   HR ATTENDANCE ANALYTICS — SQL QUERIES
   Source  : AtliQ attendance dataset (Apr–Jun 2022, 74 employees)
   Tables  : attendance_daily   (EmployeeCode, Name, Date, Status, Month)
             attendance_monthly (EmployeeCode, Name, Month, TotalPresentDays,
                                  Present, WorkFromHome, PaidLeave, SickLeave,
                                  BirthdayLeave, FloatingFestivalLeave,
                                  BereavementLeave, LeaveWithoutPay,
                                  WeeklyOff, HolidayOff, MenstrualLeave)
   Dialect : ANSI SQL — tested on SQLite, works on MySQL / PostgreSQL /
             SQL Server / BigQuery with only minor syntax tweaks.

   Load into SQLite quickly (from the /python folder, after running
   consolidate_attendance.py):
     python -c "
       import sqlite3, pandas as pd
       d = pd.read_csv('../data/attendance_daily.csv')
       m = pd.read_csv('../data/attendance_monthly.csv')
       con = sqlite3.connect('../data/hr.db')
       d.to_sql('attendance_daily', con, index=False, if_exists='replace')
       m.to_sql('attendance_monthly', con, index=False, if_exists='replace')
     "
   ===================================================================== */

-- 1. Headcount and total working days tracked ----------------------------
SELECT
    COUNT(DISTINCT EmployeeCode)                          AS total_employees,
    COUNT(DISTINCT Month)                                 AS months_tracked,
    COUNT(*)                                               AS total_daily_records
FROM attendance_daily;

-- 2. Overall attendance mix (% of all tracked days by status) -----------
SELECT
    Status,
    COUNT(*)                                               AS days,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM attendance_daily), 2) AS pct_of_all_days
FROM attendance_daily
GROUP BY Status
ORDER BY days DESC;

-- 3. Average monthly attendance rate (Present+WFH / working days) -------
SELECT
    Month,
    ROUND(AVG(Present + WorkFromHome), 2)                  AS avg_days_worked,
    ROUND(AVG(TotalPresentDays), 2)                        AS avg_total_present_days,
    ROUND(AVG(PaidLeave + SickLeave + LeaveWithoutPay), 2) AS avg_leave_days
FROM attendance_monthly
GROUP BY Month;

-- 4. Top 10 employees by total leave taken (all types, across all months) --
SELECT
    EmployeeCode,
    Name,
    ROUND(SUM(PaidLeave + SickLeave + LeaveWithoutPay + BereavementLeave
             + BirthdayLeave + FloatingFestivalLeave + MenstrualLeave), 1) AS total_leave_days,
    ROUND(SUM(WorkFromHome), 1)                             AS total_wfh_days,
    ROUND(SUM(Present), 1)                                  AS total_present_days
FROM attendance_monthly
GROUP BY EmployeeCode, Name
ORDER BY total_leave_days DESC
LIMIT 10;

-- 5. Employees most likely to work from home (WFH as % of days worked) ---
SELECT
    EmployeeCode,
    Name,
    ROUND(SUM(WorkFromHome), 1)                             AS total_wfh,
    ROUND(SUM(Present), 1)                                  AS total_present,
    ROUND(100.0 * SUM(WorkFromHome) / NULLIF(SUM(Present) + SUM(WorkFromHome), 0), 1) AS wfh_pct
FROM attendance_monthly
GROUP BY EmployeeCode, Name
HAVING (SUM(Present) + SUM(WorkFromHome)) > 0
ORDER BY wfh_pct DESC
LIMIT 15;

-- 6. Leave-without-pay (LWP) — a proxy for disengagement/flight risk -----
SELECT
    EmployeeCode,
    Name,
    Month,
    LeaveWithoutPay
FROM attendance_monthly
WHERE LeaveWithoutPay > 0
ORDER BY LeaveWithoutPay DESC, Month;

-- 7. Sick leave trend by month (possible burnout / seasonal illness signal) --
SELECT
    Month,
    ROUND(SUM(SickLeave), 1)                                AS total_sick_days,
    ROUND(AVG(SickLeave), 2)                                AS avg_sick_days_per_employee,
    COUNT(DISTINCT CASE WHEN SickLeave > 0 THEN EmployeeCode END) AS employees_with_sick_leave
FROM attendance_monthly
GROUP BY Month;

-- 8. Perfect attendance (zero leave of any kind, full month) ------------
SELECT
    EmployeeCode,
    Name,
    Month
FROM attendance_monthly
WHERE PaidLeave = 0 AND SickLeave = 0 AND LeaveWithoutPay = 0
  AND BereavementLeave = 0 AND BirthdayLeave = 0
  AND FloatingFestivalLeave = 0 AND MenstrualLeave = 0
ORDER BY Month, Name;

-- 9. Day-of-week attendance pattern (which weekdays see the most WFH/leave) --
SELECT
    CASE CAST(strftime('%w', Date) AS INTEGER)
        WHEN 0 THEN 'Sunday' WHEN 1 THEN 'Monday' WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday' WHEN 4 THEN 'Thursday' WHEN 5 THEN 'Friday'
        ELSE 'Saturday' END                                 AS day_of_week,
    Status,
    COUNT(*)                                                AS occurrences
FROM attendance_daily
WHERE Status NOT IN ('WO', 'HO')
GROUP BY day_of_week, Status
ORDER BY occurrences DESC
LIMIT 20;

-- 10. Month-over-month attendance rate change per employee ---------------
WITH pivoted AS (
    SELECT
        EmployeeCode, Name, Month,
        ROUND(100.0 * (Present + WorkFromHome) /
              NULLIF(Present + WorkFromHome + PaidLeave + SickLeave + LeaveWithoutPay
                     + BereavementLeave + BirthdayLeave + FloatingFestivalLeave + MenstrualLeave, 0), 1) AS attendance_rate_pct
    FROM attendance_monthly
)
SELECT * FROM pivoted
ORDER BY EmployeeCode,
    CASE Month WHEN 'Apr 2022' THEN 1 WHEN 'May 2022' THEN 2 WHEN 'June 2022' THEN 3 END;

-- 11. Half-day usage (HPL, HSL, HLWP, etc.) — granular leave behavior ----
SELECT
    Status,
    COUNT(*)                                                AS occurrences,
    COUNT(DISTINCT EmployeeCode)                            AS distinct_employees
FROM attendance_daily
WHERE Status LIKE 'H%'
GROUP BY Status
ORDER BY occurrences DESC;

-- 12. Weekly-off + holiday coverage check (data quality sanity check) ----
SELECT
    Month,
    SUM(CASE WHEN Status = 'WO' THEN 1 ELSE 0 END)          AS weekly_off_days_logged,
    SUM(CASE WHEN Status = 'HO' THEN 1 ELSE 0 END)          AS holiday_days_logged
FROM attendance_daily
GROUP BY Month;
