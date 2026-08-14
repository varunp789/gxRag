import Link from "next/link";

import { adminActions, adminTenants } from "../../../lib/portal-data";

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

        <article className="card">
          <h2 className="section-title">Tenant inspection</h2>
          <ul className="portal-list">
            {adminTenants.map((tenant) => (
              <li key={tenant.id}>
                <strong>{tenant.name}</strong>
                <br />
                {tenant.plan} plan · {tenant.workspaces} workspace(s) ·{" "}
                {tenant.status}
              </li>
            ))}
          </ul>
        </article>

        <article className="card">
          <h2 className="section-title">Admin actions</h2>
          <ul className="portal-list">
            {adminActions.map((action) => (
              <li key={action}>{action}</li>
            ))}
          </ul>
        </article>

        <article className="card">
          <h2 className="section-title">Phase 4 diagnostics</h2>
          <ul className="portal-list">
            <li>
              <Link href="/admin/ingestion">Open ingestion diagnostics</Link>
            </li>
          </ul>
        </article>
      </section>
    </main>
  );
}
