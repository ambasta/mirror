from .bitbucket import Client as BitbucketClient
from .github import Client as GithubClient


class Migrant:
    def __init__(
        self,
        gh_token,
        bb_user,
        bb_pass,
        gh_org=None,
        gh_team=None,
        bb_org=None,
        repos=None,
    ):
        self.bb_user = bb_user
        self.bb_pass = bb_pass
        self.github = GithubClient(gh_token, organization=gh_org, team=gh_team)
        self.bitbucket = BitbucketClient(
            self.bb_user, self.bb_pass, organization=bb_org
        )
        self.repos = repos

    def migrate(self):
        print("Fetching repos")
        self.bitbucket.get_repositories()
        print(f"Migrating {len(self.bitbucket.repos)} repos")

        for repo in self.bitbucket.repos:
            print(f"Importing {repo['name']}")
            repo["url"] = repo["links"]["clone"][0]["href"]

            if not self.repos or repo["name"] in self.repos:
                self.github.import_repo(repo, self.bb_user, self.bb_pass)
            else:
                print(f"Skipping {repo['name']}")
