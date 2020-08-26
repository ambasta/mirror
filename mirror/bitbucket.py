import requests


class Client:
    BASE_URI = "https://api.bitbucket.org/2.0/"

    def __init__(self, username, password, organization=None):
        self.username = username
        self.password = password
        self.organization = organization
        self.repos = []

    def get_repositories(self, api_url=None):

        if api_url is None:
            api_url = f"{self.BASE_URI}repositories"

            if self.organization:
                api_url = f"{api_url}/{self.organization}"

        request = requests.get(api_url, auth=(self.username, self.password))
        response = request.json()
        self.repos += response.get("values", [])
        api_url = response.get("next", None)

        if api_url is not None:
            self.get_repositories(api_url)
