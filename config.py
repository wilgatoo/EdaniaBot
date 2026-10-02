import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

DISCORD_CHANNEL_ID = int(
    os.getenv("DISCORD_CHANNEL_ID", "0")
)

DISCORD_ROLE_ID = int(
    os.getenv("DISCORD_ROLE_ID", "0")
)

CHECK_INTERVAL = int(
    os.getenv("CHECK_INTERVAL", "10")
)

GARMOTH_URL = (
    "https://garmoth.com/api/trpc/"
    "serverBuffs.getEdanaWeek"
)

MAX_USES = 10

DOMAINS = {
    "edana_aphrodon": {
        "name": "Aphrodon",
        "boss": "Agris"
    },
    "edana_hermesia": {
        "name": "Hermesia",
        "boss": "Markthanan"
    },
    "edana_magaia": {
        "name": "Magaia",
        "boss": "Elion"
    },
    "edana_aresion": {
        "name": "Aresion",
        "boss": "Aal"
    }
}