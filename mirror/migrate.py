import asyncio
from .bitbucket import Client as BitbucketClient
from .github import Client as GithubClient


class Migrant:
    def __init__(
        self,
        loop,
        gh_token,
        bb_user,
        bb_pass,
        gh_org=None,
        gh_team=None,
        bb_org=None,
        repos=None,
    ):
        self.loop = loop
        self.bb_user = bb_user
        self.bb_pass = bb_pass
        self.github = GithubClient(gh_token, organization=gh_org, team=gh_team)
        self.bitbucket = BitbucketClient(
            self.bb_user, self.bb_pass, organization=bb_org
        )
        self.repos = repos

    async def migrate(self):
        queue = asyncio.Queue(loop=self.loop)
        await asyncio.wait(
            [
                self.bitbucket.get_repositories(queue),
                self.github.import_repo(queue, self.bb_user, self.bb_pass),
            ]
        )
