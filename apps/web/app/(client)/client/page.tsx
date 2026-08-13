const capabilities = [
  "Workspace dashboard",
  "Asset upload",
  "Processing timeline",
  "Graph and table exploration",
  "Retrieval playground",
];

export default function ClientPortalPage() {
  return (
    <main className="shell">
      <section className="hero">
        <span className="eyebrow">Client portal</span>
        <h1>Customer-facing workspace experience.</h1>
        <p>
          This route group is reserved for tenant users who upload content and
          consume retrieval-ready knowledge.
        </p>
      </section>

      <section className="grid two-up">
        <article className="card">
          <h2 className="section-title">Initial areas</h2>
          <ul className="portal-list">
            {capabilities.map((capability) => (
              <li key={capability}>{capability}</li>
            ))}
          </ul>
        </article>
      </section>
    </main>
  );
}

