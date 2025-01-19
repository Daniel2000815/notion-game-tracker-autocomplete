import requests, json, igdb, time, re, os
from dotenv import load_dotenv
from igdb import Game
from typing import NamedTuple, List
from spinner import Spinner
from utils import removeComas

load_dotenv()

token = os.getenv('NOTION_TOKEN')
databaseID = os.getenv('NOTION_DATABASE_ID')

headers = {
    "Authorization": "Bearer " + token,
    "Content-Type": "application/json",
    "Notion-Version": "2022-02-22"
}

to_notion_field = {
    'select':           lambda value: {'select': {'name': value}}                           if value else None,
    'multi_select':     lambda value: {'multi_select': [{'name': item} for item in value]}  if value else None,
    'number':           lambda value: {'type': 'number', 'number': value}                   if value else None,
    'date':             lambda value: {'date': {'start': value}}                            if value else None,
    'title':            lambda value: {'title': [{'text': {'content': value}}]}             if value else None
}

from_notion_field = {
    'multi_select': lambda field: [item["name"] for item in field.get("multi_select", [])] if field else [],
    'select':       lambda field: field["select"].get("name", "") if isinstance(field, dict) and field.get("select") else "",
    'number':       lambda field: field.get("number", 0) if field else 0,
    'date':         lambda field: field["date"].get("start", "") if isinstance(field, dict) and field.get("date") else "",
    'title':        lambda field: field.get("title", [{}])[0].get("plain_text", "") if field.get("title") else ""
}

class NotionPage(NamedTuple):
    id: str
    coverURL: str
    iconURL: str
    game: Game
    anticipated: str
    status: str
    url: str
    json: dict

    @classmethod
    def from_dict(cls, data: dict) -> "NotionPage":
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
            iconURL=data.get("icon", {}).get("external", {}).get("url", "") if data.get("icon") else "",
            coverURL=data.get("cover", {}).get("external", {}).get("url", "") if data.get("cover") else "",
            timeToBeat=from_notion_field["number"](properties.get("HLTB", {})),
        )

        return cls(
            id=data.get("id", ""),
            coverURL=data.get("cover", {}).get("external", {}).get("url", "") if data.get("cover") else "",
            iconURL=data.get("icon", {}).get("external", {}).get("url", "") if data.get("icon") else "",
            game=game,
            anticipated=from_notion_field["select"](properties.get("Anticipated", {})),
            status=from_notion_field["select"](properties.get("Status", {})),
            url=data.get("url", ""),
            json=data
        )
    
    def needsUpdate(self):
        return (
            "#" in self.game.title
            or not self.game.developers
            or not self.game.launchDate
            or not self.game.genres
            or not self.game.rating
            or not self.game.timeToBeat
            or not self.iconURL
            or not self.coverURL
            or not self.game.igdbId
        )
    
    def to_dict(self) -> dict:
        # Extraer el objeto Game de NotionPage
        game = self.game
        notion_dict = {
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
                    'HLTB': to_notion_field["number"](game.timeToBeat),
                    'Anticipated': to_notion_field["select"](self.anticipated),
                    'Status': to_notion_field["select"](self.status),
                }.items()
                if value is not None 
            },
            'icon': {'external': {'url': self.iconURL}} if self.iconURL else None,
            'cover': {'external': {'url': self.coverURL}} if self.coverURL else None,
        }

        return notion_dict
    
    def update(self, newGame: Game):
        updateUrl = f"https://api.notion.com/v1/pages/{self.id}"
        self = self._replace(game=newGame, coverURL=newGame.coverURL, iconURL=newGame.iconURL)
        
        data = json.dumps(self.to_dict())
        response = requests.patch(updateUrl, headers=headers, data=data)
        return [response.status_code, response.text]
    
    def process(self, verbose=False, listAll=False):
        # print('Processing {}'.format(notionPage["properties"]["Game Title"]["title"][0]["plain_text"]))
        nameSplitted = self.game.title.split()
        isNewGame = False

        if "#" in nameSplitted[-1]:
            title = " ".join(nameSplitted[:-1])
            lastWord =  self.game.title.split()[-1]
            platformWanted = lastWord[:-1] if len(lastWord)>1 else ""
            isNewGame = True
        else:
            title = self.game.title.replace("#","")
            platformWanted = ""

        spinner = Spinner()
        spinner.start(title)
        
        if not isNewGame and not self.needsUpdate():
            if verbose:
                spinner.stop("Already updated", "👍", "grey")
            return
        
        spinner.log(f'Searching in IGDB by {"name" if self.game.igdbId==None else "id"}...', "🔍" if self.game.igdbId==None else "🎯")
        igdbGame = igdb.searchGameByTitle(title, listAll=listAll, platformWanted=platformWanted, verbose=verbose) if self.game.igdbId==None else igdb.searchGameById(self.game.igdbId)

        if not igdbGame:
            spinner.error("Not found in IGDB")
            return

    
        nameDif = abs(len(igdbGame.title) - len(title))
        if nameDif > 2:
            print('⚠️ Original name ({}) and found name ({}) differ by {} characters'.format(title, igdbGame.title, nameDif))

        igdbGame = removeComas(igdbGame)

        
        overwrittedFields = self.game.overwrittenFields(igdbGame)
        missedFields = igdbGame.missingFields()

        if not overwrittedFields:
            if missedFields:
                spinner.log(f'Could not get missing fields: {missedFields}', "🌵", 'grey')
                spinner.stop()
                return
            else:
                spinner.warn("this line shouldn't be reached")
        
        spinner.log("Updating Notion page...")
        code = self.update(igdbGame)

        if overwrittedFields:
            if any(p in ["IGDB_ID", "Game Title"] for p in overwrittedFields):
                spinner.warn(f'Overwritten: {list(overwrittedFields.keys()) if not verbose else overwrittedFields}, missing {missedFields}')

            elif missedFields and missedFields!=["franchises"]:
                spinner.warn(f'Updated {list(overwrittedFields.keys()) if not verbose else overwrittedFields}, missing {missedFields}')
            else:
                spinner.log(f'Updated successfully {list(overwrittedFields.keys()) if not verbose else overwrittedFields}', "✔️", 'green')
            
            spinner.stop()
            return

        if not code[0]:
            spinner.error("Unknown error")
            return
        
        if code[0]!=200:
            spinner.error(f'Got error {code[1]} from Notion')
            return
            
        if verbose:
            print(igdbGame)


def processPages(params, verbose=False, listAll=False):
    readUrl = f"https://api.notion.com/v1/databases/{databaseID}/query"
    pages = []

    while True:
        search_response = requests.request("POST", readUrl, json=params, headers=headers)

        if not search_response.ok:
            raise Exception(f"Failed to fetch pages: {search_response.status_code} - {search_response.text}")
        
        search_response_obj = search_response.json()		
        pages = search_response_obj.get("results")

        for page in pages:
            NotionPage.from_dict(page).process(verbose=verbose, listAll=listAll)

        if not search_response_obj.get("has_more"):
            break

        params["start_cursor"] = search_response_obj.get("next_cursor")