import json
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class GXRagError(Exception):
    """Raised for any non-2xx API response."""

    def __init__(self, status: int, detail: str) -> None:
        super().__init__(f"gxRag request failed ({status}): {detail}")
        self.status = status
        self.detail = detail


class GXRagClient:
    """Client for the gxRag API.

    ``api_key`` accepts a workspace API key (``gxk_...``) or a user bearer token.
    A key is bound to one workspace, so ``workspace_id`` is only needed for
    user tokens that belong to several workspaces.
    """

    def __init__(self, base_url: str, workspace_id: str | None = None, api_key: str | None = None,
                 timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.workspace_id = workspace_id
        self.api_key = api_key
        self.timeout = timeout

    def _request(self, path: str, payload: dict[str, Any] | None = None, method: str | None = None) -> Any:
        headers = {"Accept": "application/json"}
        data = None
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.workspace_id:
            headers["X-Workspace-Id"] = self.workspace_id
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode()
        request = Request(f"{self.base_url}/v1{path}", data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read()
        except HTTPError as error:
            try:
                detail = json.loads(error.read()).get("detail", error.reason)
            except (ValueError, AttributeError):
                detail = str(error.reason)
            raise GXRagError(error.code, str(detail)) from None
        return json.loads(body) if body else None

    def health(self) -> dict[str, Any]: return self._request("/health")
    def query(self, mode: str, query: str, **filters: Any) -> dict[str, Any]: return self._request(f"/query/{mode}", {"query": query, **filters})
    def vector(self, query: str, **filters: Any) -> dict[str, Any]: return self.query("vector", query, **filters)
    def hybrid(self, query: str, **filters: Any) -> dict[str, Any]: return self.query("hybrid", query, **filters)
    def graph(self, query: str, **filters: Any) -> dict[str, Any]: return self.query("graph", query, **filters)
    def multimodal(self, query: str, **filters: Any) -> dict[str, Any]: return self.query("multimodal", query, **filters)
    def structured(self, query: str, **filters: Any) -> dict[str, Any]: return self.query("structured", query, **filters)
    def answer(self, mode: str, query: str, **options: Any) -> dict[str, Any]: return self._request(f"/answers/{mode}", {"query": query, **options})
    def list_assets(self) -> list[dict[str, Any]]: return self._request("/assets")
    def asset_status(self, asset_id: str) -> dict[str, Any]: return self._request(f"/assets/{asset_id}/status")
    def upload(self, **fields: Any) -> dict[str, Any]: return self._request("/assets/upload", fields)
    def process(self, asset_id: str, **options: Any) -> dict[str, Any]: return self._request(f"/assets/{asset_id}/process", options)
