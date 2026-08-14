export const productPackaging = [
  {
    name: "API Starter",
    audience: "Teams embedding Graph RAG in their own product",
    billingUnit: "Documents + queries",
  },
  {
    name: "Hosted Workspace",
    audience: "Teams using the client portal and managed retrieval",
    billingUnit: "Workspace + usage",
  },
  {
    name: "Enterprise",
    audience: "Organizations needing governance and admin operations",
    billingUnit: "Contracted capacity",
  },
];

export const workspaces = [
  {
    id: "ws_orbit_prod",
    name: "Orbit Production",
    tenant: "Orbit Bio Labs",
    environment: "production",
    role: "workspace_owner",
    region: "us-east-1",
  },
  {
    id: "ws_orbit_research",
    name: "Orbit Research",
    tenant: "Orbit Bio Labs",
    environment: "staging",
    role: "workspace_owner",
    region: "us-east-1",
  },
  {
    id: "ws_rivet_trial",
    name: "Rivet Trial Workspace",
    tenant: "Rivet Capital",
    environment: "production",
    role: "workspace_owner",
    region: "eu-west-1",
  },
];

export const adminTenants = [
  {
    id: "tenant_orbit",
    name: "Orbit Bio Labs",
    plan: "Growth",
    status: "active",
    workspaces: 2,
  },
  {
    id: "tenant_rivet",
    name: "Rivet Capital",
    plan: "Starter",
    status: "trial",
    workspaces: 1,
  },
];

export const adminActions = [
  "Review tenant plans and quotas",
  "Inspect workspace access and API keys",
  "Audit support activity and admin actions",
  "Prepare for asset and job operations in phase 3",
];

