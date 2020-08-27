import aiohttp
import asyncio


class Client:
    BASE_URI = "https://api.bitbucket.org/2.0/"

    def __init__(self, username, password, organization=None):
        self.username = username
        self.password = password
        self.organization = organization
        self.repos = []

    async def get_repositories(self, queue, api_url=None):

        if api_url is None:
            api_url = f"{self.BASE_URI}repositories"

            if self.organization:
                api_url = f"{api_url}/{self.organization}"
        print('BB: Fetching Page')
        data = []

        async with aiohttp.ClientSession() as session:

            async with session.get(
                api_url, auth=aiohttp.BasicAuth(self.username, password=self.password)
            ) as response:
                assert response.status == 200
                print('BB: Got page, parsing data')
                data = await response.json()
                print('BB: Got data, processing repos')

        for repo in data.get("values", []):
            print('BB: Pushing repo to queue')
            await queue.put(repo)
        api_url = data.get("next", None)

        if api_url is not None:
            print('BB: Going for next page')
            await self.get_repositories(queue, api_url)
        else:
            await queue.put(None)
