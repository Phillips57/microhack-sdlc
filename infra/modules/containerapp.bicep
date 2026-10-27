@description('Azure region for the app.')
param location string

@description('Name of the Container App.')
param appName string

@description('Resource ID of the Container Apps managed environment.')
param environmentId string

@description('Fully-qualified image reference.')
param image string

@description('Container listening port.')
param targetPort int

@description('Whether ingress is public or environment-internal.')
param externalIngress bool

@description('Allow HTTP ingress. Enable only for private, in-environment API traffic.')
param allowInsecure bool = false

@description('ACR login server.')
param registryLoginServer string

@description('User-assigned identity resource ID with AcrPull.')
param registryIdentityId string

@description('Container environment variables.')
param env array = []

@description('Volumes mounted in the container app.')
param volumes array = []

@description('Volume mounts for the container.')
param volumeMounts array = []

@description('Tags applied to the app.')
param tags object = {}

@minValue(0)
param minReplicas int = 1

@minValue(1)
param maxReplicas int = 3

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${registryIdentityId}': {}
    }
  }
  properties: {
    managedEnvironmentId: environmentId
    configuration: {
      ingress: {
        external: externalIngress
        targetPort: targetPort
        transport: 'http'
        allowInsecure: allowInsecure
        traffic: [
          {
            weight: 100
            latestRevision: true
          }
        ]
      }
      registries: [
        {
          server: registryLoginServer
          identity: registryIdentityId
        }
      ]
    }
    template: {
      containers: [
        {
          name: appName
          image: image
          resources: {
            cpu: json('0.5')
            memory: '1.0Gi'
          }
          env: env
          volumeMounts: volumeMounts
          probes: [
            {
              type: 'Startup'
              httpGet: {
                path: '/'
                port: targetPort
                scheme: 'HTTP'
              }
              initialDelaySeconds: 5
              periodSeconds: 10
              failureThreshold: 12
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/'
                port: targetPort
                scheme: 'HTTP'
              }
              periodSeconds: 10
              failureThreshold: 3
            }
            {
              type: 'Liveness'
              httpGet: {
                path: '/'
                port: targetPort
                scheme: 'HTTP'
              }
              periodSeconds: 30
              failureThreshold: 3
            }
          ]
        }
      ]
      volumes: volumes
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-concurrency'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

@description('The app DNS name within the managed environment.')
output appName string = containerApp.name
