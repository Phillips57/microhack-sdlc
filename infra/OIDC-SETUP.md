# Set up GitHub Actions OIDC for Azure

This guide configures the identity used by
[`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml). OIDC lets
GitHub exchange a short-lived token for Azure access; you do not create or store
an Azure client secret.

The workflow currently trusts pushes to `main` and manual runs of that
workflow. Its federated credential must match the repository and branch exactly.

## 1. Create an app registration

In the [Microsoft Entra admin center](https://entra.microsoft.com/):

1. Open **Identity > Applications > App registrations** and select **New
   registration**.
2. Give it a name such as `github-octocat-supply-deploy`.
3. Keep the default supported account type (**Accounts in this organizational
   directory only**) and select **Register**. No redirect URI is needed.
4. On the app's **Overview** page, record:
   - **Application (client) ID** — this becomes the GitHub secret
     `AZURE_CLIENT_ID`.
   - **Directory (tenant) ID** — this becomes `AZURE_TENANT_ID`.

Registering the application also creates its service principal (shown as an
**Enterprise application** in Entra). You will use the service principal's
object ID for `AZURE_CLIENT_OBJECT_ID` in step 3; that is a different ID from
the application/client ID.

## 2. Add the GitHub federated credential

On the app registration, open **Certificates & secrets > Federated
credentials** and select **Add credential**. Choose the **GitHub Actions
deploying Azure resources** scenario, then enter:

| Field | Value |
| --- | --- |
| Organization | `Phillips57` |
| Repository | `microhack-sdlc` |
| Entity type | **Branch** |
| Branch | `main` |
| Name | `github-main-deploy` |

Use the default issuer and audience:

```text
Issuer:   https://token.actions.githubusercontent.com
Audience: api://AzureADTokenExchange
Subject:  repo:Phillips57/microhack-sdlc:ref:refs/heads/main
```

The subject is case-sensitive and must match the workflow run's GitHub
repository and branch. This workflow does not use a GitHub Environment, so do
not create an environment-based subject. If you rename or transfer the
repository, change the federated credential to match. GitHub's immutable
subject-claim format may apply to repositories created or renamed/transferred
after July 15, 2026; if the subject above does not match the run, check the
`sub` claim format in GitHub's
[OIDC reference](https://docs.github.com/en/actions/reference/security/oidc#immutable-subject-claims)
and use the subject GitHub issues for this repository.

## 3. Grant Azure permissions

In the Azure portal, open the target **Subscription > Access control (IAM) >
Add role assignment**. Assign both roles below to the new service principal
(search for its app name under **User, group, or service principal**):

| Role | Scope | Why this workflow needs it |
| --- | --- | --- |
| **Contributor** | Target resource group | Deploys resources in the existing resource group. The Bicep template grants `AcrPush` on the registry for image publishing. |
| **User Access Administrator** | Target resource group | Lets Bicep grant `AcrPull` to the Container Apps identity and `AcrPush` to this GitHub service principal on the registry. |

The resource group must already exist; the workflow validates it and deploys
within that scope. `resource-group.bicep` is available for subscription-level
provisioning separately, but the workflow does not use it. These built-in roles
are broad within the resource group. For a production pipeline, use a custom
role with only the required actions. Do not assign **Owner** to the GitHub
identity merely to make deployment work.

Get the subscription ID from **Subscription > Overview**. Get the service
principal object ID from **Enterprise applications > All applications >
github-octocat-supply-deploy > Overview** (field: **Object ID**).

If you have Azure CLI access, you can check the values without creating a
client secret:

```bash
az account show --query id --output tsv
az account show --query tenantId --output tsv

# Supply the Application (client) ID from step 1:
az ad sp show --id '<APPLICATION_CLIENT_ID>' --query id --output tsv
```

The last command returns the service principal's **object ID** for
`AZURE_CLIENT_OBJECT_ID`.

## 4. Configure GitHub Actions secrets and variables

Open the
[repository's Actions secrets and variables settings](https://github.com/Phillips57/microhack-sdlc/settings/secrets/actions)
and select the **Secrets** or **Variables** tab as appropriate.

Create these **repository secrets**:

| Secret | Value |
| --- | --- |
| `AZURE_CLIENT_ID` | Application (client) ID from step 1 |
| `AZURE_TENANT_ID` | Directory (tenant) ID from step 1 |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID from step 3 |

Create these **repository variables**:

| Variable | Example / value |
| --- | --- |
| `AZURE_RESOURCE_GROUP` | `octocat-supply-rg` (choose a resource-group name) |
| `AZURE_LOCATION` | An Azure region supporting Container Apps, for example `eastus` |
| `AZURE_CLIENT_OBJECT_ID` | Service principal **Object ID** from step 3 |

Save IDs as text exactly as displayed. Do not add quotes or create an
`AZURE_CREDENTIALS` secret. The workflow does not use a client secret.

## 5. Run the workflow and verify

1. Ensure the workflow changes are on the repository's `main` branch.
2. Open **Actions > Build, test, and deploy to Azure > Run workflow** and select
   `main`, or push a commit to `main`.
3. The workflow runs tests, logs into Azure using OIDC, provisions the resource
   group and infrastructure with Bicep, builds and pushes the images, deploys
   the Container Apps, then checks the products endpoint and cart add/read
   flow.
4. Open the successful run's summary for the public frontend URL. The workflow
   fails early with a specific message if a required secret or variable is
   missing.

If Azure login reports that no matching federated identity record was found,
compare the credential's issuer, audience, and subject with the workflow run.
Check that the run is from `Phillips57/microhack-sdlc` on `main`, and that no
repository rename or transfer changed the subject.

## References

- [Microsoft: Authenticate to Azure from GitHub Actions by OIDC](https://learn.microsoft.com/en-us/azure/developer/github/connect-from-azure-openid-connect)
- [GitHub: Configuring OpenID Connect in Azure](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-azure)
