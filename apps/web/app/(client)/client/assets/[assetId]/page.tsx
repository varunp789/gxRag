import Link from "next/link";
type AssetDetailPageProps = {
  params: Promise<{ assetId: string }>;
};

export default async function AssetDetailPage({ params }: AssetDetailPageProps) {
  const { assetId } = await params;

  return (
    <main className="shell">
      <section className="hero">
        <span className="eyebrow">Asset detail</span>
        <h1>{assetId}</h1>
        <p>
          Review source artifacts, graph data, and processing status.
        </p>
      </section>
      <section className="grid two-up"><Link className="card" href={`/client/assets/${assetId}/timeline`}><h2>Processing timeline</h2><p>Follow each job step and retry state.</p></Link><Link className="card" href="/client/retrieval"><h2>Explore retrieval</h2><p>Query this asset with citations.</p></Link></section>
    </main>
  );
}
