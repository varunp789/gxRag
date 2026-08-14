"use client";
import { useState, useTransition } from "react";
import { api } from "../../../../lib/api";

type Result = { content: string; score: number; citation: { label: string; asset_id: string; provenance: string[] } };
export default function RetrievalPage() {
  const [mode, setMode] = useState("hybrid"); const [query, setQuery] = useState(""); const [results, setResults] = useState<Result[]>([]); const [error, setError] = useState(""); const [pending, startTransition] = useTransition();
  function search() { startTransition(async () => { try { setError(""); const response = await api<{ results: Result[] }>(`/query/${mode}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query }) }); setResults(response.results); } catch (cause) { setError(cause instanceof Error ? cause.message : "Query failed"); } }); }
  return <main className="shell"><section className="hero"><span className="eyebrow">Retrieval playground</span><h1>Ask across your workspace.</h1><p>Test vector, hybrid, graph, multimodal, and structured retrieval with traceable citations.</p></section><section className="card grid"><label>Mode <select value={mode} onChange={(event) => setMode(event.target.value)}>{["vector", "hybrid", "graph", "multimodal", "structured"].map((item) => <option key={item}>{item}</option>)}</select></label><textarea value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ask a question about your assets" /><button onClick={search} disabled={pending || !query}>{pending ? "Searching…" : "Run query"}</button>{error ? <p>{error}</p> : null}</section><section className="grid">{results.map((result, index) => <article className="card" key={index}><h2>{result.citation.label} · {result.score.toFixed(2)}</h2><p>{result.content}</p><p><strong>Citation:</strong> {result.citation.asset_id} · {result.citation.provenance.join(" → ")}</p></article>)}</section></main>;
}
