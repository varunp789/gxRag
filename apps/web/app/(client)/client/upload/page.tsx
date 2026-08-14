import Link from "next/link";
import { uploadModes } from "../../../../lib/asset-data";

export default function ClientUploadPage() {
  return (
    <main className="shell">
      <section className="hero">
        <span className="eyebrow">Asset upload</span>
        <h1>Unified ingestion entry point.</h1>
        <p>
          Add files or web content to the active workspace, then monitor queued
          processing from the asset registry.
        </p>
      </section>
      <section className="card"><p>For API ingestion, use the SDK or POST to the upload endpoint with source metadata and optional encoded content.</p><Link className="pill" href="/client/assets">View assets</Link></section>

      <section className="grid two-up">
        {uploadModes.map((mode) => (
          <article className="card" key={mode.label}>
            <h2>{mode.label}</h2>
            <p>{mode.description}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
