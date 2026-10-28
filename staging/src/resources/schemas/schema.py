import pandera.pandas as pa

# DataFrames that are written to each core table. The database assigns the identity keys.
COUNTRIES_SCHEMA = pa.DataFrameSchema(
    {
        "country_name": pa.Column("string", unique=True, nullable=False),
    },
    strict=True,
    ordered=True,
)

LOCATIONS_SCHEMA = pa.DataFrameSchema(
    {
        "location_name": pa.Column("string", unique=True, nullable=False),
    },
    strict=True,
    ordered=True,
)

SEARCH_LOCATIONS_SCHEMA = pa.DataFrameSchema(
    {
        "search_location_name": pa.Column("string", unique=True, nullable=False),
        "country_id": pa.Column("Int64", nullable=True),
    },
    strict=True,
    ordered=True,
)

COMPANIES_SCHEMA = pa.DataFrameSchema(
    {
        "company_name": pa.Column("string", nullable=False),
        "company_name_key": pa.Column("string", unique=True, nullable=False),
    },
    strict=True,
    ordered=True,
)

PLATFORMS_SCHEMA = pa.DataFrameSchema(
    {
        "platform_name": pa.Column("string", unique=True, nullable=False),
    },
    strict=True,
    ordered=True,
)

SCHEDULE_TYPES_SCHEMA = pa.DataFrameSchema(
    {
        "schedule_type_name": pa.Column("string", unique=True, nullable=False),
    },
    strict=True,
    ordered=True,
)

JOB_CATEGORIES_SCHEMA = pa.DataFrameSchema(
    {
        "job_category_name": pa.Column("string", unique=True, nullable=False),
    },
    strict=True,
    ordered=True,
)

SALARY_RATES_SCHEMA = pa.DataFrameSchema(
    {
        "salary_rate_name": pa.Column("string", unique=True, nullable=False),
    },
    strict=True,
    ordered=True,
)

SKILLS_SCHEMA = pa.DataFrameSchema(
    {
        "skill_name": pa.Column("string", unique=True, nullable=False),
    },
    strict=True,
    ordered=True,
)

SKILL_TYPES_SCHEMA = pa.DataFrameSchema(
    {
        "skill_type_name": pa.Column("string", unique=True, nullable=False),
    },
    strict=True,
    ordered=True,
)

SKILL_SKILL_TYPES_SCHEMA = pa.DataFrameSchema(
    {
        "skill_id": pa.Column("Int64", nullable=False),
        "skill_type_id": pa.Column("Int64", nullable=False),
    },
    unique=["skill_id", "skill_type_id"],
    strict=True,
    ordered=True,
)

JOBS_SCHEMA = pa.DataFrameSchema(
    {
        "source_row_hash": pa.Column(
            "string", pa.Check.str_length(64), unique=True, nullable=False
        ),
        "job_title": pa.Column("string", nullable=False),
        "job_category_id": pa.Column("Int64", nullable=False),
        "company_id": pa.Column("Int64", nullable=True),
        "job_location_id": pa.Column("Int64", nullable=True),
        "search_location_id": pa.Column("Int64", nullable=True),
        "platform_id": pa.Column("Int64", nullable=True),
        "salary_rate_id": pa.Column("Int64", nullable=True),
        "posted_at": pa.Column("datetime64[us]", nullable=False),
        "work_from_home": pa.Column("boolean", nullable=False),
        "no_degree_mention": pa.Column("boolean", nullable=False),
        "health_insurance": pa.Column("boolean", nullable=False),
        "salary_year_avg": pa.Column(object, nullable=True),
        "salary_hour_avg": pa.Column(object, nullable=True),
    },
    strict=True,
    ordered=True,
)

JOB_SKILLS_SCHEMA = pa.DataFrameSchema(
    {
        "job_id": pa.Column("Int64", nullable=False),
        "skill_id": pa.Column("Int64", nullable=False),
    },
    unique=["job_id", "skill_id"],
    strict=True,
    ordered=True,
)

JOB_SCHEDULE_TYPES_SCHEMA = pa.DataFrameSchema(
    {
        "job_id": pa.Column("Int64", nullable=False),
        "schedule_type_id": pa.Column("Int64", nullable=False),
    },
    unique=["job_id", "schedule_type_id"],
    strict=True,
    ordered=True,
)

# One schema per core table, by table name.
CORE_SCHEMAS = {
    "countries": COUNTRIES_SCHEMA,
    "locations": LOCATIONS_SCHEMA,
    "search_locations": SEARCH_LOCATIONS_SCHEMA,
    "companies": COMPANIES_SCHEMA,
    "platforms": PLATFORMS_SCHEMA,
    "schedule_types": SCHEDULE_TYPES_SCHEMA,
    "job_categories": JOB_CATEGORIES_SCHEMA,
    "salary_rates": SALARY_RATES_SCHEMA,
    "skills": SKILLS_SCHEMA,
    "skill_types": SKILL_TYPES_SCHEMA,
    "skill_skill_types": SKILL_SKILL_TYPES_SCHEMA,
    "jobs": JOBS_SCHEMA,
    "job_skills": JOB_SKILLS_SCHEMA,
    "job_schedule_types": JOB_SCHEDULE_TYPES_SCHEMA,
}
