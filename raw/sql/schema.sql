-- Raw layer: the CSV as it comes, only with types. Safe to run more than once.

CREATE SCHEMA IF NOT EXISTS raw;


-- ---------------------------------------------------------------------------
-- raw
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS raw.job_postings (
    raw_id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_title_short       TEXT,
    job_title             TEXT,
    job_location          TEXT,
    job_via               TEXT,
    job_schedule_type     TEXT,
    job_work_from_home    BOOLEAN,
    search_location       TEXT,
    job_posted_date       TIMESTAMP,
    job_no_degree_mention BOOLEAN,
    job_health_insurance  BOOLEAN,
    job_country           TEXT,
    salary_rate           TEXT,
    salary_year_avg       NUMERIC,
    salary_hour_avg       NUMERIC,
    company_name          TEXT,
    job_skills            TEXT[],
    job_type_skills       JSONB,
    row_hash              CHAR(64) NOT NULL,
    loaded_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Not unique: exact duplicates of the source are kept in raw and removed in staging.
CREATE INDEX IF NOT EXISTS ix_raw_job_postings_row_hash ON raw.job_postings (row_hash);
