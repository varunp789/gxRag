import { adapterDiagnostics, assetSummary } from "../../../../lib/asset-data";

export default function AdminIngestionPage() {
  return (
    <main className="shell">
      <section className="hero">
        <span className="eyebrow">Ingestion diagnostics</span>
        <h1>Adapter and asset activity view.</h1>
        <p>
          This page reflects the phase 4 admin diagnostics surface for adapter
          coverage, ingestion status, and source-specific inspection.
        </p>
      </section>

      <section className="grid two-up">
        <article className="card">
          <h2 className="section-title">Adapter coverage</h2>
          <ul className="portal-list">
            {adapterDiagnostics.map((item) => (
              <li key={item.adapter}>
                <strong>{item.adapter}</strong>
                <br />
                {item.supported} · {item.output}
                <br />
                {item.notes}
              </li>
            ))}
          </ul>
        </article>

        <article className="card">
          <h2 className="section-title">Recent asset activity</h2>
          <ul className="portal-list">
            {assetSummary.map((asset) => (
              <li key={asset.id}>
                <strong>{asset.title}</strong>
                <br />
                {asset.adapter} adapter · {asset.status} ·{" "}
                {asset.processingStatus}
              </li>
            ))}
          </ul>
        </article>
      </section>
    </main>
  );
}

