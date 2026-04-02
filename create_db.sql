-- ============================================================
-- create_db.sql
-- Census Budget Expenditure Database
-- COP-3710 Project Part D
-- ============================================================

DROP DATABASE IF EXISTS census_budget;
CREATE DATABASE census_budget
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE census_budget;

-- ============================================================
-- SURVEY
-- ============================================================
CREATE TABLE SURVEY (
    survey_id       INT             NOT NULL AUTO_INCREMENT,
    survey_name     VARCHAR(255)    NOT NULL,
    survey_type     ENUM('Annual','Quinquennial','Decennial','Monthly','Quarterly') NOT NULL,
    frequency       ENUM('Annual','Biennial','Quinquennial','Monthly','Quarterly','Decennial') NOT NULL,
    sponsor_agency  VARCHAR(255)    NOT NULL,
    PRIMARY KEY (survey_id)
);

-- ============================================================
-- SURVEY_YEAR
-- ============================================================
CREATE TABLE SURVEY_YEAR (
    year_id         INT             NOT NULL AUTO_INCREMENT,
    survey_id       INT             NOT NULL,
    reference_year  YEAR            NOT NULL,
    release_date    DATE            NOT NULL,
    PRIMARY KEY (year_id),
    CONSTRAINT fk_sy_survey FOREIGN KEY (survey_id) REFERENCES SURVEY(survey_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ============================================================
-- NAICS_INDUSTRY  (self-referencing for hierarchy)
-- ============================================================
CREATE TABLE NAICS_INDUSTRY (
    naics_code          CHAR(6)         NOT NULL,
    parent_naics_code   CHAR(6)         NULL,
    sector_code         CHAR(2)         NOT NULL,
    industry_title      VARCHAR(255)    NOT NULL,
    hierarchy_level     TINYINT         NOT NULL,
    PRIMARY KEY (naics_code),
    CONSTRAINT fk_naics_parent FOREIGN KEY (parent_naics_code)
        REFERENCES NAICS_INDUSTRY(naics_code)
        ON UPDATE CASCADE ON DELETE SET NULL
);

-- ============================================================
-- GEOGRAPHIC_AREA
-- ============================================================
CREATE TABLE GEOGRAPHIC_AREA (
    geo_id          INT             NOT NULL AUTO_INCREMENT,
    geo_type        ENUM('State','County','MSA','National','Region','City') NOT NULL,
    state_fips      CHAR(2)         NULL,
    county_fips     CHAR(5)         NULL,
    msa_code        CHAR(5)         NULL,
    region_name     VARCHAR(255)    NOT NULL,
    PRIMARY KEY (geo_id)
);

-- ============================================================
-- BUSINESS_ESTABLISHMENT
-- ============================================================
CREATE TABLE BUSINESS_ESTABLISHMENT (
    establishment_id    BIGINT          NOT NULL AUTO_INCREMENT,
    naics_code          CHAR(6)         NOT NULL,
    geo_id              INT             NOT NULL,
    survey_id           INT             NOT NULL,
    employer_size_class ENUM('<5','5-9','10-19','20-49','50-99','100-249','250-499','500-999','1000+') NOT NULL,
    num_employees       INT             NOT NULL DEFAULT 0,
    annual_revenue      DECIMAL(18,2)   NOT NULL DEFAULT 0.00,
    legal_form          VARCHAR(100)    NOT NULL,
    PRIMARY KEY (establishment_id),
    CONSTRAINT fk_be_naics   FOREIGN KEY (naics_code)  REFERENCES NAICS_INDUSTRY(naics_code)   ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_be_geo     FOREIGN KEY (geo_id)      REFERENCES GEOGRAPHIC_AREA(geo_id)       ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_be_survey  FOREIGN KEY (survey_id)   REFERENCES SURVEY(survey_id)             ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ============================================================
-- EXPENDITURE_RECORD
-- ============================================================
CREATE TABLE EXPENDITURE_RECORD (
    record_id           BIGINT          NOT NULL AUTO_INCREMENT,
    establishment_id    BIGINT          NOT NULL,
    year_id             INT             NOT NULL,
    naics_code          CHAR(6)         NOT NULL,
    geo_id              INT             NOT NULL,
    total_expenditures  DECIMAL(18,2)   NOT NULL DEFAULT 0.00,
    data_quality_flag   CHAR(1)         NOT NULL DEFAULT 'A',
    suppression_flag    BOOLEAN         NOT NULL DEFAULT FALSE,
    relative_std_error  FLOAT           NOT NULL DEFAULT 0.0,
    PRIMARY KEY (record_id),
    CONSTRAINT fk_er_estab  FOREIGN KEY (establishment_id) REFERENCES BUSINESS_ESTABLISHMENT(establishment_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_er_year   FOREIGN KEY (year_id)          REFERENCES SURVEY_YEAR(year_id)                     ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_er_naics  FOREIGN KEY (naics_code)       REFERENCES NAICS_INDUSTRY(naics_code)               ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_er_geo    FOREIGN KEY (geo_id)           REFERENCES GEOGRAPHIC_AREA(geo_id)                  ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ============================================================
-- CAPITAL_EXPENDITURE
-- ============================================================
CREATE TABLE CAPITAL_EXPENDITURE (
    capex_id                BIGINT          NOT NULL AUTO_INCREMENT,
    record_id               BIGINT          NOT NULL,
    new_structures          DECIMAL(18,2)   NOT NULL DEFAULT 0.00,
    used_structures         DECIMAL(18,2)   NOT NULL DEFAULT 0.00,
    new_machinery_equip     DECIMAL(18,2)   NOT NULL DEFAULT 0.00,
    software_capitalized    DECIMAL(18,2)   NOT NULL DEFAULT 0.00,
    leased_owned_land       DECIMAL(18,2)   NOT NULL DEFAULT 0.00,
    total_capex             DECIMAL(18,2)   NOT NULL DEFAULT 0.00,
    PRIMARY KEY (capex_id),
    CONSTRAINT fk_capex_record FOREIGN KEY (record_id) REFERENCES EXPENDITURE_RECORD(record_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- ============================================================
-- OPERATING_EXPENSE
-- ============================================================
CREATE TABLE OPERATING_EXPENSE (
    opex_id                 BIGINT          NOT NULL AUTO_INCREMENT,
    record_id               BIGINT          NOT NULL,
    rent_lease_payments     DECIMAL(18,2)   NOT NULL DEFAULT 0.00,
    communication_costs     DECIMAL(18,2)   NOT NULL DEFAULT 0.00,
    health_insurance        DECIMAL(18,2)   NOT NULL DEFAULT 0.00,
    legal_accounting        DECIMAL(18,2)   NOT NULL DEFAULT 0.00,
    rd_expenditure          DECIMAL(18,2)   NOT NULL DEFAULT 0.00,
    total_operating_exp     DECIMAL(18,2)   NOT NULL DEFAULT 0.00,
    PRIMARY KEY (opex_id),
    CONSTRAINT fk_opex_record FOREIGN KEY (record_id) REFERENCES EXPENDITURE_RECORD(record_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- ============================================================
-- PAYROLL
-- ============================================================
CREATE TABLE PAYROLL (
    payroll_id          BIGINT          NOT NULL AUTO_INCREMENT,
    record_id           BIGINT          NOT NULL,
    annual_payroll      DECIMAL(18,2)   NOT NULL DEFAULT 0.00,
    q1_payroll          DECIMAL(18,2)   NOT NULL DEFAULT 0.00,
    fringe_benefits     DECIMAL(18,2)   NOT NULL DEFAULT 0.00,
    employer_pension    DECIMAL(18,2)   NOT NULL DEFAULT 0.00,
    workers_comp        DECIMAL(18,2)   NOT NULL DEFAULT 0.00,
    num_paid_employees  INT             NOT NULL DEFAULT 0,
    PRIMARY KEY (payroll_id),
    CONSTRAINT fk_payroll_record FOREIGN KEY (record_id) REFERENCES EXPENDITURE_RECORD(record_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);
