import Link from "next/link";

import { assetSummary } from "../../../../lib/asset-data";

export default function ClientAssetsPage() {
  return (
    <main className="shell">
      <section className="hero">
        <span className="eyebrow">Assets</span>
        <h1>Workspace asset registry.</h1>
        <p>
          This page maps to the phase 3 asset list and status endpoints for the
          active workspace.
        </p>
      </section>

      <section className="grid">
        {assetSummary.map((asset) => (
          <Link className="card" href={`/client/assets/${asset.id}`} key={asset.id}>
            <h2>{asset.title}</h2>
            <p>
              {asset.assetType} · {asset.sourceType} · {asset.workspace}
            </p>
            <p>
              <strong>Status:</strong> {asset.status} / {asset.processingStatus}
            </p>
          </Link>
        ))}
      </section>
    </main>
  );
}

