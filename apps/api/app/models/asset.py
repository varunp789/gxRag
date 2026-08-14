from pydantic import BaseModel, Field, HttpUrl


class AssetSource(BaseModel):
    id: str
    asset_id: str
    source_type: str
    location: str
    mime_type: str
    created_at: str


class AssetUpload(BaseModel):
    id: str
    asset_id: str
    file_name: str
    mime_type: str
    size_bytes: int
    uploaded_at: str


class AssetVersion(BaseModel):
    id: str
    asset_id: str
    version: int
    created_at: str
    status: str


class Artifact(BaseModel):
    id: str
    asset_id: str
    workspace_id: str
    artifact_type: str
    storage_path: str
    format: str
    warnings: list[str] = Field(default_factory=list)
    created_at: str


class JobStep(BaseModel):
    id: str
    job_id: str
    name: str
    status: str
    adapter_key: str | None = None
    artifact_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ProcessingJob(BaseModel):
    id: str
    asset_id: str
    workspace_id: str
    status: str
    trigger: str
    created_at: str
    updated_at: str
    current_step: str
    step_count: int
    steps: list[JobStep] = Field(default_factory=list)


class Asset(BaseModel):
    id: str
    workspace_id: str
    tenant_id: str
    asset_type: str
    title: str
    source_type: str
    status: str
    ingestion_status: str
    processing_status: str
    created_at: str
    updated_at: str
    latest_version_id: str
    source_id: str
    upload_id: str | None = None
    current_job_id: str | None = None
    adapter_key: str | None = None
    warnings: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class AssetBundle(BaseModel):
    asset: Asset
    source: AssetSource
    version: AssetVersion
    upload: AssetUpload | None = None
    jobs: list[ProcessingJob] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)


class AssetStatusResponse(BaseModel):
    asset_id: str
    workspace_id: str
    asset_status: str
    ingestion_status: str
    processing_status: str
    current_job: ProcessingJob | None = None
    artifacts: list[Artifact] = Field(default_factory=list)


class UploadAssetRequest(BaseModel):
    title: str
    asset_type: str
    file_name: str
    mime_type: str
    size_bytes: int
    tags: list[str] = Field(default_factory=list)


class CreateAssetFromUrlRequest(BaseModel):
    title: str
    asset_type: str
    url: HttpUrl
    mime_type: str
    tags: list[str] = Field(default_factory=list)


class ProcessAssetRequest(BaseModel):
    trigger: str = "manual"


class IngestionAdapterDefinition(BaseModel):
    key: str
    asset_types: list[str] = Field(default_factory=list)
    supports_v1: bool
    normalized_output_format: str


class IngestionDiagnostic(BaseModel):
    adapter: IngestionAdapterDefinition
    asset_count: int
    job_count: int
    recent_warning_count: int
    latest_asset_id: str | None = None

