# Azure deployment

The GitHub Actions workflow builds and tests the app, creates its Azure resources
with Bicep, publishes images to Azure Container Registry, deploys the containers,
and verifies the live cart flow.

## Architecture

- **Azure Container Apps** hosts the React/nginx frontend and Python/FastAPI API.
  Only the frontend has public ingress; nginx proxies `/api` over private,
  same-environment ingress to the API.
- **Azure Container Registry (Basic)** stores both images. Its admin account is
  disabled. A user-assigned managed identity has `AcrPull`; the GitHub Actions
  service principal has `AcrPush`.
- **SQLite** is stored in the API container's local filesystem. The API is fixed
  to one replica so the cart flow works consistently during a deployment, but
  its data is ephemeral and resets when the container restarts or a revision is
  replaced. Use a managed database for persistent or horizontally scaled use.
- **Log Analytics** receives Container Apps logs.
- **Health probes** use `/api/health/ready` for API startup/readiness and
  `/api/health/live` for API liveness. Readiness checks database connectivity;
  liveness only checks that the process is responding. The frontend keeps its
  `/` probes.

The API is the Python implementation because the shopping cart routes are
implemented there. The frontend uses same-origin API URLs, so browser requests
go through nginx and never need public access to the API. This lab subscription
disables public networking and shared-key access on storage accounts; rather
than weakening those controls or requiring a private network, the demo keeps
SQLite local to its single API replica.

## GitHub setup (one time)

Follow [OIDC-SETUP.md](./OIDC-SETUP.md) for step-by-step Microsoft Entra
federated credential setup, Azure role assignments, and GitHub secrets and
variables. No client secret or registry password is used.

## Deployment

Push to `main` or run **Build, test, and deploy to Azure** with
`workflow_dispatch`. The workflow:

1. Builds the frontend and runs Python API tests.
2. Validates both Bicep templates.
3. Creates/updates the resource group and shared resources using Bicep.
4. Builds and pushes the API and frontend images using the OIDC-authenticated
   pipeline identity.
5. Deploys the two Container Apps using Bicep.
6. Exercises products and a cart add/read flow through the public frontend URL.

## SRE Agent observability

The API's Uvicorn access logs and application logs are collected in the
Container Apps environment's Log Analytics workspace (`octosupply-lab-logs`).
Connect that workspace to the Azure SRE Agent's **Logs** data source, and add
the `octosupply-lab-api` and `octosupply-lab-frontend` Container Apps as Azure
resources. Connect the GitHub repository as a **Code** data source to let the
agent correlate production telemetry with the deployed application.

Use the API's `/api/health/live` and `/api/health/ready` endpoints to distinguish
process health from database readiness. The SRE Agent can query Container Apps
logs and Azure Monitor metrics; Container Apps health probes are separate from
the agent's conversational investigation workflow.

The target resource group must exist before the workflow runs; it validates
that group and uses it for all deployment operations. An optional
`resource-group.bicep` template is provided for separate subscription-level
resource group provisioning. All application Azure resources are defined in
`main.bicep`. The first Bicep deployment creates the registry and supporting
resources before any image push. The second deploys the app revisions with the
newly published image tags.

## Local Bicep validation

```bash
az bicep build --file infra/resource-group.bicep --stdout
az bicep build --file infra/main.bicep --stdout
```

Resource names are deterministic within the resource group and include a short
stable suffix for globally unique ACR and storage-account names. Re-running the
workflow updates the existing resources and deployments.
