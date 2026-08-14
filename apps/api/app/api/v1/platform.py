from fastapi import APIRouter

from app.models.product import ProductDefinition, QueryContract
from app.services.catalog import get_product_definition

router = APIRouter(prefix="/platform")


@router.get("/definition", response_model=ProductDefinition)
def get_definition() -> ProductDefinition:
    return get_product_definition()


@router.get("/api-scope", response_model=list[str])
def get_api_scope() -> list[str]:
    definition = get_product_definition()
    endpoints: list[str] = []
    for group in definition.endpoint_groups:
        endpoints.extend(group.endpoints)
    return endpoints


@router.get("/query-contract", response_model=QueryContract)
def get_query_contract() -> QueryContract:
    return get_product_definition().query_contract
