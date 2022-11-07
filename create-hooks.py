import requests


def createServiceHooks(organization, pat, grafanaURL, apiToken, count=100):
    """
    :param organization: The name of the Azure DevOps organization
    :param pat: A personal access token contains your security credentials for Azure DevOps. A PAT identifies you,
    your accessible organizations, and scopes of access
    :param grafanaURL: Grafana endpoint
    :param apiToken: Grafana authentication
    :param count: Number of projects returned by API
    """
    url = f'https://dev.azure.com/{organization}/'
    # https://learn.microsoft.com/en-us/rest/api/azure/devops/core/projects/list?view=azure-devops-rest-6.0&tabs=HTTP
    uri = url + f"_apis/projects?api-version=6.0&$top={count}"
    headers = {'Content-type': 'application/json'}

    # https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate?view=azure-devops&tabs=Windows
    resp = requests.get(uri, headers=headers, auth=('', pat))

    if resp.ok:

        # List of all projects available for current PAT privilegies
        projects = resp.json()['value']

        for project in projects:

#             # Testing for 1 project
#             if project['name'] == 'Project.Name':

            projectId = project['id']
            projectName = project['name']

            # https://learn.microsoft.com/en-us/rest/api/azure/devops/release/definitions/list?view=azure-devops-rest-6.0&tabs=HTTP
            url = f'https://vsrm.dev.azure.com/{organization}/'
            uri = url + f"{projectName}/_apis/release/definitions?api-version=6.0"

            resp = requests.get(uri, headers=headers, auth=('', pat))
            # Definitions in project
            definitions = resp.json()['value']

            if resp.ok:
              
                print("Processing {}".format(projectName))
                
                for definition in definitions:
                  
                    # Definition must contain K8s what is connected to AKS
                    if str(definition['name']).endswith(' K8s'):
                      
                        releaseDefinitionId = definition['id']
                        uriReleaseDefinition = url + f"{projectName}/_apis/release/definitions/{releaseDefinitionId}?api-version=6.0"
                        resp = requests.get(uriReleaseDefinition, headers=headers, auth=('', pat))

                        if resp.ok:
                          
                            environments = resp.json()['environments']
                            
                            for environment in environments:
                              
                                if environment['name'] == 'prod':
                                  
                                    releaseEnvironmentId = environment['id']
                                    payload = {
                                        "consumerActionId": "addAnnotation",
                                        "consumerId": "grafana",
                                        "consumerInputs": {
                                            "url": grafanaURL,
                                            "apiToken": apiToken,
                                            "tags": "pipelines, itds, automation",
                                            "annotationDeploymentDurationWindow": 'true',
                                            "dashboardId": "28"
                                        },
                                        "eventType": "ms.vss-release.deployment-completed-event",
                                        "publisherId": "rm",
                                        "publisherInputs": {
                                            "releaseDefinitionId": releaseDefinitionId,
                                            "releaseEnvironmentId": releaseEnvironmentId,
                                            "releaseEnvironmentStatus": "",
                                            "projectId": projectId
                                        },
                                        "scope": 1
                                    }

                                    print("\tCreating Service Hook Subscription for: {}".format(definition['name']))
                                    # https://learn.microsoft.com/en-us/azure/devops/service-hooks/create-subscription?view=azure-devops
                                    uriHooksSubscriptions = url + "_apis/hooks/subscriptions?api-version=6.0"
                                    requests.post(uriHooksSubscriptions, json=payload, headers=headers,
                                                  auth=('', pat))


if __name__ == "__main__":
    createServiceHooks(organization='example.com',
                       pat='baz42sqkd87v87df87dv7ss8sfd7d77ka2f2csp37bil4ezzhdfj5chkq',
                       grafanaURL='https://metrics.example.com/',
                       apiToken='glsa_rau6ygh0887v87df87dv7ss8sfd7d77ka2fds897dfv987',
                       count=500)
