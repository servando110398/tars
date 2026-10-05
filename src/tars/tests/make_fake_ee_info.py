"""Generate a fake EE_Info file with the same columns and types as the real export.

Writes an .xlsx next to this script. The real files are legacy .xls, which pandas
can't write, so convert the .xlsx with Excel (Save As "Excel 97-2003 Workbook").

Run with: uv run python src/tars/tests/make_fake_ee_info.py
"""
from pathlib import Path

import pandas as pd
from faker import Faker

ROWS = 25
OUTPUT = Path(__file__).parent / "test_files" / "fake_ee_info.xlsx"

fake = Faker()
Faker.seed(42)  # same fake data on every run, so tests stay repeatable
rng = fake.random

STATUSES = [("A1", "Active Full Time"), ("A2", "Active Part Time"), ("PR", "PRN"), ("L1", "Leave of Absence")]
DEPTS = [(6010, "Radiology"), (6120, "Pharmacy"), (6230, "Intensive Care Unit"), (6340, "Emergency Department"), (8010, "Finance")]
SHIFTS = ["Day", "Evening", "Night", "Rotating"]
JOBS = [(4101, "Registered Nurse", 1, 1), (4205, "Pharmacy Technician", 0, 0), (4310, "Radiology Technologist", 0, 0), (5120, "Financial Analyst", 0, 0)]
ACCOUNTS = [50100, 50200, 50300]


def fake_employee() -> dict:
    status, description = rng.choice(STATUSES)
    dept, dept_name = rng.choice(DEPTS)
    shift = rng.choice(SHIFTS)
    job_class, job_title, rn_bedside, rn_lic = rng.choice(JOBS)
    pp_hrs = rng.choice([80, 72, 64, 40])
    hire_date = fake.date_between("-25y", "-1y")
    trained = rng.choice([0, 1, 1, 1])
    terminated = rng.random() < 0.05

    return {
        "Employee": fake.unique.random_int(100000, 999999),
        "Last Name": fake.last_name(),
        "First Name": fake.first_name(),
        "Hire Date": pd.Timestamp(hire_date),
        "Adj_Hire_Date": pd.Timestamp(fake.date_between(hire_date, "today")),
        "Status": status,
        "Description": description,
        "Dept": dept,
        "Dept Name": dept_name,
        "Daily Hrs": rng.choice([7.5, 8.0, 8.5, 10.0, 12.0]),
        "Shift": shift,
        "PP Hrs": pp_hrs,
        "FTE": round(pp_hrs / 80, 2),
        "Position Code": fake.random_int(10000, 99999),
        "Job Title": job_title,
        "Job Class": job_class,
        "RN Bedside": rn_bedside,
        "RN Lic": rn_lic,
        "Exempt": "Y" if job_class == 5120 else "N",
        "EXP_ACCT_UNIT": dept,
        "EXP_ACCOUNT": rng.choice(ACCOUNTS),
        "Evening_Shfit": int(shift == "Evening"),
        "ShiftNight_Shfit": int(shift == "Night"),
        "Term Date": pd.Timestamp(fake.date_between("-90d", "today")) if terminated else pd.NaT,
        "Supervisor": fake.name(),
        "Chief": fake.name() if rng.random() > 0.02 else None,
        "HRO_Trainer_Trained": 0,
        "HRO_Staff_Trained": trained,
        "HRO_Staff_Trained_Date": pd.Timestamp(fake.date_between("-2y", "today")) if trained else pd.NaT,
    }


if __name__ == "__main__":
    df = pd.DataFrame([fake_employee() for _ in range(ROWS)])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(OUTPUT, index=False, sheet_name="Sheet1")
    print(f"Wrote {len(df)} fake rows x {df.shape[1]} columns to {OUTPUT}")
