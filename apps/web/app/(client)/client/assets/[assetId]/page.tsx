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
          This route is reserved for artifact inspection, processing history,
          and status tracking for a single asset.
        </p>
      </section>
    </main>
  );
}

