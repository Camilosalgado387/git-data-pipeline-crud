# ADDR: Architecture and Design Decision Record

## Document Status

- **Status:** Accepted for the current learning project
- **Date:** 2026-10-05
- **Scope:** Current architecture of `git-data-pipeline-crud`
- **Meaning of ADDR:** Architecture and Design Decision Record. This document consolidates the architectural decisions that are currently encoded in the repository, including decisions that were implicit rather than formally recorded.

## 1. Context

The project needs a small, understandable service that catalogs datasets and records pipeline run metadata. The service must be easy to run locally, easy to test, and useful for practicing Git and CI/CD. Its expected scale and operational requirements are educational and local rather than production-grade.

The repository therefore prioritizes a short feedback loop, low setup cost, clear module boundaries, HTTP contract validation, and reproducible automated checks.

## 2. Architectural Summary

The system is a synchronous layered HTTP service:

```text
Client
  |
  v
FastAPI routes (app/main.py)
  |
  v
Pydantic contracts (app/models.py)
  |
  v
SQLite access and CRUD (app/database.py)
  |
  v
catalog.db
```

FastAPI owns request parsing, validation integration, routing, OpenAPI generation, and HTTP status handling. The database module owns connections, SQL, transactions, schema initialization, and row mapping. Pydantic models define the boundary between external JSON and internal typed data.

## 3. Decision Records

### ADR-001: Use FastAPI for the HTTP service

**Decision:** Use FastAPI as the web framework.

**Why:** It provides typed request validation through Pydantic, automatic OpenAPI/Swagger documentation, concise route declarations, and a straightforward test client. These features match the educational objective and minimize framework ceremony.

**Alternatives considered:** Flask would be simpler at the absolute minimum but would require more explicit validation and documentation wiring. Django would add capabilities that are unnecessary for this small service.

**Consequences:** The application depends on FastAPI and Pydantic conventions. Route functions remain synchronous, which is appropriate for the current small SQLite workload but limits throughput for heavier I/O.

### ADR-002: Use SQLite as the persistence store

**Decision:** Store catalog metadata in a local SQLite database.

**Why:** SQLite is included with Python, requires no separate service, works well for local development, and supports relational constraints and cascading deletes.

**Alternatives considered:** PostgreSQL would be a stronger production choice but would require an external service and more setup. In-memory storage would make the API less realistic and lose data between restarts.

**Consequences:** The service is easy to start but inherits SQLite file-locking and single-file deployment constraints. Horizontal scaling, high write concurrency, backups, and operational migration require additional design.

### ADR-003: Keep persistence in a dedicated database module

**Decision:** Put SQL and database lifecycle operations in `app/database.py`, while keeping routes in `app/main.py`.

**Why:** This creates a clear ownership boundary and keeps HTTP concerns out of SQL functions. It also makes database functions directly testable with an alternate path.

**Alternatives considered:** Putting SQL inside route functions would reduce files initially but would couple transport and persistence, making future database changes and tests harder.

**Consequences:** The module is intentionally lightweight rather than a full repository/ORM abstraction. More complex queries or multiple storage backends may eventually justify a richer repository layer.

### ADR-004: Use Pydantic models as the API contract

**Decision:** Define request and response models in `app/models.py` and use them in route declarations.

**Why:** Pydantic gives consistent validation, clear defaults, generated API schemas, and protection against invalid numeric ranges such as negative row counts or quality scores outside `0..1`.

**Alternatives considered:** Manual dictionary validation would duplicate logic and weaken generated documentation. An ORM model layer would add complexity not needed by the current scope.

**Consequences:** Validation currently covers shape and basic ranges, but not business vocabularies. Adding enums, stricter URLs, emails, or typed datetimes should happen in the models first.

### ADR-005: Use UTC ISO 8601 timestamps

**Decision:** Generate timestamps with `datetime.now(timezone.utc)` and serialize them with `isoformat()`.

**Why:** UTC avoids machine-local timezone ambiguity, and ISO 8601 is portable across JSON clients and data systems. The same convention is used by dataset audit fields, pipeline runs, and `/datetime`.

**Alternatives considered:** Local naive datetimes would be easier to write but make comparison and distributed operation error-prone. Epoch numbers are compact but less readable in API responses.

**Consequences:** Consumers must parse timezone-aware ISO strings. Public response models currently type timestamps as strings, so a future contract improvement could use Pydantic `datetime` fields.

### ADR-006: Initialize the schema at application startup

**Decision:** Call `init_db()` from FastAPI's lifespan startup hook.

**Why:** A fresh local checkout can start without a manual database command. `CREATE TABLE IF NOT EXISTS` makes repeated starts safe, and the existing `quality_score` compatibility check handles one known schema evolution.

**Alternatives considered:** A manual setup script increases operational steps. A full migration framework is more robust but disproportionate to the current learning scope.

**Consequences:** Startup is coupled to database availability. Schema evolution is currently ad hoc and must be replaced with versioned migrations before production use.

### ADR-007: Use parameterized SQL and per-operation connections

**Decision:** Open a SQLite connection for each database operation, enable foreign keys on that connection, and bind values with `?` placeholders.

**Why:** Per-operation connections are simple and avoid sharing connection state across requests. Parameter binding prevents value-based SQL injection and handles SQLite quoting correctly. Enabling foreign keys makes the dataset/run relationship enforceable.

**Alternatives considered:** A long-lived connection or ORM session could reduce connection setup but adds lifecycle and concurrency complexity. Raw string-built SQL for values would be unsafe.

**Consequences:** Connection setup is repeated, and transaction/retry behavior is basic. The dynamic update clause is acceptable because field names come from the fixed Pydantic model, while all values remain bound parameters.

### ADR-008: Represent pipeline runs as child records of datasets

**Decision:** Store runs in `pipeline_runs` with a foreign key to `datasets` and `ON DELETE CASCADE`.

**Why:** A run has no meaning in this catalog without its dataset. Cascading deletion prevents orphaned run records when a dataset is removed.

**Alternatives considered:** Keeping runs in a separate unlinked log would preserve history but weaken referential integrity. Soft deletion could preserve history but is outside the current CRUD scope.

**Consequences:** Deleting a dataset deletes its run history. If audit retention becomes a requirement, the deletion policy must change to soft deletion or archival.

### ADR-009: Use explicit CRUD functions instead of an ORM

**Decision:** Implement CRUD with standard-library SQLite calls and explicit row mappers.

**Why:** The schema and query set are small, and explicit SQL keeps the data path visible for a data-engineering learning project. It avoids introducing ORM configuration and migration behavior prematurely.

**Alternatives considered:** SQLAlchemy would provide a broader production path, typed query composition, and richer relationship handling, at the cost of dependency and abstraction overhead.

**Consequences:** Developers must maintain SQL and mapping code manually. Query growth, complex filtering, or multiple databases are signals to reassess this decision.

### ADR-010: Use GitHub Actions as the merge quality gate

**Decision:** Run Ruff and the Pytest suite for pushes to `main` and pull requests targeting `main`.

**Why:** These checks catch syntax/style regressions and behavioral failures before merge, while keeping the workflow easy to understand.

**Alternatives considered:** Local-only checks are faster to configure but unreliable as a team gate. A larger matrix or deployment pipeline is unnecessary for the current project.

**Consequences:** CI uses Python 3.12 while local environments may differ. Dependencies are installed from minimum-version ranges, so reproducibility would improve with a lock/constraint file and a broader version matrix.

### ADR-011: Add a UTC date/time endpoint as a general API utility

**Decision:** Expose `GET /datetime` returning separate `date`, `time`, and combined `datetime` fields.

**Why:** It provides a simple observable endpoint for the current date/time requirement and demonstrates timezone-aware serialization without coupling it to a database record.

**Alternatives considered:** Returning only a formatted display string would be less useful to machines. Returning server-local time would be ambiguous across environments.

**Consequences:** The endpoint reports UTC, not the caller's local timezone. Clients needing local display should convert the timezone themselves.

### ADR-012: Use hardcoded HTTP Basic authentication for the documentation

**Decision:** Protect `/login`, `/docs`, and `/openapi.json` with HTTP Basic authentication. Accept only the in-code demonstration credentials `admin`/`admin`; do not create a user table or add user fields to the data models.

**Why:** The immediate requirement is a basic gate for interactive API documentation, while user persistence is explicitly deferred. FastAPI's `HTTPBasic` dependency provides the challenge/validation flow without introducing a new database concern.

**Alternatives considered:** A users table with hashed passwords would be appropriate for real accounts but is outside the current scope. OAuth2/JWT would add token lifecycle and authorization complexity that the current API does not need.

**Consequences:** This is not production authentication. Credentials are static source-level values, there is no logout/session management, and the API's dataset endpoints remain unauthenticated. HTTPS and a proper identity store are required before exposing this pattern beyond local/demo use.

## 4. Non-Goals

The current architecture intentionally does not provide:

- Pipeline execution or scheduling.
- Dataset file upload/download or content inspection.
- Persistent user accounts or authorization. The current implementation has only a hardcoded HTTP Basic gate for the documentation routes.
- Production observability, distributed tracing, or alerting.
- Multi-tenant isolation.
- Guaranteed audit retention after dataset deletion.
- High-availability or horizontal scaling.

## 5. Security and Reliability Posture

The implementation uses parameterized SQL values, Pydantic input validation, SQLite foreign keys, and isolated temporary databases in tests. Those are useful baseline controls, not a complete production security model.

Important gaps are static source-level credentials, no authorization model, unrestricted status/type strings, no rate limiting, no structured logs, no secret management beyond environment-based database configuration, no backup policy, and no migration rollback mechanism.

## 6. Evolution Triggers

Revisit the architecture when any of these become true:

| Trigger | Likely architectural response |
|---|---|
| Multiple API instances or frequent concurrent writes | Move from SQLite to PostgreSQL and review transaction handling. |
| Schema changes become frequent | Introduce Alembic or another versioned migration tool. |
| More complex query/filter requirements | Add repository abstractions or evaluate SQLAlchemy. |
| Need to preserve run history | Replace cascade deletion with soft deletion/archive policy. |
| External users consume the API | Add auth, authorization, rate limiting, request IDs, and audit logging. |
| Long-running pipeline lifecycle | Add run update/complete endpoints and explicit state transitions. |
| Production operations | Add structured logs, metrics, health/readiness separation, deployment configuration, and backups. |

## 7. Decision Summary

The current architecture is coherent for a small educational CRUD API: a thin FastAPI layer, explicit Pydantic contracts, a focused SQLite data layer, UTC timestamps, and CI checks. Its main tradeoff is simplicity over production capability. The most important future boundary is persistence: SQLite, ad hoc schema compatibility, and cascade deletion are appropriate today but need deliberate replacement or refinement as scale, audit, and operational requirements grow.