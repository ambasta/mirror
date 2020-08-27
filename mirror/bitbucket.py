import aiohttp
import asyncio


class Client:
    BASE_URI = "https://api.bitbucket.org/2.0/"

    def __init__(self, username, password, organization=None):
        self.username = username
        self.password = password
        self.organization = organization
        self.repos = []

    async def get_repositories(self, client, queue, api_url=None):

        if api_url is None:
            api_url = f"{self.BASE_URI}repositories"

            if self.organization:
                api_url = f"{api_url}/{self.organization}"
        print('Fetching Page')

        async with client.get(
            api_url, auth=aiohttp.BasicAuth(self.username, password=self.password)
        ) as response:
            assert response.status == 200
            data = await response.json()

            for repo in data.get("values", []):
                print('Pushing repo to queue')
                await queue.put(repo)
            api_url = data.get("next", None)

            if api_url is not None:
                await self.get_repositories(queue, client, api_url)
            else:
                await queue.put(None)
