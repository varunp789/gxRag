import Link from "next/link";
import { ApiError, api } from "../../../../../../lib/api";
import { buildTimeline, type AssetStatus } from "../../../../../../lib/timeline";

type Props = { params: Promise<{ assetId: string }> };

const marker: Record<string, string> = { done: "✓", active: "…", failed: "✗", pending: "○" };

export default async function Timeline({ params }: Props) {
  const { assetId } = await params;
  let status: AssetStatus | null = null;
  let error: string | null = null;
  try {
    status = await api<AssetStatus>(`/assets/${encodeURIComponent(assetId)}/status`);
  } catch (caught) {
    error = caught instanceof ApiError && caught.status === 404 ? "Asset not found." : "Processing status is unavailable right now.";
  }
  const timeline = status ? buildTimeline(status) : null;

  return (
    <main className="shell">
      <section className="hero">
        <span className="eyebrow">Processing timeline</span>
        <h1>{assetId}</h1>
        <p>{timeline ? timeline.headline : error}</p>
      </section>
      {timeline && (
        <section className="card">
          <progress value={timeline.progress} max={100} aria-label="Processing progress" />
          <ol className="portal-list">
            {timeline.entries.map((entry) => (
              <li key={entry.id} data-state={entry.state}>
                <span aria-hidden="true">{marker[entry.state]}</span> {entry.label}
                {entry.detail && <small> — {entry.detail}</small>}
                {entry.retryable && <small> (will retry)</small>}
              </li>
            ))}
          </ol>
          {timeline.indexIssues.length > 0 && (
            <ul role="alert">
              {timeline.indexIssues.map((issue) => (
                <li key={issue}>{issue}</li>
              ))}
            </ul>
          )}
        </section>
      )}
      <p>
        <Link href={`/client/assets/${assetId}`}>Back to asset</Link>
      </p>
    </main>
  );
}
