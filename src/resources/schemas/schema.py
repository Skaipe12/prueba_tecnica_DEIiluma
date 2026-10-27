import pandera.pandas as pa

# DataFrame that is written to raw.
RAW_JOB_POSTINGS_SCHEMA = pa.DataFrameSchema(
    {
        "job_title_short": pa.Column("string", nullable=True),
        "job_title": pa.Column("string", nullable=True),
        "job_location": pa.Column("string", nullable=True),
        "job_via": pa.Column("string", nullable=True),
        "job_schedule_type": pa.Column("string", nullable=True),
        "job_work_from_home": pa.Column("boolean", nullable=True),
        "search_location": pa.Column("string", nullable=True),
        "job_posted_date": pa.Column("datetime64[us]", nullable=True),
        "job_no_degree_mention": pa.Column("boolean", nullable=True),
        "job_health_insurance": pa.Column("boolean", nullable=True),
        "job_country": pa.Column("string", nullable=True),
        "salary_rate": pa.Column("string", nullable=True),
        "salary_year_avg": pa.Column(object, nullable=True),
        "salary_hour_avg": pa.Column(object, nullable=True),
        "company_name": pa.Column("string", nullable=True),
        "job_skills": pa.Column(object, nullable=True),
        "job_type_skills": pa.Column(object, nullable=True),
        "row_hash": pa.Column("string", pa.Check.str_length(64), nullable=False),
    },
    strict=True,
    ordered=True,
)
