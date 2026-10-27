# OctoSupply SRE Agent exercise

## Scope and telemetry

The monitored deployment is in `rg-labuser-0034`:

- Frontend: `octosupply-lab-frontend`
- API: `octosupply-lab-api`
- Container Apps environment: `octosupply-lab-env`
- Log Analytics workspace: `octosupply-lab-logs`

The Container Apps environment sends console and system logs to the workspace.
Container Apps also exposes platform metrics through Azure Monitor. The API's
`/api/health/live` endpoint reports process liveness; `/api/health/ready`
checks SQLite connectivity and returns HTTP 503 when the database cannot be
reached. The Container Apps startup/readiness probes use the readiness
endpoint, and the liveness probe uses the liveness endpoint.
For the API Container App, Azure Monitor publishes `Requests`, `ResponseTime`,
`RestartCount`, `Replicas`, `CpuPercentage`, and `MemoryPercentage`; this app
does not currently emit custom business metrics.

The existing `octocat-dev-sre` agent has Azure resource access scoped to this
resource group. Its action mode remains **Review** with **Low** access; it does
not apply remediations autonomously. A Log Analytics connector named
`octosupply-lab-logs` was added to the agent.

## Agent preflight and manual findings

At 15:04 UTC on 2026-10-27, the SRE Agent was asked to verify access to only the
named OctoSupply apps and workspace, without changing resources.

**The agent surfaced:**

- Its read-only queries returned rows from both `ContainerAppConsoleLogs_CL`
  and `ContainerAppSystemLogs_CL` for the exact frontend and API app names.
- Revision `octosupply-lab-frontend--0000002` was healthy with one replica;
  `octosupply-lab-api--0000002` was healthy with one replica at its configured
  maximum.
- Recent requests to `/` and `/api/cart` returned HTTP 200. It also found the
  pre-deployment `/api/health/live` request returning 404 and no current probe
  failures.
- It noted `VolumeMountFailure` entries from older API revisions; these
  preceded the healthy revision and were not evidence of a current failure.

**Manual investigation found:**

- The 404 was expected at that point: the API had not yet implemented health
  routes, and the Bicep module still pointed every probe at `/`. The API source
  and probe paths were inspected directly before adding distinct health
  endpoints.
- A direct request through the public frontend reproduced the health-route 404.
- The SRE Agent's earlier thread initially described a different `octocat-dev`
  deployment in the same resource group. Supplying the exact OctoSupply app,
  environment, and workspace names prevented that unrelated context from being
  treated as the target.
- The SRE Agent's GitHub OAuth popup was blocked by the browser, so repository
  source indexing was not connected. Code-level correlation therefore still
  required manual source inspection.

The first rollout of the health endpoints failed the workflow's live check:
the API routes were initially declared without the repository's existing
`/api` route prefix, so the public `/api/health/live` request returned 404.
Manual comparison of the route declarations, existing `/api/*` routes, and
the nginx proxy path identified the mismatch. The API routes and Bicep probe
paths were aligned to `/api/health/*`. The corrected run
[40528185951](https://github.com/Phillips57/microhack-sdlc/actions/runs/40528185951)
passed, including live health and cart checks. Manual requests then returned
HTTP 200 from `/api/health/live`, `/api/health/ready`, and `/api/products`; a
cart item add/read also succeeded. The deployed API and frontend are both on
revision `0000004`, with the API probes configured for `/api/health/*`.

## Controlled fault and recovery

At 15:18:26 UTC on 2026-10-27, a reversible API configuration fault was
introduced with `az containerapp update`, setting `DB_FILE` to
`/proc/self/status/app.db`. This created API revision
`octosupply-lab-api--0000005`.

**Manual evidence:**

- The new revision repeatedly exited during startup. Console logs at
  15:19:03, 15:19:14, 15:19:35, and 15:20:16 UTC recorded
  `FileExistsError: [Errno 17] File exists: '/proc/7/status'`.
- System logs recorded container exit code 3 with reason `ProcessExited`;
  revision 0000005 remained in `Activating` with no healthy state.
- The previous revision `octosupply-lab-api--0000004` remained healthy and
  served traffic. Public health and product requests still returned HTTP 200.
  Container Apps is configured for single-revision mode and kept the healthy
  revision serving traffic; an attempt to route directly to revision 0000005
  was rejected because weighted traffic requires multiple-revision mode. I
  left the app in single-revision mode rather than changing that safety
  setting merely to create a user-facing outage.

  **The Agent surfaced:**

  - Revision `0000005` could not start because `DB_FILE` was
    `/proc/self/status/app.db`; it found the `FileExistsError`, container exit
    code 3, and compared the failing setting with healthy revision `0000004`,
    whose `DB_FILE` was `/tmp/app.db`.
  - It correctly classified this as a failed rollout, not an observed API
    outage: Container Apps kept 100% of traffic on healthy revision `0000004`.
    The Agent noted its API-only evidence could not establish the external
    frontend/cart outcome.

  **Manual follow-up:** Direct public checks through the frontend returned 200
  for both health routes and products while revision `0000005` was failing. A
  cart add/read also succeeded through the frontend, confirming the synthetic
  user flow remained available. Revision `0000005` was not receiving requests.

  At 15:25:29 UTC, I restored `DB_FILE=/tmp/app.db`, creating
  `octosupply-lab-api--0000006`. Azure reported that revision healthy with one
  replica. Public health, products, and cart add/read checks passed. Logs from
  revision `0000006` show successful startup, `/api/health/live` and
  `/api/health/ready` returning 200, and cart requests returning 200.

  **Agent post-recovery verification (15:28 UTC):** The Agent independently
  confirmed API revision `0000006` was latest and ready, healthy with one
  replica, and configured with `DB_FILE=/tmp/app.db`. Frontend revision
  `0000004` was also latest, ready, and healthy with one replica. Workspace
  logs after 15:25 UTC showed both health routes returning 200 and cart add/read
  returning 200 through the frontend at approximately 15:26:25 UTC. It found no
  console errors or system probe failures through 15:28 UTC and made no
  resource changes.

  ## Reliability backlog

  - Replace the single-replica, ephemeral SQLite store with a managed database
    before using this pattern for durable or horizontally scaled workloads.
  - Add Azure Monitor alert rules for failed Container Apps revisions, readiness
    probe failures, and sustained HTTP 5xx rates, then route alerts into the
    SRE Agent incident workflow. This exercise used an interactive investigation;
    it did not configure automatic alert-to-agent triggering.
  - Connect the GitHub repository to the SRE Agent with a least-privilege
    GitHub App or approved OAuth flow. The browser blocked the OAuth popup, so
    this run had telemetry and Azure-resource context but no indexed source-code
    context.
  - Add OpenTelemetry/Application Insights traces for API requests and database
    dependencies; current evidence is primarily Container Apps logs, health
    probes, and platform metrics.
  - Keep the deployment workflow's health and cart smoke checks, and consider a
    staged rollout/rollback policy for failed revisions.
