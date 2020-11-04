import asyncio
import os

from csv import DictReader

from ghsuitesync.github import Organization
from ghsuitesync.gsuite import Developers


def load_csv():
    """
    Load the org structure CSV
    """
    data = []

    if os.path.exists("data/listing.csv"):

        with open("data/listing.csv", "r") as handle:
            reader = DictReader(handle)
            data = [row for row in reader]
    return data


async def main():
    """
    Add members to gsuite, github as specified
    """
    data = load_csv()
    org = Organization()
    developers = Developers()
    developers.show()
    developers.insert_members([member["email"].lower() for member in data])
    developers.show()
    await org.setup()

    org.show()
    org.show_invitations()
    members = []

    for member in data:
        hierarchy = []

        for i in range(4):
            level = member[f"l{i + 1}"]

            if level:
                hierarchy.append(level)
        members.append({"email": member["email"].lower(), "teams": hierarchy})
    await org.add_members(members)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
