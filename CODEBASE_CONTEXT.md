# Codebase Context

## 1. Purpose and Scope

`git-data-pipeline-crud` is a small REST API for cataloging dataset metadata and recording pipeline execution logs. It is also a learning project for Git, GitHub, pull requests, CI/CD, testing, and semantic versioning.

The current implementation is intentionally compact:

- Web framework: FastAPI.
- Runtime server: Uvicorn.
- Validation and API schemas: Pydantic v2.
- Persistence: SQLite through Python's standard `sqlite3` module.
- Tests: Pytest and FastAPI/Starlette `TestClient`.
- Quality gate: Ruff plus Pytest in GitHub Actions.

The application is a metadata catalog. It does not execute data pipelines, read datasets, schedule jobs, authenticate users, or expose raw data contents.

## 2. Repository Layout

```text
git-data-pipeline-crud/
├── .github/workflows/ci.yml  # GitHub Actions quality gate
├── app/
│   ├── __init__.py           # Package marker and package docstring
│   ├── database.py           # SQLite connection, schema, CRUD, row mapping
│   ├── main.py               # FastAPI application, lifespan, HTTP routes
│   └── models.py             # Pydantic request and response contracts
├── tests/
│   ├── __init__.py
│   └── test_main.py          # Endpoint and lifecycle tests
├── .gitignore                # Local databases, environments, caches, raw data
├── README.md                 # Project overview, setup, and Git missions
├── requirements.txt          # Runtime and development dependencies
├── CODEBASE_CONTEXT.md       # This operational codebase reference
└── ADDR.md                   # Architecture and design decision record
```

`catalog.db` and `venv/` may exist locally. They are ignored by Git and are not part of the deployable source. Python cache directories are also ignored.

## 3. Runtime and Configuration

### Installation

From the repository root:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The dependency file uses minimum versions rather than a lock file:

- `fastapi>=0.115.0`
- `uvicorn[standard]>=0.30.0`
- `pydantic>=2.0.0`
- `pytest>=8.0.0`
- `httpx>=0.27.0`
- `ruff>=0.5.0`

### Start the API

```powershell
uvicorn app.main:app --reload --port 8000
```

Interactive documentation is available at `/docs`; both it and `/openapi.json` require HTTP Basic authentication. The demonstration login is `/login` with username `admin` and password `admin`; valid credentials receive a `303` redirect to `/docs`.

### Database configuration

The database path is read once when `app.database` is imported:

```text
DATABASE_PATH=<path>
```

If the variable is absent, the path is `catalog.db` in the process working directory. The database is initialized during FastAPI startup through the lifespan function. Initialization is idempotent because it uses `CREATE TABLE IF NOT EXISTS`.

## 4. Application Startup and Request Flow

1. Uvicorn imports `app.main:app`.
2. FastAPI enters the lifespan context.
3. `init_db()` creates or upgrades the local SQLite schema.
4. A request reaches a route in `app/main.py`.
5. FastAPI validates request data using a Pydantic model when the route has a body.
6. The route delegates persistence work to a function in `app/database.py`.
7. The database layer opens a connection, enables foreign keys, executes parameterized SQL, and maps rows to a Pydantic response model.
8. FastAPI serializes the response and applies the declared response model/status code.

The route layer owns HTTP concerns such as path parameters and 404 responses. The database layer owns SQL and persistence concerns. The models layer owns input constraints and response shape.

## 5. HTTP API Contract

### General endpoints

| Method | Path | Success response | Behavior |
|---|---|---|---|
| GET | `/` | `200` | Returns project name, version `0.2.0`, docs path, and healthy status. |
| GET | `/health` | `200` | Returns `{"status":"ok"}`. |
| GET | `/login` | `303` | Validates HTTP Basic credentials and redirects to `/docs`. |
| GET | `/docs` | `200` | Serves Swagger UI after HTTP Basic authentication. |
| GET | `/openapi.json` | `200` | Serves the OpenAPI schema after HTTP Basic authentication. |
| GET | `/datetime` | `200` | Returns current UTC date, time, and ISO 8601 datetime. |

Example `/datetime` response:

```json
{
  "date": "2026-10-05",
  "time": "18:19:41.730002",
  "datetime": "2026-10-05T18:19:41.730002+00:00"
}
```

### Dataset endpoints

| Method | Path | Success response | Failure behavior |
|---|---|---|---|
| POST | `/datasets` | `201`, `DatasetResponse` | `422` for invalid body. |
| GET | `/datasets` | `200`, list of `DatasetResponse` | Query validation returns `422`. |
| GET | `/datasets/{dataset_id}` | `200`, `DatasetResponse` | `404` if the ID does not exist. |
| PUT | `/datasets/{dataset_id}` | `200`, `DatasetResponse` | `404` if absent; `422` for invalid body. |
| DELETE | `/datasets/{dataset_id}` | `200`, deletion message | `404` if absent. |

`GET /datasets` supports `skip` (default `0`, minimum `0`) and `limit` (default `50`, range `1..100`). Results are ordered by descending ID.

### Pipeline run endpoints

| Method | Path | Success response | Failure behavior |
|---|---|---|---|
| POST | `/datasets/{dataset_id}/runs` | `201`, `PipelineRunResponse` | `404` if the dataset does not exist; `422` for invalid body. |
| GET | `/datasets/{dataset_id}/runs` | `200`, list of `PipelineRunResponse` | `404` if the dataset does not exist. |

Runs are ordered by descending ID. Creating a run sets `started_at` to the current UTC time. `completed_at` is null when the requested status is `running`; otherwise it is set immediately to the same current time.

## 6. Data Model

### `datasets` table

| Column | SQLite type | Rules/default |
|---|---|---|
| `id` | INTEGER | Primary key, autoincrement. |
| `name` | TEXT | Required; API length 2-100. |
| `source` | TEXT | Required; examples include S3, DB, Kafka URIs. |
| `format` | TEXT | Required; default `parquet`. |
| `row_count` | INTEGER | Required; default `0`; API must be non-negative. |
| `schema_version` | TEXT | Required; default `v1.0`. |
| `status` | TEXT | Required; default `active`. |
| `owner` | TEXT | Required. |
| `quality_score` | REAL | Required; default `0.0`; API range `0..1`. |
| `created_at` | TEXT | Required ISO 8601 UTC string. |
| `updated_at` | TEXT | Required ISO 8601 UTC string. |

### `pipeline_runs` table

| Column | SQLite type | Rules/default |
|---|---|---|
| `id` | INTEGER | Primary key, autoincrement. |
| `dataset_id` | INTEGER | Required foreign key to `datasets`; cascade delete. |
| `run_type` | TEXT | Required; API default `ingestion`. |
| `status` | TEXT | Required; API default `success`. |
| `records_processed` | INTEGER | Required; default `0`; API must be non-negative. |
| `started_at` | TEXT | Required ISO 8601 UTC string. |
| `completed_at` | TEXT | Nullable; set null for a `running` run. |

The database schema has a lightweight compatibility step: if an existing `datasets` table lacks `quality_score`, `init_db()` adds that column with a default. This is not a general migration framework.

## 7. Pydantic Contracts

`DatasetCreate` inherits all fields from `DatasetBase`. Required fields are `name`, `source`, and `owner`. Other fields have defaults.

`DatasetUpdate` makes every editable field optional and uses `exclude_unset=True`, so omitted fields are preserved. An empty update returns the existing dataset unchanged.

`DatasetResponse` adds `id`, `created_at`, and `updated_at` to the dataset fields.

`PipelineRunCreate` accepts `run_type`, `status`, and `records_processed`, all with defaults. `PipelineRunResponse` adds identifiers and timestamps.

Validation is deliberately basic. `format`, `status`, `schema_version`, `run_type`, and owner/source strings are not restricted to enumerations or normalized formats.

## 8. Persistence Details

- Each operation opens its own SQLite connection.
- `sqlite3.Row` allows columns to be accessed by name.
- Foreign keys are enabled per connection with `PRAGMA foreign_keys = ON`.
- Writes use context managers so transactions commit on successful exit and roll back on exceptions.
- SQL values use placeholders (`?`) rather than string interpolation.
- Dataset update builds a `SET` clause dynamically, but its field names come from the fixed Pydantic update model; values remain parameterized.
- Row-to-model helpers translate SQLite rows into API response models.
- Most read connections are explicitly closed before returning.
- Dataset deletion cascades to pipeline runs at the database level.

## 9. Tests and Quality Controls

`tests/test_main.py` uses a temporary SQLite file for every test. The `isolated_db` fixture patches `database.DEFAULT_DB_PATH`, initializes the schema, and removes the temporary file afterward. This prevents tests from modifying the developer's `catalog.db`.

Covered behavior includes:

- Root and health endpoints.
- UTC datetime endpoint shape and timezone awareness.
- Dataset creation and retrieval.
- Missing dataset returns `404`.
- Invalid dataset body returns `422`.
- Dataset pagination limit.
- Partial dataset update.
- Dataset deletion.
- Pipeline run creation and listing.

The CI workflow runs on Ubuntu with Python 3.12 for pushes to `main` and pull requests targeting `main`. It installs `requirements.txt`, runs `ruff check .`, then runs `pytest -v tests/`.

## 10. Git and Delivery Context

The recent history shows an initial API setup, addition of `quality_score`, documentation/version exercises, a conflict-resolution exercise, and the date endpoint feature. The active branch at the time this document was written is `main`, aligned with `origin/main`.

Recommended delivery flow from the repository's learning material:

1. Create a feature branch.
2. Make a focused change and run lint/tests locally.
3. Push the branch and open a pull request.
4. Let CI validate Ruff and Pytest.
5. Merge after review.
6. Tag stable releases using semantic versioning.

## 11. Known Limitations and Risks

- SQLite and a local file are suitable for learning and low-concurrency use, but not a production multi-instance deployment database.
- Authentication is only a hardcoded HTTP Basic demonstration for `/login`, `/docs`, and `/openapi.json`; there is no user store, authorization model, or credential rotation.
- There is no rate limiting, audit log, or request correlation ID.
- There is no structured application logging or metrics/tracing setup.
- Dependency versions are not pinned, so installations can change over time.
- There is no dedicated migration tool or rollback strategy.
- Status and type fields accept arbitrary strings despite examples implying finite values.
- Timestamps are strings rather than typed datetime fields in the public Pydantic models.
- The `running` state has no endpoint to complete or update a pipeline run after creation.
- There is no filtering, sorting selection, full-text search, or dataset archival endpoint.
- The API is not configured for production worker management, HTTPS termination, or container deployment.
- The current tests do not directly assert delete cascade behavior, update timestamp changes, all validation boundaries, or the exact `time` field of `/datetime`.

## 12. Safe Extension Points

- Add a new route in `app/main.py` and a focused test in `tests/test_main.py`.
- Add or change request/response rules in `app/models.py` before changing SQL behavior.
- Add persistence operations in `app/database.py`; keep HTTP exceptions in the route layer.
- For schema changes beyond the existing compatibility check, introduce a real migration strategy before deployment.
- Keep timestamps timezone-aware and serialized as ISO 8601 UTC values.
- Preserve parameterized SQL and foreign-key enforcement for all new database operations.