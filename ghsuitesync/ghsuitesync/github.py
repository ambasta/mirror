import asyncio
import aiohttp
import json

from gql import gql, Client, AIOHTTPTransport
from github import Github, UnknownObjectException


class Organization:
    __token = ""
    __organizaton = ""
    __url = "https://api.github.com/graphql"
    __base_uri = "https://api.github.com"

    def __init__(self):
        self.__map = {}
        self.__users = {}
        self.__invitations = {}
        self.__teams = {}
        self.__client = Github(self.__token)
        self.__client = self.__client.get_organization(self.__organizaton)
        self.__transport = AIOHTTPTransport(
            url=self.__url, headers={"Authorization": f"token {self.__token}"}
        )
        self.__setup_complete = False

    def __link_teams(self):
        """
        Convert team.parent from id/name to object
        """

        for team_id_or_name, team_data in self.__teams.items():

            if "parent" in team_data:
                parent = team_data["parent"]

                if parent is None:
                    del team_data["parent"]

                if isinstance(parent, int) or isinstance(parent, str):
                    team_data["parent"] = self.__teams[parent]

    async def __populate_teams(self, api_url=None):
        """
        Populate existing teams from github
        """
        data = []
        link = None

        if api_url is None:
            api_url = f"{self.__base_uri}/orgs/{self.__organizaton}/teams"

        async with aiohttp.ClientSession() as session:
            async with session.get(
                api_url, headers={"Authorization": f"token {self.__token}"}
            ) as response:
                assert response.status == 200
                data = await response.json()
                link = response.links

        for team in data:
            team_data = {
                "id": team["id"],
                "name": team["name"],
                "parent": team["parent"],
                "node": team["node_id"],
            }
            self.__teams[team["name"]] = team_data
            self.__teams[team["id"]] = team_data
        api_url = link.get("next", {}).get("url", None)

        if api_url is not None:
            await self.__populate_teams(api_url)

    async def __populate_members(self, after=None):
        """
        Populate existing members from github
        """
        results = None

        async with Client(
            transport=self.__transport, fetch_schema_from_transport=True
        ) as session:
            params = {"orgname": self.__organizaton}

            if after:
                params["after"] = after
            query = gql(
                """
query ($orgname: String!, $after: String) {
    organization(login: $orgname) {
        membersWithRole(first: 100, after: $after) {
            nodes {
                organizationVerifiedDomainEmails(login: $orgname)
            }
            pageInfo {
                endCursor
            }
        }
    }
}
                """
            )
            results = await session.execute(query, variable_values=params)
        # import ipdb
        # ipdb.set_trace()

        if results:
            members_with_role = results.get("organization", {}).get(
                "membersWithRole", {}
            )

            for user in members_with_role.get("nodes", []):

                for email in user["organizationVerifiedDomainEmails"]:
                    self.__users[email.lower()] = True

            after = members_with_role.get("pageInfo", {}).get("endCursor")

            if after:
                await self.__populate_members(after)

    async def __populate_invitees(self, api_url=None):
        """
        Populate existing invitations from github
        """
        data = []
        link = None

        if api_url is None:
            api_url = f"{self.__base_uri}/orgs/{self.__organizaton}/invitations"

        async with aiohttp.ClientSession() as session:
            async with session.get(
                api_url, headers={"Authorization": f"token {self.__token}"}
            ) as response:
                assert response.status == 200
                data = await response.json()
                link = response.links

        for invitation in data:
            invitee = {
                "email": invitation["email"].lower(),
                "id": invitation["id"],
            }
            self.__invitations[invitee["email"].lower()] = invitee
        api_url = link.get("next", {}).get("url", None)

        if api_url is not None:
            await self.__populate_invitees(api_url)

    async def setup(self):
        """
        Populate existing data from github
        """
        print("Populating members")
        await self.__populate_members()
        print(f"{len(self.__users)} members populated")
        print("Populating teams")
        await self.__populate_teams()
        print(f"{len(self.__teams)} teams populated")
        self.__link_teams()
        print("Populating invitations")
        await self.__populate_invitees()
        print(f"{len(self.__invitations)} invitations populated")
        self.__notify_duplicates()

    def __notify_duplicates(self):
        """
        Notify of emails that have duplicate invitations
        """
        duplicates = []

        for email, invitation in self.__invitations.items():

            if email in self.__users:
                duplicates.append(invitation)
        print("Here are the duplicate invitations: ", json.dumps(duplicates))
        print("Press any key to continue: ")

    async def __add_teams(self, teams):
        """
        Add a team hierarchy into github
        Returns the leaf team
        """

        if teams:
            team = teams[-1]

            if team in self.__teams:
                return self.__teams[team]
            parent = await self.__add_teams(teams[:-1])
            api_url = f"{self.__base_uri}/orgs/{self.__organizaton}/teams"
            kwargs = {"name": team, "privacy": "closed"}
            data = None

            if parent:
                kwargs["parent_team_id"] = parent["id"]

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    api_url,
                    headers={"Authorization": f"token {self.__token}"},
                    json=kwargs,
                ) as response:
                    assert response.status == 201
                    data = await response.json()
            team_data = {
                "id": data["id"],
                "name": team,
                "node": data["node_id"],
            }

            if parent:
                team_data["parent"] = parent
            self.__teams[team] = team_data
            self.__teams[team_data["id"]] = team_data

        return None

    async def __add_user(self, email, team=None):
        """
        Add a user to organization
        """
        api_url = f"{self.__base_uri}/orgs/{self.__organizaton}/invitations"
        kwargs = {
            "email": email.lower(),
        }
        data = {}

        if team:
            kwargs["team_ids"] = [team["id"]]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                api_url,
                headers={"Authorization": f"token {self.__token}"},
                json=kwargs,
            ) as response:
                assert response.status == 201
                data = await response.json()
        self.__invitations[email.lower()] = {
            "email": data["email"].lower(),
            "id": data["id"],
        }

    async def add_members(self, members):
        extras = []
        member_emails = [member["email"].lower() for member in members]

        for member in self.__users.keys():

            if member.lower() not in member_emails:
                extras.append(member)

        for member in self.__invitations.keys():

            if member.lower() not in member_emails:
                extras.append(member)
        print(f"Extras: {', '.join(extras)}")
        input("Press enter when extras are cleared: ")

        for member in members:

            team = await self.__add_teams(member["teams"])
            email = member["email"].lower()

            if email in self.__users:
                print(f"Member '{email}' already in organization")
            elif email in self.__invitations:
                print(f"Member '{email}' already invited")
            else:
                print(f"Adding new member '{email}': {member}")
                await self.__add_user(email.lower(), team)

    def show(self):
        print(
            f"Total {len(self.__users) + len(self.__invitations)} members: {len(self.__users)} active {len(self.__invitations)} invited"
        )

    def show_invitations(self):
        print(f"Invites: {', '.join(self.__invitations.keys())}")
