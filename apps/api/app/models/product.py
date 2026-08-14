from pydantic import BaseModel, Field


class ProductPackaging(BaseModel):
    sku: str
    name: str
    audience: str
    billing_unit: str


class UsageUnit(BaseModel):
    key: str
    label: str
    description: str


class SourceType(BaseModel):
    key: str
    label: str
    enabled_in_v1: bool


class RetrievalMode(BaseModel):
    key: str
    label: str
    enabled_in_v1: bool


class AdminCapability(BaseModel):
    key: str
    label: str


class AssetOutputContract(BaseModel):
    fields: list[str] = Field(default_factory=list)


class ApiEndpointGroup(BaseModel):
    name: str
    endpoints: list[str] = Field(default_factory=list)


class QueryContract(BaseModel):
    request_fields: list[str] = Field(default_factory=list)
    response_fields: list[str] = Field(default_factory=list)
    retrieval_modes: list[str] = Field(default_factory=list)


class ProductDefinition(BaseModel):
    packaging: list[ProductPackaging]
    usage_units: list[UsageUnit]
    source_types: list[SourceType]
    retrieval_modes: list[RetrievalMode]
    admin_capabilities: list[AdminCapability]
    output_contract: AssetOutputContract
    query_contract: QueryContract
    versioning_policy: str
    compatibility_policy: str
    endpoint_groups: list[ApiEndpointGroup]
