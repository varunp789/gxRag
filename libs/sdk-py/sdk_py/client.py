from urllib.request import urlopen


class GXRagClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def health(self) -> bytes:
        with urlopen(f"{self.base_url}/v1/health") as response:
            return response.read()

