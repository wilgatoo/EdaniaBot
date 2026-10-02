import requests

from config import GARMOTH_URL, DOMAINS


class GarmothReader:

    def __init__(self):

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/154.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
            "Referer": "https://garmoth.com/",
        })

    def get_week_data(self):

        params = {
            "input": '{"region":"sa"}'
        }

        response = self.session.get(
            GARMOTH_URL,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        if "result" not in data:

            raise RuntimeError(
                "Garmoth no devolvió un resultado válido."
            )

        return data["result"]["data"]

    def read(self):

        week_data = self.get_week_data()

        calls = week_data.get(
            "calls",
            []
        )

        result = {}

        for buff_id, config in DOMAINS.items():

            domain_calls = [
                call
                for call in calls
                if call.get("buffId") == buff_id
            ]

            domain_calls.sort(
                key=lambda x: x.get(
                    "startedAt",
                    0
                )
            )

            uses = len(domain_calls)

            result[config["name"]] = {
                "name": config["name"],
                "boss": config["boss"],
                "buff_id": buff_id,
                "uses": uses,
                "calls": domain_calls
            }

        return {
            "since": week_data.get("since"),
            "until": week_data.get("until"),
            "domains": result
        }