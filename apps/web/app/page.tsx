import Link from "next/link";

const portals = [
  {
    href: "/client",
    name: "Client Portal",
    description:
      "Upload assets, monitor processing, inspect graphs, and test retrieval APIs.",
  },
  {
    href: "/admin",
    name: "Admin Portal",
    description:
      "Operate tenants, inspect jobs, monitor usage, and support production workflows.",
  },
];

export default function HomePage() {
  return (
    <main className="shell">
      <section className="hero">
        <span className="eyebrow">Phase 0 foundation</span>
        <h1>Graph RAG platform monorepo scaffold.</h1>
        <p>
          This workspace now has a FastAPI backend, a worker service, and a
          Next.js App Router frontend prepared for both customer and admin
          surfaces.
        </p>
        <div className="pill-row">
          <span className="pill">FastAPI API</span>
          <span className="pill">Worker service</span>
          <span className="pill">Next.js App Router</span>
          <span className="pill">Client + Admin portals</span>
        </div>
      </section>

      <section className="grid two-up">
        {portals.map((portal) => (
          <Link className="card" href={portal.href} key={portal.name}>
            <h2>{portal.name}</h2>
            <p>{portal.description}</p>
          </Link>
        ))}
      </section>
    </main>
  );
}

