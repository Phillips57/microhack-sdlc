targetScope = 'subscription'

@description('Name of the application resource group.')
param resourceGroupName string

@description('Azure region for the resource group.')
param location string

resource resourceGroup 'Microsoft.Resources/resourceGroups@2022-09-01' = {
  name: resourceGroupName
  location: location
  tags: {
    project: 'octocat-supply'
    managedBy: 'bicep'
  }
}

output resourceGroupId string = resourceGroup.id
