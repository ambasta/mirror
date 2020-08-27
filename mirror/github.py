import aiohttp
import asyncio
import logging

LOGGER = logging.getLogger(__name__)


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
        LOGGER.debug("Fetching page")

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
            LOGGER.info(f"Skipping duplicate repo {repo['name']}")
            return
        kwargs = {"name": repo["name"], "private": repo.get("is_private", True)}
        api_url = f"{self.BASE_URI}/user/repos"

        if self.organization:
            api_url = f"{self.BASE_URI}/orgs/{self.organization}/repos"
        LOGGER.debug(f"Creating repo {repo['name']}")

        async with aiohttp.ClientSession() as session:

            async with session.post(
                api_url, headers={"Authorization": f"token {self.token}"}, json=kwargs
            ) as response:

                if response.status != 201:
                    LOGGER.error(
                        f"Failed to create repo {repo['name']}. Response status {response.status} Data: {response.text}"
                    )
                return await response.json()

    async def import_repo(self, queue, username, password):
        LOGGER.info("Fetching existing repos")
        await self.setup()

        while True:
            LOGGER.debug("Setup complete. Awaiting repos to migrate")
            repo = await queue.get()

            if repo is None:
                LOGGER.info("Migration complete")
                break
            LOGGER.info(f"Migrating repo {repo['name']}")
            created = await self.create_repo(repo)
            LOGGER.debug(f"Repo {repo['name']} barebones created")

            if created:
                import_url = f"{self.BASE_URI}/repos/{created['full_name']}/import"
                params = {
                    "vcs": "git",
                    "vcs_url": repo["url"],
                    "vcs_username": username,
                    "vcs_password": password,
                }
                LOGGER.debug(f"Migrating to {created['full_name']}")

                async with aiohttp.ClientSession() as session:
                    async with session.put(
                        import_url,
                        json=params,
                        headers={"Authorization": f"token {self.token}"},
                    ) as response:
                        assert response.status == 201
                        LOGGER.debug(f"Migration task created {created['full_name']}")
            await asyncio.sleep(2)
