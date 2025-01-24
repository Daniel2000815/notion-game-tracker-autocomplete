import json
import os
from typing import NamedTuple
import requests
from dotenv import load_dotenv
import igdb
from igdb import Game
from spinner import Spinner
from utils import remove_comas

load_dotenv()

token = os.getenv('NOTION_TOKEN')
databaseID = os.getenv('NOTION_DATABASE_ID')

headers = {
    "Authorization": "Bearer " + token,
    "Content-Type": "application/json",
    "Notion-Version": "2022-02-22"
}

to_notion_field = {
    'select':
        lambda value: {'select': {'name': value}}                           if value else None,
    'multi_select':
        lambda value: {'multi_select': [{'name': item} for item in value]}  if value else None,
    'number':
        lambda value: {'type': 'number', 'number': value}                   if value else None,
    'date':
        lambda value: {'date': {'start': value}}                            if value else None,
    'title':
        lambda value: {'title': [{'text': {'content': value}}]}             if value else None
}

from_notion_field = {
    'multi_select':
        lambda field: [item["name"] for item in field.get("multi_select", [])]
        if field else [],
    'select':
        lambda field: field["select"].get("name", "")
        if isinstance(field, dict) and field.get("select") else "",
    'number':
        lambda field: field.get("number", 0) if field else 0,
    'date':
        lambda field: field["date"].get("start", "")
        if isinstance(field, dict) and field.get("date") else "",
    'title':
        lambda field: field.get("title", [{}])[0].get("plain_text", "")
        if field.get("title") else ""
}

class NotionPage(NamedTuple):
    "Representation of a game page in Notion database"
    id: str = ""
    cover_url: str = ""
    icon_url: str = ""
    game: 'Game' = None
    anticipated: str = "Unknown"
    status: str = "Pending"
    url: str = ""
    json: dict = {}

    @classmethod
    def create(cls, **kwargs):
        """
        Create a NotionPage instance with default values for unspecified fields.
        """
        default_game = Game.create()        
        default_values = cls._field_defaults
        
        return cls(
            **{**default_values, "game": default_game, **kwargs}
        )
    
    @classmethod
    def from_dict(cls, data: dict) -> "NotionPage":
        "Create `NotionPage` instance from an actual notion page json"
        properties = data["properties"]

        game = Game(
            igdbId=from_notion_field["number"](properties.get("IGDB ID", {})),
            title=from_notion_field["title"] (properties.get("Game Title", {})),
            rating=from_notion_field["number"](properties.get("IGDB Rating", {})),
            developers=from_notion_field["multi_select"](properties.get("Developer", {})),
            launchDate=from_notion_field["date"](properties.get("Launch Date", {})),
            franchises=from_notion_field["multi_select"](properties.get("Franchise", {})),
            genres=from_notion_field["multi_select"](properties.get("Genre", {})),
            platforms=from_notion_field["multi_select"](properties.get("Platform", {})),
            icon_url=data.get("icon", {}).get("external", {}).get("url", "")
                if data.get("icon") else "",
            cover_url=data.get("cover", {}).get("external", {}).get("url", "")
                if data.get("cover") else "",
            time_to_beat=from_notion_field["number"](properties.get("HLTB", {})),
        )

        return cls(
            id=data.get("id", ""),
            cover_url=data.get("cover", {}).get("external", {}).get("url", "")
                if data.get("cover") else "",
            icon_url=data.get("icon", {}).get("external", {}).get("url", "")
                if data.get("icon") else "",
            game=game,
            anticipated=from_notion_field["select"](properties.get("Anticipated", {})),
            status=from_notion_field["select"](properties.get("Status", {})),
            url=data.get("url", ""),
            json=data
        )

    def needs_update(self):
        "Whether a page has any field that always requires updating"
        return (
            "#" in self.game.title
            or not self.game.developers
            or not self.game.launchDate
            or not self.game.genres
            or not self.game.rating
            or not self.game.time_to_beat
            or not self.icon_url
            or not self.cover_url
            or not self.game.igdbId
        )

    def to_dict(self) -> dict:
        "Convert `NotionPage` instance to json"
        # Extraer el objeto Game de NotionPage
        game = self.game
        notion_dict = {
            'parent': {
                "type": "database_id",
                "database_id": databaseID
            },
            'properties': {
                key: value
                for key, value in {
                    'IGDB ID': to_notion_field["number"](game.igdbId),
                    'Game Title':to_notion_field["title"](game.title),
                    'IGDB Rating': to_notion_field["number"](game.rating),
                    'Developer': to_notion_field["multi_select"](game.developers),
                    'Launch Date': to_notion_field["date"](game.launchDate),
                    'Franchise': to_notion_field["multi_select"](game.franchises),
                    'Genre': to_notion_field["multi_select"](game.genres),
                    'Platform': to_notion_field["multi_select"](game.platforms),
                    'HLTB': to_notion_field["number"](game.time_to_beat),
                    'Anticipated': to_notion_field["select"](self.anticipated),
                    'Status': to_notion_field["select"](self.status),
                }.items()
                if value is not None
            },
            'icon': {'external': {'url': self.icon_url}} if self.icon_url else None,
            'cover': {'external': {'url': self.cover_url}} if self.cover_url else None,
        }

        return notion_dict

    def update_to_notion(self, new_game: Game = None):
        "Push NotionPage to Notion"
        update_url = (f"https://api.notion.com/v1/pages/{self.id}" 
            if self.id
            else f"https://api.notion.com/v1/pages"
        )

        if new_game is not None:
            self = self._replace(
                game=new_game,
                cover_url=new_game.cover_url,
                icon_url=new_game.icon_url
            )

        data = json.dumps(self.to_dict())
        if self.id:
            response = requests.patch(update_url, headers=headers, data=data)
        else:
            response = requests.post(update_url, headers=headers, data=data)
        print(response.text)
        return [response.status_code, response.text]

    def search_in_igdb(self, verbose=False, list_all=False):
        "Search game in IGDB with the `NotionPage` name and push changes"
        name_splitted = self.game.title.split()
        is_new_game = False

        if "#" in name_splitted[-1]:
            title = " ".join(name_splitted[:-1])
            last_word =  self.game.title.split()[-1]
            platform_wanted = last_word[:-1] if len(last_word)>1 else ""
            is_new_game = True
        else:
            title = self.game.title.replace("#","")
            platform_wanted = ""

        spinner = Spinner()
        spinner.start(title)

        if not is_new_game and not self.needs_update():
            if verbose:
                spinner.stop("Already updated", "👍", "grey")
            return

        valid_id = self.game.igdbId is not None and self.game.igdbId > 0
        spinner.log(
            f'Searching in IGDB by {"name" if not valid_id else "id"}...',
            "🔍" if self.game.igdbId is None else "🎯"
        )
        igdb_game = igdb.search_game_by_title(
            title, list_all=list_all, platform_wanted=platform_wanted
        ) if not valid_id else igdb.search_game_by_id(self.game.igdbId)

        if not igdb_game:
            spinner.error("Not found in IGDB")
            return

        name_dif = abs(len(igdb_game.title) - len(title))
        if name_dif > 2:
            print(f'⚠️ Original name ({title}) and found name ({igdb_game.title}) differ by {name_dif} characters')

        return remove_comas(igdb_game)
    
    def process(self, verbose=False, list_all=False):
        spinner = Spinner()
        igdb_game = self.search_in_igdb(verbose, list_all)

        overwritted_fields = self.game.overwritten_fields(igdb_game)
        missed_fields = igdb_game.missing_fields()

        if not overwritted_fields:
            if missed_fields:
                spinner.log(f'Could not get missing fields: {missed_fields}', "🌵", 'grey')
                spinner.stop()
                return

            spinner.warn("this line shouldn't be reached")

        spinner.log("Updating Notion page...")
        code = self.update_to_notion(igdb_game)

        if overwritted_fields:
            if missed_fields and missed_fields!=["franchises"]:
                spinner.warn(f'Updated {list(overwritted_fields.keys())}, missing {missed_fields}')
            else:
                spinner.log(f'Updated successfully {list(overwritted_fields.keys())}', "✔️", 'green')

            spinner.stop()
            if verbose:
                for key, (value1, value2) in overwritted_fields.items():
                    print(f"\t{key}: {value1} -> {value2}")
                print("\n")

            spinner.resume("\n")
            return

        if not code[0]:
            spinner.error("Unknown error")
            return

        if code[0]!=200:
            spinner.error(f'Got error {code[1]} from Notion')
            return

        if verbose:
            print(igdb_game)


def update_pages(params, verbose=False, list_all=False):
    """Fetch pages from Notion database filtering by `params`,
    create `NotionPage` instance from it, and call `process` method
    from each one
    """
    read_url = f"https://api.notion.com/v1/databases/{databaseID}/query"
    pages = []

    while True:
        search_response = requests.request("POST", read_url, json=params, headers=headers)

        if not search_response.ok:
            raise Exception(
                f"Failed to fetch pages: {search_response.status_code} - {search_response.text}"
            )

        search_response_obj = search_response.json()
        pages = search_response_obj.get("results")

        for page in pages:
            NotionPage.from_dict(page).process(verbose=verbose, list_all=list_all)

        if not search_response_obj.get("has_more"):
            break

        params["start_cursor"] = search_response_obj.get("next_cursor")

def create_page(title, status="Catalog"):
    page = NotionPage(
        game=Game.create(title=title),
        status=status
    )

    print(page.json)
    page.update_to_notion()