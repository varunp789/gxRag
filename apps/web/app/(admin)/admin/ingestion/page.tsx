import {
  adapterDiagnostics,
  artifactInspection,
  assetSummary,
  indexDiagnostics,
  processingQueue,
} from "../../../../lib/asset-data";

export default function AdminIngestionPage() {
  return (
    <main className="shell">
      <section className="hero">
        <span className="eyebrow">Ingestion diagnostics</span>
        <h1>Adapter and asset activity view.</h1>
        <p>
          This page now tracks the phase 5 and phase 6 scaffold: step-based
          processing, resumable jobs, artifact versions, and index sync status.
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
                {asset.adapter} adapter · {asset.status} · {asset.processingStatus}
                <br />
                Step {asset.currentStep} · {asset.artifacts} artifacts ·{" "}
                {asset.indexes} indexes
              </li>
            ))}
          </ul>
        </article>
      </section>

      <section className="grid two-up">
        <article className="card">
          <h2 className="section-title">Job queue monitor</h2>
          <ul className="portal-list">
            {processingQueue.map((job) => (
              <li key={job.jobId}>
                <strong>{job.assetTitle}</strong>
                <br />
                {job.status} · {job.currentStep}
                <br />
                {job.completedSteps} complete · resumable {job.resumable}
              </li>
            ))}
          </ul>
        </article>

        <article className="card">
          <h2 className="section-title">Artifact inspection</h2>
          <ul className="portal-list">
            {artifactInspection.map((artifact) => (
              <li key={artifact.artifact}>
                <strong>{artifact.artifact}</strong>
                <br />
                {artifact.format} · {artifact.producer} · {artifact.version}
              </li>
            ))}
          </ul>
        </article>
      </section>

      <section className="card">
        <h2 className="section-title">Index diagnostics</h2>
        <ul className="portal-list">
          {indexDiagnostics.map((item) => (
            <li key={item.index}>
              <strong>{item.index}</strong>
              <br />
              {item.backend} · {item.status} · {item.reconciliation}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
