const controls = [
  "Tenant and workspace management",
  "Job queue inspection",
  "Pipeline retries",
  "Usage and billing oversight",
  "Audit and support workflows",
];

export default function AdminPortalPage() {
  return (
    <main className="shell">
      <section className="hero">
        <span className="eyebrow">Admin portal</span>
        <h1>Internal operations surface.</h1>
        <p>
          This route group is reserved for platform administrators and support
          operations.
        </p>
      </section>

      <section className="grid two-up">
        <article className="card">
          <h2 className="section-title">Initial areas</h2>
          <ul className="portal-list">
            {controls.map((control) => (
              <li key={control}>{control}</li>
            ))}
          </ul>
        </article>
      </section>
    </main>
  );
}

