from dataclasses import dataclass
from datetime import datetime, timezone

from app.models.asset import Artifact, IngestionAdapterDefinition


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class AdapterResult:
    adapter_key: str
    normalized_output_format: str
    warnings: list[str]
    source_metadata: dict[str, str]
    artifact_type: str


class IngestionAdapter:
    definition: IngestionAdapterDefinition

    def run(self, asset_id: str, workspace_id: str, title: str) -> AdapterResult:
        raise NotImplementedError


class PdfAdapter(IngestionAdapter):
    definition = IngestionAdapterDefinition(
        key="pdf",
        asset_types=["document"],
        supports_v1=True,
        normalized_output_format="markdown",
    )

    def run(self, asset_id: str, workspace_id: str, title: str) -> AdapterResult:
        return AdapterResult(
            adapter_key=self.definition.key,
            normalized_output_format=self.definition.normalized_output_format,
            warnings=[],
            source_metadata={"layout": "page-based", "ocr_fallback": "false"},
            artifact_type="normalized_raw_content",
        )


class ImageAdapter(IngestionAdapter):
    definition = IngestionAdapterDefinition(
        key="image",
        asset_types=["image"],
        supports_v1=False,
        normalized_output_format="ocr-json",
    )

    def run(self, asset_id: str, workspace_id: str, title: str) -> AdapterResult:
        return AdapterResult(
            adapter_key=self.definition.key,
            normalized_output_format=self.definition.normalized_output_format,
            warnings=["Image ingestion is scaffolded but not enabled in V1."],
            source_metadata={"layout": "region-based", "ocr_fallback": "true"},
            artifact_type="ocr_preview",
        )


class AudioAdapter(IngestionAdapter):
    definition = IngestionAdapterDefinition(
        key="audio",
        asset_types=["audio"],
        supports_v1=False,
        normalized_output_format="transcript-json",
    )

    def run(self, asset_id: str, workspace_id: str, title: str) -> AdapterResult:
        return AdapterResult(
            adapter_key=self.definition.key,
            normalized_output_format=self.definition.normalized_output_format,
            warnings=["Audio ingestion is scaffolded but not enabled in V1."],
            source_metadata={"transcript": "stub", "speaker_labels": "deferred"},
            artifact_type="transcript_preview",
        )


class SpreadsheetAdapter(IngestionAdapter):
    definition = IngestionAdapterDefinition(
        key="spreadsheet",
        asset_types=["spreadsheet"],
        supports_v1=True,
        normalized_output_format="table-json",
    )

    def run(self, asset_id: str, workspace_id: str, title: str) -> AdapterResult:
        return AdapterResult(
            adapter_key=self.definition.key,
            normalized_output_format=self.definition.normalized_output_format,
            warnings=[],
            source_metadata={"shape": "tabular", "header_inference": "enabled"},
            artifact_type="structured_table_preview",
        )


class WebContentAdapter(IngestionAdapter):
    definition = IngestionAdapterDefinition(
        key="web",
        asset_types=["web_page"],
        supports_v1=True,
        normalized_output_format="content-map-json",
    )

    def run(self, asset_id: str, workspace_id: str, title: str) -> AdapterResult:
        return AdapterResult(
            adapter_key=self.definition.key,
            normalized_output_format=self.definition.normalized_output_format,
            warnings=[],
            source_metadata={"fetch_mode": "url", "content_cleaning": "enabled"},
            artifact_type="web_content_preview",
        )


ADAPTERS: dict[str, IngestionAdapter] = {
    "document": PdfAdapter(),
    "image": ImageAdapter(),
    "audio": AudioAdapter(),
    "spreadsheet": SpreadsheetAdapter(),
    "web_page": WebContentAdapter(),
}


def get_adapter_for_asset_type(asset_type: str) -> IngestionAdapter:
    return ADAPTERS[asset_type]


def list_adapter_definitions() -> list[IngestionAdapterDefinition]:
    return [adapter.definition for adapter in ADAPTERS.values()]


def build_artifact(
    *,
    asset_id: str,
    workspace_id: str,
    adapter_key: str,
    artifact_type: str,
    output_format: str,
    warnings: list[str],
) -> Artifact:
    created_at = utc_now()
    return Artifact(
        id=f"artifact_{asset_id}_{adapter_key}_{artifact_type}",
        asset_id=asset_id,
        workspace_id=workspace_id,
        artifact_type=artifact_type,
        storage_path=(
            f"tenant/workspace/{workspace_id}/asset/{asset_id}/"
            f"{artifact_type}.{output_format.replace('-', '.')}"
        ),
        format=output_format,
        warnings=warnings,
        created_at=created_at,
    )

