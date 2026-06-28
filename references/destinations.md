# Destinations Reference

This file documents how to configure each supported dlt destination, the required environment variables, and the dlt destination call. No secrets are hardcoded here — all values come from env vars or `.dlt/secrets.toml`.

---

## 1. DuckDB (local / testing)

**Use for:** local development, unit tests, quick prototypes. Zero external dependencies.

```python
import dlt

pipeline = dlt.pipeline(
    pipeline_name="my_pipeline",
    destination="duckdb",
    dataset_name="my_dataset",
)
```

**Required env vars:** None. DuckDB creates a local file (`<pipeline_name>.duckdb`) automatically.

**Notes:** Not suitable for production multi-user workloads. Default destination when no `--dest` flag is supplied by skills.

---

## 2. PostgreSQL

**Use for:** production OLTP/analytical workloads on self-managed or managed Postgres (RDS, Cloud SQL, AlloyDB, etc.).

```python
pipeline = dlt.pipeline(
    pipeline_name="my_pipeline",
    destination="postgres",
    dataset_name="my_schema",
)
```

**Required env vars (set in `.dlt/secrets.toml` or shell):**

```toml
[destination.postgres.credentials]
database = "mydb"
username = "myuser"
password = "..."          # set via env var DESTINATION__POSTGRES__CREDENTIALS__PASSWORD
host     = "db.example.com"
port     = 5432
```

Or as a connection string:

```bash
export DESTINATION__POSTGRES__CREDENTIALS="postgresql://myuser:mypassword@db.example.com:5432/mydb"
```

**Never hardcode the password.** Reference `DESTINATION__POSTGRES__CREDENTIALS__PASSWORD` or the full connection string env var.

---

## 3. BigQuery

**Use for:** Google Cloud analytical workloads.

```python
pipeline = dlt.pipeline(
    pipeline_name="my_pipeline",
    destination="bigquery",
    dataset_name="my_dataset",
)
```

**Required env vars:**

```bash
export DESTINATION__BIGQUERY__CREDENTIALS__PROJECT_ID="my-gcp-project"
export DESTINATION__BIGQUERY__CREDENTIALS__PRIVATE_KEY_ID="key-id"
export DESTINATION__BIGQUERY__CREDENTIALS__PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n..."
export DESTINATION__BIGQUERY__CREDENTIALS__CLIENT_EMAIL="sa@my-gcp-project.iam.gserviceaccount.com"
```

Or supply a path to the service-account JSON file:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

**Notes:** The service-account JSON file must not be committed to version control. Use Secret Manager or CI secrets injection.

---

## 4. Snowflake

**Use for:** Snowflake data warehouse.

```python
pipeline = dlt.pipeline(
    pipeline_name="my_pipeline",
    destination="snowflake",
    dataset_name="MY_SCHEMA",
)
```

**Required env vars:**

```bash
export DESTINATION__SNOWFLAKE__CREDENTIALS__DATABASE="MY_DB"
export DESTINATION__SNOWFLAKE__CREDENTIALS__USERNAME="MY_USER"
export DESTINATION__SNOWFLAKE__CREDENTIALS__PASSWORD="..."
export DESTINATION__SNOWFLAKE__CREDENTIALS__HOST="myaccount.snowflakecomputing.com"
export DESTINATION__SNOWFLAKE__CREDENTIALS__WAREHOUSE="MY_WH"
export DESTINATION__SNOWFLAKE__CREDENTIALS__ROLE="MY_ROLE"
```

Or as a connection string:

```bash
export DESTINATION__SNOWFLAKE__CREDENTIALS="snowflake://MY_USER:MY_PASSWORD@myaccount/MY_DB/MY_SCHEMA?warehouse=MY_WH&role=MY_ROLE"
```

---

## 5. Azure SQL / Synapse

**Use for:** Microsoft Azure analytical workloads (Azure SQL Database or Synapse Analytics).

dlt uses the `mssql` destination for both.

```python
pipeline = dlt.pipeline(
    pipeline_name="my_pipeline",
    destination="mssql",
    dataset_name="my_schema",
)
```

**Required env vars:**

```bash
export DESTINATION__MSSQL__CREDENTIALS__DATABASE="mydb"
export DESTINATION__MSSQL__CREDENTIALS__USERNAME="myuser"
export DESTINATION__MSSQL__CREDENTIALS__PASSWORD="..."
export DESTINATION__MSSQL__CREDENTIALS__HOST="myserver.database.windows.net"
export DESTINATION__MSSQL__CREDENTIALS__PORT="1433"
```

**Notes:** Install the `pyodbc` and `mssql` extras: `pip install "dlt[mssql]"`. For Synapse, set the schema collation to `Latin1_General_100_CI_AS_SC_UTF8`.

---

## 6. Filesystem (Blob Storage — Parquet or CSV)

**Use for:** data lake landing zones on Azure Blob, GCS, S3, or local filesystem. Outputs Parquet (default) or CSV files.

```python
pipeline = dlt.pipeline(
    pipeline_name="my_pipeline",
    destination="filesystem",
    dataset_name="my_prefix",
)
```

**Required env vars (example for Azure Blob):**

```bash
export DESTINATION__FILESYSTEM__BUCKET_URL="az://mycontainer/myfolder"
export DESTINATION__FILESYSTEM__CREDENTIALS__AZURE_STORAGE_ACCOUNT_NAME="mystorageaccount"
export DESTINATION__FILESYSTEM__CREDENTIALS__AZURE_STORAGE_ACCOUNT_KEY="..."
```

**For S3:**

```bash
export DESTINATION__FILESYSTEM__BUCKET_URL="s3://mybucket/myprefix"
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
```

**Output format** — default is Parquet. To use CSV, set `data_writer.file_format = "csv"` in your dlt config or pass it as a pipeline argument.

---

## Secrets Policy

All `...PASSWORD`, `...KEY`, and `...CREDENTIALS` values must come from environment variables or `.dlt/secrets.toml`. They must never be hardcoded in pipeline files, skills, or generated code. See `references/security.md` for the full policy.
