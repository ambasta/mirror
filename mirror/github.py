from github import Github
import aiohttp
import asyncio


class Client:
    BASE_URI = "https://api.github.com"

    def __init__(self, token, organization=None, team=None):
        self.token = token
        self.organization = organization
        self.team = team
        self.repos = []

    async def setup(self, client, api_url=None):

        if api_url is None:
            api_url = f"{self.BASE_URI}/user/repos"

            if self.organization:
                api_url = f"{self.BASE_URI}/orgs/{self.organization}/repos"

        headers = {"Authorization": f"token {self.token}"}

        async with client.get(api_url, headers=headers) as response:
            assert response.status == 200

            data = await response.json()

            for repo in data:
                self.repos.append(repo["name"])
            link = response.links
            api_url = link.get("next", {}).get("url", None)

            if api_url is not None:
                await self.setup(client, api_url)

    async def create_repo(self, client, repo):

        if repo["name"] in self.repos:
            return
        kwargs = {"name": repo["name"], "private": repo.get("is_private", True)}
        api_url = f"{self.BASE_URI}/user/repos"

        if self.organization:
            api_url = f"{self.BASE_URI}/orgs/{self.organization}/repos"

        async with client.post(
            api_url, headers={"Authorization": f"token {self.token}"}, json=kwargs
        ) as response:
            assert response.status == 201
            return await response.json()

    async def import_repo(self, client, queue, username, password):
        print('Setting up GH')
        await self.setup(client)

        while True:
            print('Awaiting repo information')
            repo = await queue.get()

            if repo is None:
                break
            print('Possibly creating repo')
            created = await self.create_repo(client, repo)

            if created:
                print(f"Migrating {created['full_name']}")
                import_url = f"{self.BASE_URI}/repos/{created['full_name']}/import"
                params = {
                    "vcs": "git",
                    "vcs_url": repo["url"],
                    "vcs_username": username,
                    "vcs_password": password,
                }

                async with client.put(
                    import_url,
                    json=params,
                    headers={"Authorization": f"token {self.token}"},
                ) as response:
                    assert response.status == 201
