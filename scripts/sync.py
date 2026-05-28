import json
import os

from dotenv import load_dotenv
from notion_client import Client


load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

notion = Client(auth=NOTION_TOKEN)


def load_mangas():

    with open("data/mangas.json", "r", encoding="utf-8") as file:
        return json.load(file)


def create_page(manga):

    notion.pages.create(
        parent={"database_id": NOTION_DATABASE_ID},

        properties={

            "Nome": {
                "title": [
                    {
                        "text": {
                            "content": manga["nome"]
                        }
                    }
                ]
            },

            "Alias": {
                "rich_text": [
                    {
                        "text": {
                            "content": ", ".join(manga["alias"])
                        }
                    }
                ]
            },

            "Status": {
                "select": {
                    "name": manga["status"]
                }
            },

            "Nota": {
                "select": {
                    "name": manga["nota"]
                }
            },

            "Último lido": {
                "number": manga["ultimo_lido"]
            },

            "Total caps": {
                "number": manga["total_caps"]
            },

            "Path": {
                "url": f"file://{manga['path']}"
            }
        }
    )


def sync():

    mangas = load_mangas()

    for manga in mangas:

        try:

            create_page(manga)

            print(f"[OK] {manga['nome']}")

        except Exception as error:

            print(f"[ERRO] {manga['nome']}")
            print(error)


if __name__ == "__main__":
    sync()