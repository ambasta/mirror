import click
from .migrate import Migrant
from .wrapper import coroutine

@click.command()
@click.option("--github-token", help="Your Github Token", required=True)
@click.option(
    "--github-organization", help="The organization to import to instead of the user",
)
@click.option("--github-team", help="The organization team to give the repository to")
@click.option("--bitbucket-username", help="Your Bitbucket Username", required=True)
@click.option("--bitbucket-password", help="Your Bitbucket Password", required=True)
@click.option("--bitbucket-organization", help="Your Bitbucket Organization")
@click.option(
    "--repos-to-migrate",
    multiple=True,
    help="""
    Repositories you want to migrate. \n
    If not passed, the command will migrate all your repositories. \n
    You can pass this parameter as many times as needed \n
    e.g. --repos-to-migrate=REPO1 --repos-to-migrate=REPO2
    """,
)
@click.option("-v", "--verbose", count=True)
@coroutine
async def migrate(
    loop,
    github_token,
    github_organization,
    github_team,
    bitbucket_username,
    bitbucket_password,
    bitbucket_organization,
    repos_to_migrate,
    verbose,
):
    migrant = Migrant(
        loop,
        github_token,
        bitbucket_username,
        bitbucket_password,
        gh_org=github_organization,
        gh_team=github_team,
        bb_org=bitbucket_organization,
        repos=repos_to_migrate,
    )
    return await migrant.migrate()
