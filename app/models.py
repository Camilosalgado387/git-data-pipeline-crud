
from pydantic import BaseModel, Field


class DatasetBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["sales_transactions_daily"])
    source: str = Field(..., examples=["s3://company-lake/raw/sales/"])
    format: str = Field(default="parquet", examples=["parquet", "csv", "json"])
    row_count: int = Field(default=0, ge=0)
    schema_version: str = Field(default="v1.0", examples=["v1.0"])
    status: str = Field(default="active", examples=["active", "deprecated", "archived"])
    owner: str = Field(..., examples=["data-team@company.com"])


class DatasetCreate(DatasetBase):
    pass


class DatasetUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    source: str | None = None
    format: str | None = None
    row_count: int | None = Field(None, ge=0)
    schema_version: str | None = None
    status: str | None = None
    owner: str | None = None


class DatasetResponse(DatasetBase):
    id: int
    created_at: str
    updated_at: str


class PipelineRunCreate(BaseModel):
    run_type: str = Field(default="ingestion", examples=["ingestion", "transformation", "quality_check"])
    status: str = Field(default="success", examples=["running", "success", "failed"])
    records_processed: int = Field(default=0, ge=0)


class PipelineRunResponse(BaseModel):
    id: int
    dataset_id: int
    run_type: str
    status: str
    records_processed: int
    started_at: str
    completed_at: str | None = None
