import argparse

import requests

from requests.auth import HTTPBasicAuth


def handle(args):
    pipeline_name = args.repository_full_name.replace("/", ".")
    organization = args.devops_organization
    project = args.devops_project

    auth = HTTPBasicAuth("", args.azure_devops_access_token)

    endpoint = f"https://dev.azure.com/{organization}/{project}/_apis/pipelines?api-version=7.0"
    body = {
        "folder": args.devops_folder,
        "name": pipeline_name,
        "configuration": {
            "path": args.yaml_path,
            "repository": {
                "fullName": args.repository_full_name,
                "type": "gitHub",
                "connection": {"id": args.connection_id},
            },
            "type": "yaml",
        },
    }
    headers = {"Accept": "application/json"}

    result = requests.post(endpoint, auth=auth, json=body, headers=headers)
    if result.status_code not in [200]:
        _raise_api_error(result)

    print(f"Pipeline {pipeline_name} created!")

    repository_name = args.repository_full_name.split("/")[1]
    for env in ["dev", "qa", "prd"]:
        env_name = f"{repository_name}-{env}"
        data = {"name": env_name}
        endpoint = f"https://dev.azure.com/{organization}/{project}/_apis/distributedtask/environments?api-version=7.0"
        result = requests.post(endpoint, auth=auth, json=data)
        if result.status_code not in [200]:
            _raise_api_error(result)
        print(f"Enviroment {env_name} created!")

    print("Done!")


def _raise_api_error(result):
    if result.status_code == 203:
        # When authentication fails, the API returns a 203 and HTML signin page
        error_message = "It looks like the Access Token is invalid or expired."
    else:
        error_message = result.json()["message"]
    raise Exception(f"Something went wrong! Message given status code {result.status_code}: {error_message}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--azure-devops-access-token", type=str, required=True, help="The access token to call Azure DevOps REST API"
    )
    parser.add_argument(
        "--repository-full-name", required=True, type=str, help="The target repository {organization}/{repository}"
    )
    parser.add_argument("--devops-organization", required=True, type=str, help="The Azure DevOps organization")
    parser.add_argument("--devops-project", required=True, type=str, help="The Azure DevOps project")
    parser.add_argument("--devops-folder", required=False, type=str, help="The folder at Azure DevOps")
    parser.add_argument(
        "--connection-id", required=True, type=str, help="The Id of the connection between Azure DevOps and Github"
    )
    parser.add_argument(
        "--yaml-path",
        required=False,
        type=str,
        help="The path of the pipeline yaml file",
        default="azure-pipelines.yaml",
    )
    args = parser.parse_args()

    handle(args)
