import Link from "next/link";
export default function Tenants(){return <main className="shell"><section className="hero"><span className="eyebrow">Tenants</span><h1>Customer directory.</h1><p>Inspect tenant plans, workspace status, and support context without database access.</p></section><section className="card"><Link href="/admin">GET /v1/admin/tenants</Link></section></main>}
