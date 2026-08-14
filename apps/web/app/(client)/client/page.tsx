import Link from "next/link";

import { workspaces } from "../../../lib/portal-data";

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

        <article className="card">
          <h2 className="section-title">Workspace switcher</h2>
          <ul className="portal-list">
            {workspaces.map((workspace) => (
              <li key={workspace.id}>
                <strong>{workspace.name}</strong>
                <br />
                {workspace.tenant} · {workspace.environment} · {workspace.region}
              </li>
            ))}
          </ul>
        </article>

        <article className="card">
          <h2 className="section-title">Phase 3 entry points</h2>
          <ul className="portal-list">
            <li>
              <Link href="/client/upload">Open unified upload flow</Link>
            </li>
            <li>
              <Link href="/client/assets">Open workspace asset registry</Link>
            </li>
          </ul>
        </article>
      </section>
    </main>
  );
}
