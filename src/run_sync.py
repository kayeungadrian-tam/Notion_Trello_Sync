import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
import requests
from tqdm import tqdm


class NotionHandler:
    def __init__(self, token):
        self.headers = {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }
        self.url = "https://api.notion.com/v1"

    def add_page_to_db(self, properties, database_id):
        data = {"parent": {"database_id": database_id}, "properties": properties}

        response = requests.post(f"{self.url}/pages", headers=self.headers, json=data)

        if response.status_code == 200:
            return response.json().get("id")
        else:
            print(response.status_code)
            print(response.json())

    def add_content_to_page(self, page_id: str, description: str):
        updated_body = [
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "text": {
                                "content": description,
                            }
                        }
                    ]
                },
            }
        ]

        payload = {
            "children": updated_body,
        }

        response = requests.patch(
            f"{self.url}/blocks/{page_id}/children", json=payload, headers=self.headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(response.status_code)
            print(response.json())


class TrelloHandler:
    def __init__(self, token: str, key: str):
        self.query = {
            "key": key,
            "token": token,
        }

    def get_cards(self, board_id: str):
        url = f"https://api.trello.com/1/boards/{board_id}/cards?customFieldItems=true"

        response = requests.request("GET", url, params=self.query)

        return response

    def get_lists(self, board_id: str):
        url = f"https://api.trello.com/1/boards/{board_id}/lists"

        response = requests.request("GET", url, params=self.query)

        return response


load_dotenv()


def create_id_map_from_list(json_list: list[dict], key: str):
    id_map = {}
    for data in json_list:
        id_key = data.get(key)
        data.pop(key)
        id_map[id_key] = data

    return id_map


def get_today_date():
    return datetime.now().strftime("%Y-%m-%d")


def main():
    today = get_today_date()

    trello_handler = TrelloHandler(os.getenv("TRELLO_TOKEN"), os.getenv("TRELLO_KEY"))
    cards = trello_handler.get_cards(os.getenv("TRELLO_BOARD_ID")).json()
    lists = trello_handler.get_lists(os.getenv("TRELLO_BOARD_ID")).json()
    list_map = create_id_map_from_list(lists, key="id")

    notion_handler = NotionHandler(os.getenv("NOTION_TOKEN"))

    for card in tqdm(cards[:10]):
        card_dict = {}

        id_list = card.get("idList")
        status = list_map.get(id_list).get("name")

        title = card.get("name")
        description = card.get("desc")
        url = card.get("shortUrl")
        due_date = card.get("due")
        start_date = card.get("start")

        if start_date is not None:
            start_date = start_date.split("T")[0]
        else:
            start_date = today

        if due_date is not None:
            due_date = due_date.split("T")[0]
        else:
            due_date = (datetime.today() + timedelta(days=2)).strftime("%Y-%m-%d")

        if due_date < start_date:
            start_date = due_date

        card_properties = {
            "Title": {"title": [{"text": {"content": title}}]},
            # "Description": {"rich_text": [{"text": {"content": description}}]},
            "Priority": {"select": {"name": "Mediun"}},
            "Due": {"date": {"start": start_date, "end": due_date}},
            "Status": {"status": {"name": status}},
            "URL": {"url": url},
        }

        card_id = notion_handler.add_page_to_db(
            card_properties, os.getenv("NOTION_DATABASE_ID")
        )

        notion_handler.add_content_to_page(card_id, description)


if __name__ == "__main__":
    main()
