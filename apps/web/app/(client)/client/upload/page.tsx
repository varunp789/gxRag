import { uploadModes } from "../../../../lib/asset-data";

export default function ClientUploadPage() {
  return (
    <main className="shell">
      <section className="hero">
        <span className="eyebrow">Asset upload</span>
        <h1>Unified ingestion entry point.</h1>
        <p>
          This page represents the phase 3 asset registration flow for uploads
          and URL-based ingestion within a workspace.
        </p>
      </section>

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

