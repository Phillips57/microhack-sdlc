@description('Azure region for the registry.')
param location string

@description('Globally unique registry name (alphanumeric, 5-50 characters).')
param registryName string

@description('Resource ID of the Container Apps pull identity.')
param pullIdentityId string

@description('Principal ID of the Container Apps pull identity.')
param pullPrincipalId string

@description('Principal ID of the GitHub Actions service principal.')
param githubActionsPrincipalId string = ''

@description('Tags applied to the registry.')
param tags object = {}

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: registryName
  location: location
  tags: tags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
  }
}

var acrPullRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
var acrPushRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8311e382-0749-4cb8-b61a-304f252e45ec')

resource pullAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, pullIdentityId, acrPullRoleId)
  scope: registry
  properties: {
    roleDefinitionId: acrPullRoleId
    principalId: pullPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource githubPushAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(githubActionsPrincipalId)) {
  name: guid(registry.id, githubActionsPrincipalId, acrPushRoleId)
  scope: registry
  properties: {
    roleDefinitionId: acrPushRoleId
    principalId: githubActionsPrincipalId
    principalType: 'ServicePrincipal'
  }
}

@description('The registry login server.')
output loginServer string = registry.properties.loginServer

@description('The registry resource ID.')
output registryId string = registry.id

@description('The registry name.')
output registryName string = registry.name
