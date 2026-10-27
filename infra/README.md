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
- **Azure Files (Standard LRS)** persists the SQLite database at `/app/data`.
  The API is intentionally fixed to one replica and disables SQLite WAL on the
  network share. This supports a persistent demo/cart flow, not a horizontally
  scaled production database. Move to a managed database before scaling the API.
- **Log Analytics** receives Container Apps logs.

The API is the Python implementation because the shopping cart routes are
implemented there. The frontend uses same-origin API URLs, so browser requests
go through nginx and never need public access to the API.

## GitHub setup (one time)

Create an Entra application/service principal for GitHub Actions and configure
an OIDC federated credential with subject:

```text
repo:<OWNER>/<REPOSITORY>:ref:refs/heads/main
```

Set these GitHub Actions **secrets**:

| Secret | Value |
| --- | --- |
| `AZURE_CLIENT_ID` | Entra application/client ID |
| `AZURE_TENANT_ID` | Entra tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Target subscription ID |

Set these GitHub Actions **variables**:

| Variable | Value |
| --- | --- |
| `AZURE_RESOURCE_GROUP` | Name for the deployment resource group |
| `AZURE_LOCATION` | Azure region supporting Container Apps |
| `AZURE_CLIENT_OBJECT_ID` | Service principal's object/principal ID |

Grant that principal permission to create the resource group, deploy the
resources, and assign the two narrowly scoped ACR roles. The simple built-in
setup is **Contributor** and **User Access Administrator** at the subscription
scope. A more restrictive custom role is appropriate for a long-lived
production pipeline. No client secret or registry password is used.

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

The resource group deployment is defined in `resource-group.bicep`; all other
Azure resources are defined in `main.bicep`. The first Bicep deployment creates
the registry and supporting resources before any image push. The second deploys
the app revisions with the newly published image tags.

## Local Bicep validation

```bash
az bicep build --file infra/resource-group.bicep --stdout
az bicep build --file infra/main.bicep --stdout
```

Resource names are deterministic within the resource group and include a short
stable suffix for globally unique ACR and storage-account names. Re-running the
workflow updates the existing resources and deployments.
