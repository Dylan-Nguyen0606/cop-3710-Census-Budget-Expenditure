
import csv
import argparse
import sys
from pathlib import Path

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:
    sys.exit(
        "ERROR: mysql-connector-python is not installed.\n"
        "Fix:   pip install mysql-connector-python"
    )

# ── CLI ───────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Load Census Budget CSV data into MySQL.")
parser.add_argument("--host",     default="localhost", help="MySQL host (default: localhost)")
parser.add_argument("--port",     type=int, default=3306, help="MySQL port (default: 3306)")
parser.add_argument("--user",     default="root",      help="MySQL user (default: root)")
parser.add_argument("--password", default="",          help="MySQL password (default: empty)")
args = parser.parse_args()

DATA_DIR = Path("data")

# ── connection ────────────────────────────────────────────────────────────────
print(f"\nConnecting to MySQL at {args.host}:{args.port} as '{args.user}' ...")
try:
    conn = mysql.connector.connect(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database="census_budget",
    )
except MySQLError as err:
    sys.exit(
        f"\nConnection failed: {err}\n"
        "Ensure MySql is running"
    )

cur = conn.cursor()
print("Connected successfully.\n")

# Disable FK checks so tables can be (re)loaded safely
cur.execute("SET FOREIGN_KEY_CHECKS = 0;")

# ── helper ────────────────────────────────────────────────────────────────────
def truncate_and_load(csv_file, table, columns):
    path = DATA_DIR / csv_file
    if not path.exists():
        print(f"  WARNING: {csv_file} not found - skipped.")
        return 0

    cur.execute(f"TRUNCATE TABLE {table};")

    placeholders = ", ".join(["%s"] * len(columns))
    col_names    = ", ".join(columns)
    sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"

    rows_inserted = 0
    errors        = 0
    batch         = []

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert empty strings to NULL; strip whitespace
            values = tuple(
                None if row[c].strip() == "" else row[c].strip()
                for c in columns
            )
            batch.append(values)

            if len(batch) >= 500:
                try:
                    cur.executemany(sql, batch)
                    rows_inserted += len(batch)
                except MySQLError as e:
                    print(f"    ERROR in {table}: {e}")
                    errors += len(batch)
                batch = []

    if batch:
        try:
            cur.executemany(sql, batch)
            rows_inserted += len(batch)
        except MySQLError as e:
            print(f"    ERROR (final batch) in {table}: {e}")
            errors += len(batch)

    conn.commit()

    status = "OK" if errors == 0 else "WARN"
    print(f"  [{status}]  {table:<32}  {rows_inserted:>5} rows loaded"
          + (f"  ({errors} errors)" if errors else ""))
    return rows_inserted

# ── load order ──────────────────────────────────────
print("Loading tables ...\n")
total_rows = 0

total_rows += truncate_and_load("survey.csv", "SURVEY",
    ["survey_id", "survey_name", "survey_type", "frequency", "sponsor_agency"])

total_rows += truncate_and_load("survey_year.csv", "SURVEY_YEAR",
    ["year_id", "survey_id", "reference_year", "release_date"])

total_rows += truncate_and_load("naics_industry.csv", "NAICS_INDUSTRY",
    ["naics_code", "parent_naics_code", "sector_code", "industry_title", "hierarchy_level"])

total_rows += truncate_and_load("geographic_area.csv", "GEOGRAPHIC_AREA",
    ["geo_id", "geo_type", "state_fips", "county_fips", "msa_code", "region_name"])

total_rows += truncate_and_load("business_establishment.csv", "BUSINESS_ESTABLISHMENT",
    ["establishment_id", "naics_code", "geo_id", "survey_id",
     "employer_size_class", "num_employees", "annual_revenue", "legal_form"])

total_rows += truncate_and_load("expenditure_record.csv", "EXPENDITURE_RECORD",
    ["record_id", "establishment_id", "year_id", "naics_code", "geo_id",
     "total_expenditures", "data_quality_flag", "suppression_flag", "relative_std_error"])

total_rows += truncate_and_load("capital_expenditure.csv", "CAPITAL_EXPENDITURE",
    ["capex_id", "record_id", "new_structures", "used_structures",
     "new_machinery_equip", "software_capitalized", "leased_owned_land", "total_capex"])

total_rows += truncate_and_load("operating_expense.csv", "OPERATING_EXPENSE",
    ["opex_id", "record_id", "rent_lease_payments", "communication_costs",
     "health_insurance", "legal_accounting", "rd_expenditure", "total_operating_exp"])

total_rows += truncate_and_load("payroll.csv", "PAYROLL",
    ["payroll_id", "record_id", "annual_payroll", "q1_payroll",
     "fringe_benefits", "employer_pension", "workers_comp", "num_paid_employees"])

# ── re-enable FK checks and verify counts ────────────────────────────────────
cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
conn.commit()

print("\n-- Verification --")
tables = [
    "SURVEY", "SURVEY_YEAR", "NAICS_INDUSTRY", "GEOGRAPHIC_AREA",
    "BUSINESS_ESTABLISHMENT", "EXPENDITURE_RECORD",
    "CAPITAL_EXPENDITURE", "OPERATING_EXPENSE", "PAYROLL"
]
for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM {t};")
    count = cur.fetchone()[0]
    print(f"  {t:<32}  {count:>5} rows in DB")

cur.close()
conn.close()

print(f"\nDone. {total_rows} total rows loaded across {len(tables)} tables.")
