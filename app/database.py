import os
import sqlite3
from datetime import datetime, timezone

from app.models import (
    DatasetCreate,
    DatasetResponse,
    DatasetUpdate,
    PipelineRunCreate,
    PipelineRunResponse,
)

DEFAULT_DB_PATH = os.environ.get("DATABASE_PATH", "catalog.db")


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    path = db_path if db_path is not None else DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str | None = None) -> None:
    conn = get_connection(db_path)
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                source TEXT NOT NULL,
                format TEXT NOT NULL DEFAULT 'parquet',
                row_count INTEGER NOT NULL DEFAULT 0,
                schema_version TEXT NOT NULL DEFAULT 'v1.0',
                status TEXT NOT NULL DEFAULT 'active',
                owner TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                run_type TEXT NOT NULL,
                status TEXT NOT NULL,
                records_processed INTEGER NOT NULL DEFAULT 0,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
            );
        """)
    conn.close()


def _row_to_dataset(row: sqlite3.Row) -> DatasetResponse:
    return DatasetResponse(
        id=row["id"],
        name=row["name"],
        source=row["source"],
        format=row["format"],
        row_count=row["row_count"],
        schema_version=row["schema_version"],
        status=row["status"],
        owner=row["owner"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_run(row: sqlite3.Row) -> PipelineRunResponse:
    return PipelineRunResponse(
        id=row["id"],
        dataset_id=row["dataset_id"],
        run_type=row["run_type"],
        status=row["status"],
        records_processed=row["records_processed"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
    )


def create_dataset(payload: DatasetCreate, db_path: str | None = None) -> DatasetResponse:
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection(db_path)
    with conn:
        cursor = conn.execute(
            """
            INSERT INTO datasets (name, source, format, row_count, schema_version, status, owner, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.name,
                payload.source,
                payload.format,
                payload.row_count,
                payload.schema_version,
                payload.status,
                payload.owner,
                now,
                now,
            ),
        )
        dataset_id = cursor.lastrowid

    return get_dataset(dataset_id, db_path=db_path)  # type: ignore[return-value]


def get_dataset(dataset_id: int, db_path: str | None = None) -> DatasetResponse | None:
    conn = get_connection(db_path)
    cursor = conn.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    return _row_to_dataset(row)


def list_datasets(skip: int = 0, limit: int = 50, db_path: str | None = None) -> list[DatasetResponse]:
    conn = get_connection(db_path)
    cursor = conn.execute("SELECT * FROM datasets ORDER BY id DESC LIMIT ? OFFSET ?", (limit, skip))
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_dataset(row) for row in rows]


def update_dataset(
    dataset_id: int, payload: DatasetUpdate, db_path: str | None = None
) -> DatasetResponse | None:
    existing = get_dataset(dataset_id, db_path=db_path)
    if existing is None:
        return None

    update_fields = payload.model_dump(exclude_unset=True)
    if not update_fields:
        return existing

    update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()

    set_clauses = [f"{field} = ?" for field in update_fields]
    values = list(update_fields.values())
    values.append(dataset_id)

    query = f"UPDATE datasets SET {', '.join(set_clauses)} WHERE id = ?"

    conn = get_connection(db_path)
    with conn:
        conn.execute(query, tuple(values))
    conn.close()

    return get_dataset(dataset_id, db_path=db_path)


def delete_dataset(dataset_id: int, db_path: str | None = None) -> bool:
    conn = get_connection(db_path)
    with conn:
        cursor = conn.execute("DELETE FROM datasets WHERE id = ?", (dataset_id,))
        deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def create_pipeline_run(
    dataset_id: int, payload: PipelineRunCreate, db_path: str | None = None
) -> PipelineRunResponse | None:
    dataset = get_dataset(dataset_id, db_path=db_path)
    if dataset is None:
        return None

    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection(db_path)
    with conn:
        cursor = conn.execute(
            """
            INSERT INTO pipeline_runs (dataset_id, run_type, status, records_processed, started_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                dataset_id,
                payload.run_type,
                payload.status,
                payload.records_processed,
                now,
                now if payload.status != "running" else None,
            ),
        )
        run_id = cursor.lastrowid
    conn.close()

    conn = get_connection(db_path)
    cursor = conn.execute("SELECT * FROM pipeline_runs WHERE id = ?", (run_id,))
    row = cursor.fetchone()
    conn.close()
    return _row_to_run(row)


def list_pipeline_runs(dataset_id: int, db_path: str | None = None) -> list[PipelineRunResponse]:
    conn = get_connection(db_path)
    cursor = conn.execute("SELECT * FROM pipeline_runs WHERE dataset_id = ? ORDER BY id DESC", (dataset_id,))
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_run(row) for row in rows]
