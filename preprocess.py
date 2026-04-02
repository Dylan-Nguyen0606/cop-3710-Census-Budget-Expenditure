
import csv
import os
import random
import datetime
from pathlib import Path

random.seed(42)          # reproducibility
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# ── helpers ──────────────────────────────────────────────────────────────────

def rand_decimal(lo, hi, decimals=2):
    return round(random.uniform(lo, hi), decimals)

def write_csv(filename, fieldnames, rows):
    path = DATA_DIR / filename
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  ✓  {path}  ({len(rows)} rows)")

# 1. SURVEY
SURVEY_TYPES  = ["Annual","Quinquennial","Decennial","Monthly","Quarterly"]
FREQUENCIES   = ["Annual","Biennial","Quinquennial","Monthly","Quarterly","Decennial"]
AGENCIES      = [
    "U.S. Census Bureau","Bureau of Labor Statistics","Bureau of Economic Analysis",
    "Small Business Administration","National Science Foundation",
    "Department of Commerce","IRS Statistics of Income","Federal Reserve Board",
]
SURVEY_NAMES  = [
    "Annual Business Survey","Annual Capital Expenditure Survey",
    "Business Expenditures Survey","Annual Survey of Manufactures",
    "Service Annual Survey","Economic Census","Quarterly Financial Report",
    "Business R&D and Innovation Survey","Statistics of U.S. Businesses",
    "County Business Patterns","Survey of Business Owners","Annual Retail Trade Survey",
]

survey_rows = []
for sid in range(1, 101):
    survey_rows.append({
        "survey_id":      sid,
        "survey_name":    SURVEY_NAMES[sid % len(SURVEY_NAMES)] + f" {sid}",
        "survey_type":    random.choice(SURVEY_TYPES),
        "frequency":      random.choice(FREQUENCIES),
        "sponsor_agency": random.choice(AGENCIES),
    })
write_csv("survey.csv", ["survey_id","survey_name","survey_type","frequency","sponsor_agency"], survey_rows)
survey_ids = [r["survey_id"] for r in survey_rows]

# 2. SURVEY_YEAR
survey_year_rows = []
yid = 1
for sid in survey_ids:
    # 1-3 years per survey
    for ref_year in random.sample(range(2015, 2024), k=random.randint(1, 3)):
        release = datetime.date(ref_year + 1, random.randint(1,12), random.randint(1,28))
        survey_year_rows.append({
            "year_id":       yid,
            "survey_id":     sid,
            "reference_year": ref_year,
            "release_date":  release.isoformat(),
        })
        yid += 1
write_csv("survey_year.csv", ["year_id","survey_id","reference_year","release_date"], survey_year_rows)
year_ids = [r["year_id"] for r in survey_year_rows]

# 3. NAICS_INDUSTRY  (hierarchy: sector → 3-digit → 4-digit → 6-digit)
SECTORS = [
    ("11","Agriculture, Forestry, Fishing and Hunting"),
    ("21","Mining, Quarrying, and Oil and Gas Extraction"),
    ("22","Utilities"),
    ("23","Construction"),
    ("31","Manufacturing"),
    ("42","Wholesale Trade"),
    ("44","Retail Trade"),
    ("48","Transportation and Warehousing"),
    ("51","Information"),
    ("52","Finance and Insurance"),
    ("53","Real Estate and Rental and Leasing"),
    ("54","Professional, Scientific, and Technical Services"),
    ("55","Management of Companies and Enterprises"),
    ("56","Administrative and Support and Waste Management"),
    ("61","Educational Services"),
    ("62","Health Care and Social Assistance"),
    ("71","Arts, Entertainment, and Recreation"),
    ("72","Accommodation and Food Services"),
    ("81","Other Services"),
    ("92","Public Administration"),
]

naics_rows = []
seen_codes = set()

def add_naics(code, parent, sector, title, level):
    if code not in seen_codes:
        naics_rows.append({
            "naics_code":        code,
            "parent_naics_code": parent,
            "sector_code":       sector,
            "industry_title":    title,
            "hierarchy_level":   level,
        })
        seen_codes.add(code)

# Level 1: sectors (2-digit padded to 6 with zeros)
for sc, title in SECTORS:
    add_naics(sc.ljust(6,"0"), None, sc, title, 1)

# Level 2: 3-digit subsectors – generate 3 per sector
for sc, _ in SECTORS:
    for sub in range(1, 4):
        code3 = (sc + str(sub)).ljust(6,"0")
        add_naics(code3, sc.ljust(6,"0"), sc, f"Subsector {sc}{sub}", 2)

# Level 3: 4-digit industry groups – generate 2 per subsector
for sc, _ in SECTORS:
    for sub in range(1, 4):
        parent3 = (sc + str(sub)).ljust(6,"0")
        for grp in range(1, 3):
            code4 = (sc + str(sub) + str(grp)).ljust(6,"0")
            add_naics(code4, parent3, sc, f"Industry Group {sc}{sub}{grp}", 3)

# Level 4: 6-digit detailed industries – generate 2 per 4-digit group
for sc, _ in SECTORS:
    for sub in range(1, 4):
        for grp in range(1, 3):
            parent4 = (sc + str(sub) + str(grp)).ljust(6,"0")
            for det in range(10, 12):
                code6 = (sc + str(sub) + str(grp) + str(det))[:6]
                add_naics(code6, parent4, sc, f"Industry {code6}", 4)

write_csv("naics_industry.csv",
          ["naics_code","parent_naics_code","sector_code","industry_title","hierarchy_level"],
          naics_rows)
naics_codes = [r["naics_code"] for r in naics_rows]

# 4. GEOGRAPHIC_AREA
GEO_TYPES  = ["State","County","MSA","National","Region","City"]
STATE_FIPS = ["01","04","06","08","09","10","12","13","15","16",
              "17","18","19","20","21","22","23","24","25","26",
              "27","28","29","30","31","32","33","34","35","36",
              "37","38","39","40","41","42","44","45","46","47",
              "48","49","50","51","53","54","55","56","72","78"]
REGION_NAMES = [
    "Northeast","South","Midwest","West","Pacific","Mountain",
    "New England","Mid-Atlantic","East South Central","West South Central",
]

geo_rows = []
for gid in range(1, 151):
    gtype      = random.choice(GEO_TYPES)
    state_fips = random.choice(STATE_FIPS)
    geo_rows.append({
        "geo_id":      gid,
        "geo_type":    gtype,
        "state_fips":  state_fips,
        "county_fips": state_fips + str(random.randint(1,999)).zfill(3) if gtype == "County" else "",
        "msa_code":    str(random.randint(10000,99999)) if gtype == "MSA" else "",
        "region_name": random.choice(REGION_NAMES) + f" Area {gid}",
    })
write_csv("geographic_area.csv",
          ["geo_id","geo_type","state_fips","county_fips","msa_code","region_name"],
          geo_rows)
geo_ids = [r["geo_id"] for r in geo_rows]

# 5. BUSINESS_ESTABLISHMENT
SIZE_CLASSES  = ["<5","5-9","10-19","20-49","50-99","100-249","250-499","500-999","1000+"]
LEGAL_FORMS   = ["Sole Proprietorship","Partnership","S-Corporation","C-Corporation",
                 "LLC","Nonprofit","Cooperative","Government","Trust"]

estab_rows = []
for eid in range(1, 301):
    estab_rows.append({
        "establishment_id":    eid,
        "naics_code":          random.choice(naics_codes),
        "geo_id":              random.choice(geo_ids),
        "survey_id":           random.choice(survey_ids),
        "employer_size_class": random.choice(SIZE_CLASSES),
        "num_employees":       random.randint(1, 5000),
        "annual_revenue":      rand_decimal(50000, 50_000_000),
        "legal_form":          random.choice(LEGAL_FORMS),
    })
write_csv("business_establishment.csv",
          ["establishment_id","naics_code","geo_id","survey_id",
           "employer_size_class","num_employees","annual_revenue","legal_form"],
          estab_rows)
estab_ids = [r["establishment_id"] for r in estab_rows]

# 6. EXPENDITURE_RECORD
DATA_QUALITY_FLAGS = ["A","B","C","D","Z"]

exp_rows = []
for rid in range(1, 401):
    eid = random.choice(estab_ids)
    # Match naics_code and geo_id to parent establishment for referential realism
    estab = next(e for e in estab_rows if e["establishment_id"] == eid)
    exp_rows.append({
        "record_id":          rid,
        "establishment_id":   eid,
        "year_id":            random.choice(year_ids),
        "naics_code":         estab["naics_code"],
        "geo_id":             estab["geo_id"],
        "total_expenditures": rand_decimal(10000, 10_000_000),
        "data_quality_flag":  random.choice(DATA_QUALITY_FLAGS),
        "suppression_flag":   random.choice([0, 0, 0, 1]),  # 25 % suppressed
        "relative_std_error": round(random.uniform(0.0, 0.35), 4),
    })
write_csv("expenditure_record.csv",
          ["record_id","establishment_id","year_id","naics_code","geo_id",
           "total_expenditures","data_quality_flag","suppression_flag","relative_std_error"],
          exp_rows)
record_ids = [r["record_id"] for r in exp_rows]

# 7. CAPITAL_EXPENDITURE
capex_rows = []
for cid, rid in enumerate(record_ids, start=1):
    ns  = rand_decimal(0, 2_000_000)
    us  = rand_decimal(0, 500_000)
    nme = rand_decimal(0, 3_000_000)
    sc  = rand_decimal(0, 1_000_000)
    ll  = rand_decimal(0, 800_000)
    capex_rows.append({
        "capex_id":             cid,
        "record_id":            rid,
        "new_structures":       ns,
        "used_structures":      us,
        "new_machinery_equip":  nme,
        "software_capitalized": sc,
        "leased_owned_land":    ll,
        "total_capex":          round(ns + us + nme + sc + ll, 2),
    })
write_csv("capital_expenditure.csv",
          ["capex_id","record_id","new_structures","used_structures",
           "new_machinery_equip","software_capitalized","leased_owned_land","total_capex"],
          capex_rows)

# 8. OPERATING_EXPENSE
opex_rows = []
for oid, rid in enumerate(record_ids, start=1):
    rl  = rand_decimal(0, 500_000)
    cc  = rand_decimal(0, 200_000)
    hi  = rand_decimal(0, 1_000_000)
    la  = rand_decimal(0, 300_000)
    rd  = rand_decimal(0, 2_000_000)
    opex_rows.append({
        "opex_id":              oid,
        "record_id":            rid,
        "rent_lease_payments":  rl,
        "communication_costs":  cc,
        "health_insurance":     hi,
        "legal_accounting":     la,
        "rd_expenditure":       rd,
        "total_operating_exp":  round(rl + cc + hi + la + rd, 2),
    })
write_csv("operating_expense.csv",
          ["opex_id","record_id","rent_lease_payments","communication_costs",
           "health_insurance","legal_accounting","rd_expenditure","total_operating_exp"],
          opex_rows)

# 9. PAYROLL
payroll_rows = []
for pid, rid in enumerate(record_ids, start=1):
    annual = rand_decimal(50_000, 5_000_000)
    q1     = round(annual * random.uniform(0.20, 0.30), 2)
    fb     = round(annual * random.uniform(0.05, 0.20), 2)
    ep     = round(annual * random.uniform(0.03, 0.10), 2)
    wc     = round(annual * random.uniform(0.005, 0.02), 2)
    payroll_rows.append({
        "payroll_id":         pid,
        "record_id":          rid,
        "annual_payroll":     annual,
        "q1_payroll":         q1,
        "fringe_benefits":    fb,
        "employer_pension":   ep,
        "workers_comp":       wc,
        "num_paid_employees": random.randint(1, 2000),
    })
write_csv("payroll.csv",
          ["payroll_id","record_id","annual_payroll","q1_payroll",
           "fringe_benefits","employer_pension","workers_comp","num_paid_employees"],
          payroll_rows)

print("\n All CSV files written to ./data/")
