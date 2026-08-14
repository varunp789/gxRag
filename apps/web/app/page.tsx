import Link from "next/link";

import { productPackaging } from "../lib/portal-data";

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
        <span className="eyebrow">gxRag platform</span>
        <h1>Knowledge you can retrieve, trace, and trust.</h1>
        <p>
          Turn documents, tables, and web content into grounded retrieval and
          answer experiences for your product.
        </p>
        <div className="pill-row">
          <span className="pill">FastAPI API</span>
          <span className="pill">Worker service</span>
          <span className="pill">Next.js App Router</span>
          <span className="pill">Client + Admin portals</span>
          <Link className="pill" href="/client/onboarding">Start a workspace</Link>
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

      <section className="grid two-up">
        {productPackaging.map((pkg) => (
          <article className="card" key={pkg.name}>
            <h2>{pkg.name}</h2>
            <p>{pkg.audience}</p>
            <p>
              <strong>Billing:</strong> {pkg.billingUnit}
            </p>
          </article>
        ))}
      </section>
    </main>
  );
}
