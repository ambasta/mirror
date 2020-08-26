from github import Github
from github.GithubException import UnknownObjectException


class Client:
    BASE_URL = "https://api.github.com"

    def __init__(self, token, organization=None, team=None):
        self.github = Github(token)
        self.organization = organization
        self.team = team

    def create_repo(self, repo):
        repo_name = repo["name"]
        domain = self.github.get_user()
        team_id = None
        kwargs = {
            "private": repo.get("is_private", True),
        }

        if self.organization is not None:
            domain = self.github.get_organization(self.organization)

            if self.team is not None:
                for team in domain.get_teams():
                    if team.name.lower() == self.team.lower():
                        team_id = team.id
                        break
        try:
            if domain.get_repo(repo_name) is not None:
                return
        except UnknownObjectException:
            pass

        if team_id is not None:
            kwargs["team_id"] = team_id

        return domain.create_repo(repo_name, **kwargs)

    def import_repo(self, repo, username, password):
        _repo = self.create_repo(repo)

        if _repo is None:
            return

        _repo.create_source_import(
            vcs="git", vcs_url=repo["url"], vcs_username=username, vcs_password=password
        )

