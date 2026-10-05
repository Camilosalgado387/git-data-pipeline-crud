from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, status

from app.database import (
    create_dataset,
    create_pipeline_run,
    delete_dataset,
    get_dataset,
    init_db,
    list_datasets,
    list_pipeline_runs,
    update_dataset,
)
from app.models import (
    DatasetCreate,
    DatasetResponse,
    DatasetUpdate,
    PipelineRunCreate,
    PipelineRunResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database on startup
    init_db()
    yield


app = FastAPI(
    title="Data Pipeline & Dataset Catalog API",
    description="A hands-on Data Engineering API to manage dataset metadata and pipeline run logs while mastering Git and CI/CD.",
    version="0.2.0",
    lifespan=lifespan,
)


@app.get("/", tags=["General"])
def read_root():
    return {
        "project": "Data Pipeline & Dataset Catalog API",
        "version": "0.2.0",
        "docs_url": "/docs",
        "status": "healthy",
    }


@app.get("/health", tags=["General"])
def health_check():
    return {"status": "ok"}


@app.post(
    "/datasets",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Datasets"],
)
def create_dataset_endpoint(payload: DatasetCreate):
    return create_dataset(payload)


@app.get(
    "/datasets",
    response_model=list[DatasetResponse],
    tags=["Datasets"],
)
def list_datasets_endpoint(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max records to return"),
):
    return list_datasets(skip=skip, limit=limit)


@app.get(
    "/datasets/{dataset_id}",
    response_model=DatasetResponse,
    tags=["Datasets"],
)
def get_dataset_endpoint(dataset_id: int):
    dataset = get_dataset(dataset_id)
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID {dataset_id} not found",
        )
    return dataset


@app.put(
    "/datasets/{dataset_id}",
    response_model=DatasetResponse,
    tags=["Datasets"],
)
def update_dataset_endpoint(dataset_id: int, payload: DatasetUpdate):
    updated = update_dataset(dataset_id, payload)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID {dataset_id} not found",
        )
    return updated


@app.delete(
    "/datasets/{dataset_id}",
    status_code=status.HTTP_200_OK,
    tags=["Datasets"],
)
def delete_dataset_endpoint(dataset_id: int):
    deleted = delete_dataset(dataset_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID {dataset_id} not found",
        )
    return {"message": f"Dataset {dataset_id} successfully deleted"}


@app.post(
    "/datasets/{dataset_id}/runs",
    response_model=PipelineRunResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Pipeline Runs"],
)
def log_pipeline_run_endpoint(dataset_id: int, payload: PipelineRunCreate):
    run = create_pipeline_run(dataset_id, payload)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID {dataset_id} not found",
        )
    return run


@app.get(
    "/datasets/{dataset_id}/runs",
    response_model=list[PipelineRunResponse],
    tags=["Pipeline Runs"],
)
def list_pipeline_runs_endpoint(dataset_id: int):
    dataset = get_dataset(dataset_id)
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID {dataset_id} not found",
        )
    return list_pipeline_runs(dataset_id)
