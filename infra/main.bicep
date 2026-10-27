targetScope = 'resourceGroup'

@description('Azure region for all resources.')
param location string = resourceGroup().location

@description('Short lowercase prefix for resource names.')
@minLength(2)
@maxLength(12)
param namePrefix string = 'octocat'

@description('Environment name used in resource names.')
@minLength(2)
@maxLength(8)
param environmentName string = 'dev'

@description('Container image reference for the Python API.')
param apiImage string

@description('Container image reference for the frontend.')
param frontendImage string

@description('Create the Container Apps after the registry and supporting resources exist.')
param deployApps bool = true

@description('Object ID of the GitHub Actions service principal. It receives AcrPush.')
param githubActionsPrincipalId string = ''

@minValue(1)
@maxValue(5)
param frontendMaxReplicas int = 3

var suffix = take(uniqueString(resourceGroup().id), 6)
var baseName = '${namePrefix}-${environmentName}'
var registryName = toLower('${namePrefix}${environmentName}${suffix}acr')
var storageBaseName = take('${namePrefix}${environmentName}', 14)
var storageAccountName = toLower('${storageBaseName}${suffix}sa')
var logAnalyticsName = '${baseName}-logs'
var environmentResourceName = '${baseName}-env'
var apiAppName = '${baseName}-api'
var frontendAppName = '${baseName}-frontend'
var fileShareName = 'appdata'
var commonTags = {
  project: 'octocat-supply'
  managedBy: 'bicep'
  environment: environmentName
}

module registry 'modules/registry.bicep' = {
  name: 'registry'
  params: {
    location: location
    registryName: registryName
    pullIdentityId: pullIdentity.id
    pullPrincipalId: pullIdentity.properties.principalId
    githubActionsPrincipalId: githubActionsPrincipalId
    tags: commonTags
  }
}

module logAnalytics 'modules/loganalytics.bicep' = {
  name: 'loganalytics'
  params: {
    location: location
    workspaceName: logAnalyticsName
    tags: commonTags
  }
}

module environment 'modules/containerapp-env.bicep' = {
  name: 'containerapp-env'
  params: {
    location: location
    environmentName: environmentResourceName
    logAnalyticsWorkspaceId: logAnalytics.outputs.workspaceId
    tags: commonTags
  }
}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  tags: commonTags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

resource fileService 'Microsoft.Storage/storageAccounts/fileServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
}

resource fileShare 'Microsoft.Storage/storageAccounts/fileServices/shares@2023-01-01' = {
  parent: fileService
  name: fileShareName
  properties: {
    shareQuota: 5
    enabledProtocols: 'SMB'
  }
}

resource environmentStorage 'Microsoft.App/managedEnvironments/storages@2024-03-01' = {
  name: '${environmentResourceName}/appdata'
  properties: {
    azureFile: {
      accountName: storageAccount.name
      accountKey: storageAccount.listKeys().keys[0].value
      shareName: fileShare.name
      accessMode: 'ReadWrite'
    }
  }
  dependsOn: [
    environment
  ]
}

resource pullIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${baseName}-pull'
  location: location
  tags: commonTags
}

module apiApp 'modules/containerapp.bicep' = if (deployApps) {
  name: 'api-app'
  params: {
    location: location
    appName: apiAppName
    environmentId: environment.outputs.environmentId
    image: apiImage
    targetPort: 3000
    externalIngress: false
    allowInsecure: true
    registryLoginServer: registry.outputs.loginServer
    registryIdentityId: pullIdentity.id
    minReplicas: 1
    maxReplicas: 1
    tags: commonTags
    env: [
      {
        name: 'PORT'
        value: '3000'
      }
      {
        name: 'DB_FILE'
        value: '/app/data/app.db'
      }
      {
        name: 'DB_ENABLE_WAL'
        value: 'false'
      }
    ]
    volumes: [
      {
        name: 'appdata'
        storageName: 'appdata'
        storageType: 'AzureFile'
      }
    ]
    volumeMounts: [
      {
        volumeName: 'appdata'
        mountPath: '/app/data'
      }
    ]
  }
  dependsOn: [
    environmentStorage
  ]
}

module frontendApp 'modules/containerapp.bicep' = if (deployApps) {
  name: 'frontend-app'
  params: {
    location: location
    appName: frontendAppName
    environmentId: environment.outputs.environmentId
    image: frontendImage
    targetPort: 80
    externalIngress: true
    registryLoginServer: registry.outputs.loginServer
    registryIdentityId: pullIdentity.id
    minReplicas: 1
    maxReplicas: frontendMaxReplicas
    tags: commonTags
    env: [
      {
        name: 'API_HOST'
        value: apiAppName
      }
      {
        name: 'API_PORT'
        value: '80'
      }
    ]
  }
  dependsOn: [
    apiApp
  ]
}

@description('Globally unique name of the Azure Container Registry.')
output acrName string = registry.outputs.registryName

@description('ACR login server for pushing images.')
output acrLoginServer string = registry.outputs.loginServer

@description('Public URL of the frontend app. Empty during the infrastructure bootstrap phase.')
output frontendUrl string = deployApps ? 'https://${frontendAppName}.${environment.outputs.defaultDomain}' : ''

@description('Private API app DNS name within the Container Apps environment.')
output apiHost string = apiAppName
