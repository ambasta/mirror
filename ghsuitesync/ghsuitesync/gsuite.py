import os
import pickle

from functools import partial

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


class Developers:
    __scopes = [
        "https://www.googleapis.com/auth/admin.directory.user",
        "https://www.googleapis.com/auth/admin.directory.group.member",
        "https://www.googleapis.com/auth/admin.directory.group",
    ]
    __group = "developers@delhivery.com"

    def __init__(self):
        self.__directory = None
        credentials = None

        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as handle:
                credentials = pickle.load(handle)

        if not credentials or not credentials.valid:

            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", self.__scopes
                )
                credentials = flow.run_local_server(port=0)

            with open("token.pickle", "wb") as handle:
                pickle.dump(credentials, handle)
        self.__directory = build("admin", "directory_v1", credentials=credentials)
        self.__members = []
        self.__members_new = []
        self.__populate_members()

    def __populate_members(self, token=None):

        if self.__directory is None:
            return
        kwargs = {"groupKey": self.__group}

        if token:
            kwargs["pageToken"] = token
        results = self.__directory.members().list(**kwargs).execute()

        for member in results["members"]:
            self.__members.append(member["email"].lower())

        if results.get("nextPageToken"):
            self.__populate_members(results["nextPageToken"])

    def __add_new_member(self, email, request_id, response, exception):

        if exception is None:
            self.__members_new.append(email)

    def insert_members(self, emails):

        if self.__directory is None:
            return
        batch = self.__directory.new_batch_http_request()
        extras = []

        for email in emails:

            if email not in self.__members:
                batch.add(
                    self.__directory.members().insert(
                        groupKey=self.__group, body={"email": email.lower()}
                    ),
                    callback=partial(self.__add_new_member, email),
                )
        batch.execute()

        for member in self.__members:

            if member not in emails:
                extras.append(member)
        print(f"Added {len(self.__members_new)} members. Extras: {', '.join(extras)}")
        self.__remove_extras(extras)

    def __remove_extras(self, extras):

        if self.__directory is None:
            return
        batch = self.__directory.new_batch_http_request()

        for email in extras:
            batch.add(
                self.__directory.members().delete(
                    groupKey=self.__group, memberKey=email
                )
            )
        batch.execute()

    def show(self):
        print(
            f"Group '{self.__group}' has {len(self.__members)} members, {len(self.__members_new)} new members added"
        )
