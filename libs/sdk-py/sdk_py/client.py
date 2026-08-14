import json
from typing import Any
from urllib.request import Request, urlopen


class GXRagClient:
    def __init__(self, base_url: str, workspace_id: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.workspace_id = workspace_id

    def _request(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {"Accept": "application/json"}
        data = None
        if self.workspace_id:
            headers["X-Workspace-Id"] = self.workspace_id
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode()
        request = Request(f"{self.base_url}/v1{path}", data=data, headers=headers)
        with urlopen(request) as response:
            return json.loads(response.read())

    def health(self) -> dict[str, Any]: return self._request("/health")
    def query(self, mode: str, query: str, **filters: Any) -> dict[str, Any]: return self._request(f"/query/{mode}", {"query": query, **filters})
    def vector(self, query: str, **filters: Any) -> dict[str, Any]: return self.query("vector", query, **filters)
    def hybrid(self, query: str, **filters: Any) -> dict[str, Any]: return self.query("hybrid", query, **filters)
    def graph(self, query: str, **filters: Any) -> dict[str, Any]: return self.query("graph", query, **filters)
    def structured(self, query: str, **filters: Any) -> dict[str, Any]: return self.query("structured", query, **filters)
    def answer(self, mode: str, query: str, **options: Any) -> dict[str, Any]: return self._request(f"/answers/{mode}", {"query": query, **options})
