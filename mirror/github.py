import aiohttp
import asyncio


class Client:
    BASE_URI = "https://api.github.com"

    def __init__(self, token, organization=None, team=None):
        self.token = token
        self.organization = organization
        self.team = team
        self.repos = []

    async def setup(self, api_url=None):

        if api_url is None:
            api_url = f"{self.BASE_URI}/user/repos"

            if self.organization:
                api_url = f"{self.BASE_URI}/orgs/{self.organization}/repos"

        headers = {"Authorization": f"token {self.token}"}
        data = []
        link = {}

        async with aiohttp.ClientSession() as session:

            async with session.get(api_url, headers=headers) as response:
                assert response.status == 200

                data = await response.json()
                link = response.links

        for repo in data:
            self.repos.append(repo["name"])
        api_url = link.get("next", {}).get("url", None)

        if api_url is not None:
            await self.setup(api_url)

    async def create_repo(self, repo):

        if repo["name"] in self.repos:
            return
        kwargs = {"name": repo["name"], "private": repo.get("is_private", True)}
        api_url = f"{self.BASE_URI}/user/repos"

        if self.organization:
            api_url = f"{self.BASE_URI}/orgs/{self.organization}/repos"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                api_url, headers={"Authorization": f"token {self.token}"}, json=kwargs
            ) as response:
                assert response.status == 201
                return await response.json()

    async def import_repo(self, queue, username, password):
        print("GH: Setting up GH")
        await self.setup()

        while True:
            print("GH: Awaiting repo information")
            repo = await queue.get()

            if repo is None:
                break
            print("GH: Possibly creating repo")
            created = await self.create_repo(repo)

            if created:
                print(f"GH: Migrating {created['full_name']}")
                import_url = f"{self.BASE_URI}/repos/{created['full_name']}/import"
                params = {
                    "vcs": "git",
                    "vcs_url": repo["url"],
                    "vcs_username": username,
                    "vcs_password": password,
                }

                async with aiohttp.ClientSession() as session:
                    async with session.put(
                        import_url,
                        json=params,
                        headers={"Authorization": f"token {self.token}"},
                    ) as response:
                        assert response.status == 201
            await asyncio.sleep(2)
