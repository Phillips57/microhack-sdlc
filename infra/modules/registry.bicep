@description('Azure region for the registry.')
param location string

@description('Globally unique registry name (alphanumeric, 5-50 characters).')
param registryName string

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

@description('The registry login server.')
output loginServer string = registry.properties.loginServer

@description('The registry resource ID.')
output registryId string = registry.id

@description('The registry name.')
output registryName string = registry.name
