-- Database schema of the jobs pipeline. Safe to run more than once.
--   raw  : the CSV as it comes.
--   core : the 3NF model that is built from raw with SQL

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS core;


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

-- Not unique: exact duplicates of the source are kept in raw and removed in core.
CREATE INDEX IF NOT EXISTS ix_raw_job_postings_row_hash ON raw.job_postings (row_hash);


-- ---------------------------------------------------------------------------
-- core: catalogs
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS core.countries (
    country_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    country_name TEXT NOT NULL UNIQUE
);

-- Location written in the job posting (job_location).
CREATE TABLE IF NOT EXISTS core.locations (
    location_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    location_name TEXT NOT NULL UNIQUE
);

-- Location used by the search that found the job. The country depends on it, not on the job.
CREATE TABLE IF NOT EXISTS core.search_locations (
    search_location_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    search_location_name TEXT NOT NULL UNIQUE,
    country_id           INTEGER REFERENCES core.countries (country_id)
);

CREATE TABLE IF NOT EXISTS core.companies (
    company_id       INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    company_name     TEXT NOT NULL,
    company_name_key TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS core.platforms (
    platform_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    platform_name TEXT NOT NULL UNIQUE
);

-- One row per single schedule type (Full-time, Part-time, ...), never a combination.
CREATE TABLE IF NOT EXISTS core.schedule_types (
    schedule_type_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    schedule_type_name TEXT NOT NULL UNIQUE
);

-- Standardized job title (job_title_short in the source).
CREATE TABLE IF NOT EXISTS core.job_categories (
    job_category_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_category_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS core.salary_rates (
    salary_rate_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    salary_rate_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS core.skills (
    skill_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    skill_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS core.skill_types (
    skill_type_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    skill_type_name TEXT NOT NULL UNIQUE
);

-- A skill can belong to several types (for example mongodb is a database and a programming skill).
CREATE TABLE IF NOT EXISTS core.skill_skill_types (
    skill_id      INTEGER NOT NULL REFERENCES core.skills (skill_id),
    skill_type_id INTEGER NOT NULL REFERENCES core.skill_types (skill_type_id),
    PRIMARY KEY (skill_id, skill_type_id)
);


-- ---------------------------------------------------------------------------
-- core: jobs and their many-to-many relations
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS core.jobs (
    job_id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_row_hash    CHAR(64) NOT NULL UNIQUE,
    job_title          TEXT NOT NULL,
    job_category_id    INTEGER NOT NULL REFERENCES core.job_categories (job_category_id),
    company_id         INTEGER REFERENCES core.companies (company_id),
    job_location_id    INTEGER REFERENCES core.locations (location_id),
    search_location_id INTEGER REFERENCES core.search_locations (search_location_id),
    platform_id        INTEGER REFERENCES core.platforms (platform_id),
    salary_rate_id     INTEGER REFERENCES core.salary_rates (salary_rate_id),
    posted_at          TIMESTAMP NOT NULL,
    work_from_home     BOOLEAN NOT NULL,
    no_degree_mention  BOOLEAN NOT NULL,
    health_insurance   BOOLEAN NOT NULL,
    salary_year_avg    NUMERIC(12, 2) CHECK (salary_year_avg >= 0),
    salary_hour_avg    NUMERIC(10, 2) CHECK (salary_hour_avg >= 0)
);

CREATE TABLE IF NOT EXISTS core.job_skills (
    job_id   BIGINT NOT NULL REFERENCES core.jobs (job_id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES core.skills (skill_id),
    PRIMARY KEY (job_id, skill_id)
);

CREATE TABLE IF NOT EXISTS core.job_schedule_types (
    job_id           BIGINT NOT NULL REFERENCES core.jobs (job_id) ON DELETE CASCADE,
    schedule_type_id INTEGER NOT NULL REFERENCES core.schedule_types (schedule_type_id),
    PRIMARY KEY (job_id, schedule_type_id)
);


-- ---------------------------------------------------------------------------
-- core: jobs and their bridge tables
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS ix_search_locations_country_id ON core.search_locations (country_id);
CREATE INDEX IF NOT EXISTS ix_skill_skill_types_skill_type_id ON core.skill_skill_types (skill_type_id);
CREATE INDEX IF NOT EXISTS ix_jobs_job_category_id ON core.jobs (job_category_id);
CREATE INDEX IF NOT EXISTS ix_jobs_company_id ON core.jobs (company_id);
CREATE INDEX IF NOT EXISTS ix_jobs_job_location_id ON core.jobs (job_location_id);
CREATE INDEX IF NOT EXISTS ix_jobs_search_location_id ON core.jobs (search_location_id);
CREATE INDEX IF NOT EXISTS ix_jobs_platform_id ON core.jobs (platform_id);
CREATE INDEX IF NOT EXISTS ix_jobs_salary_rate_id ON core.jobs (salary_rate_id);
CREATE INDEX IF NOT EXISTS ix_job_skills_skill_id ON core.job_skills (skill_id);
CREATE INDEX IF NOT EXISTS ix_job_schedule_types_schedule_type_id
    ON core.job_schedule_types (schedule_type_id);


-- ---------------------------------------------------------------------------
-- core: cleaning functions
-- ---------------------------------------------------------------------------

-- Repairs text that was UTF-8 but was read as LATIN1 ("MÃ©xico" -> "México").
-- If the text cannot be repaired it is returned unchanged.
CREATE OR REPLACE FUNCTION core.fix_mojibake(value TEXT) RETURNS TEXT
LANGUAGE plpgsql IMMUTABLE AS $$
BEGIN
    IF value IS NULL OR value !~ '[ÃÂ]' THEN
        RETURN value;
    END IF;
    RETURN convert_from(convert_to(value, 'LATIN1'), 'UTF8');
EXCEPTION
    WHEN OTHERS THEN
        RETURN value;
END;
$$;
