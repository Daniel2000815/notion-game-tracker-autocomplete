import requests, json, igdb, time, re, os
from dotenv import load_dotenv
from igdb import Game
from typing import NamedTuple, List
from spinner import Spinner

load_dotenv()

token = os.getenv('NOTION_TOKEN')
databaseID = os.getenv('NOTION_DATABASE_ID')

headers = {
    "Authorization": "Bearer " + token,
    "Content-Type": "application/json",
    "Notion-Version": "2022-02-22"
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

def dict_to_notion_page(notion_page: dict) -> NotionPage:
    properties = notion_page["properties"]

    # Helper function to safely extract multi_select fields
    def extract_multi_select(field: dict) -> List[str]:
        return [item["name"] for item in field.get("multi_select", [])] if field else []
    
    def extract_select(field: dict) -> str:
        # Ensure the field is a dictionary and the "select" key exists
        if not isinstance(field, dict) or field.get("select") is None:
            return ""  # Return an empty string if not valid
        return field["select"].get("name", "")

    # Helper function to safely extract a number field
    def extract_number(field: dict) -> int:
        return field.get("number", 0) if field else 0

    # Helper function to safely extract a date field
    def extract_date(field: dict) -> str:
        if not isinstance(field, dict) or field.get("date") is None:
            return ""
        return field["date"].get("start", "")

    game = Game(
        igdbId=extract_number(properties.get("IGDB ID", {})),
        title=(properties.get("Game Title", {}).get("title", [{}])[0].get("plain_text", "") if properties.get("Game Title", {}).get("title") else ""),
        rating=extract_number(properties.get("IGDB Rating", {})),
        developers=extract_multi_select(properties.get("Developer", {})),
        launchDate=extract_date(properties.get("Launch Date", {})),
        franchises=extract_multi_select(properties.get("Franchise", {})),
        genres=extract_multi_select(properties.get("Genre", {})),
        platforms=extract_multi_select(properties.get("Platform", {})),
        iconURL=notion_page.get("icon", {}).get("external", {}).get("url", "") if notion_page.get("icon") else "",
        coverURL=notion_page.get("cover", {}).get("external", {}).get("url", "") if notion_page.get("cover") else "",
        timeToBeat=extract_number(properties.get("HLTB", {})),
    )

    return NotionPage(
        id=notion_page.get("id", ""),
        coverURL=notion_page.get("cover", {}).get("external", {}).get("url", "") if notion_page.get("cover") else "",
        iconURL=notion_page.get("icon", {}).get("external", {}).get("url", "") if notion_page.get("icon") else "",
        game=game,
        anticipated=extract_select(properties.get("Anticipated", {})),
        status=extract_select(properties.get("Status", {})),
        url=notion_page.get("url", ""),
        json=notion_page
    )

def notion_page_to_dict(notion_page: NotionPage) -> dict:
    def to_select(value: str) -> dict:
        return {'select': {'name': value}} if value else None
    def to_multi_select(value: list) -> dict:
        return {'multi_select': [{'name': item} for item in value]} if value else None

    def to_number(value: int) -> dict:
        return {'type': 'number', 'number': value} if value else None

    def to_date(value: str) -> dict:
        return {'date': {'start': value}} if value else None
    
    def to_title(value: str) -> dict:
        return {'title': [{'text': {'content': value}}]} if value else None
    

    # Extraer el objeto Game de NotionPage
    game = notion_page.game
    notion_dict = {
        'properties': {
            key: value
            for key, value in {
                'IGDB ID': to_number(game.igdbId),
                'Game Title':to_title(game.title),
                'IGDB Rating': to_number(game.rating),
                'Developer': to_multi_select(game.developers),
                'Launch Date': to_date(game.launchDate),
                'Franchise': to_multi_select(game.franchises),
                'Genre': to_multi_select(game.genres),
                'Platform': to_multi_select(game.platforms),
                'HLTB': to_number(game.timeToBeat),
                'Anticipated': to_select(notion_page.anticipated),
                'Status': to_select(notion_page.status),
            }.items()
            if value is not None  # Filtra los valores que no sean None
        },
        'icon': {'external': {'url': notion_page.iconURL}} if notion_page.iconURL else None,
        'cover': {'external': {'url': notion_page.coverURL}} if notion_page.coverURL else None,
    }

    return notion_dict

def removeComas(val):
    if isinstance(val, str):
        return val.replace(",", "")  # Reemplaza todas las comas por una cadena vacía
    elif isinstance(val, list):
        return [removeComas(item) for item in val]  # Recorre la lista y aplica la función a cada elemento
    elif isinstance(val, dict):
        return {key: removeComas(subvalor) for key, subvalor in val.items()}  # Recorre el diccionario y aplica la función a cada valor
    elif hasattr(val, "_fields"):  # Comprobamos si el objeto tiene atributos como un NamedTuple
        return val.__class__(**{field: removeComas(getattr(val, field)) for field in val._fields})  # Recursión para NamedTuple
    else:
        return val
 
def generateFilterParams(status="any", lastTitleCharacter="any", title="any", amount=100):
    params = {"page_size": amount}

    filters = []

    if status != "any":
        filters.append({
            "property": "Status",
            "select": {"equals": status}
        })

    if lastTitleCharacter != "any":
        filters.append({
            "property": "Game Title",
            "rich_text": {"ends_with": lastTitleCharacter}
        })

    if title != "any":
        filters.append({
            "property": "Game Title",
            "rich_text": {"equals": title}
        })

    # Añadir los filtros combinados si existen
    if filters:
        if len(filters) == 1:
            params["filter"] = filters[0]  # Un solo filtro no necesita lógica de "and"
        else:
            params["filter"] = {"and": filters}

    return params

def requestPages(params):
    page_count = 1
    readUrl = f"https://api.notion.com/v1/databases/{databaseID}/query"

    search_response = requests.request("POST", readUrl, json=params, headers=headers)
    if search_response.ok:
        search_response_obj = search_response.json()		
        pages = search_response_obj.get("results")

        while search_response_obj.get("has_more"):
            page_count += 1
            params["start_cursor"] = search_response_obj.get("next_cursor")
            search_response = requests.request("POST", readUrl, json=params, headers=headers)

            if search_response.ok:
                search_response_obj = search_response.json()
                pages.extend(search_response_obj.get("results"))

    return [dict_to_notion_page(page) for page in pages]

def needsUpdate(page: NotionPage):
    return (
        "#" in page.game.title
        or not page.game.developers
        or not page.game.launchDate
        or not page.game.genres
        or not page.game.rating
        or not page.game.timeToBeat
        or not page.iconURL
        or not page.coverURL
        or not page.game.igdbId
    )

def missingFields(game: Game) -> list:
    empty_fields = []
    
    for field in game._fields:
        value = getattr(game, field)
        # Verifica si el valor está vacío o es None
        if value == "" or value == [] or value is None:
            empty_fields.append(field)
    
    return empty_fields

def overwrittenFields(game1: Game, game2: Game) -> dict:
    differences = {}
    for field in game1._fields:
        value1 = getattr(game1, field)
        value2 = getattr(game2, field)
        if value1 != value2:
            differences[field] = (value1, value2)
    return differences

def updatePage(page:NotionPage, newGame: Game):
    updateUrl = f"https://api.notion.com/v1/pages/{page.id}"
    page = page._replace(game=newGame, coverURL=newGame.coverURL, iconURL=newGame.iconURL)
    
    data = json.dumps(notion_page_to_dict(page))
    response = requests.patch(updateUrl, headers=headers, data=data)
    return [response.status_code, response.text]

def processPage(notionPage:NotionPage, verbose=False, listAll=False):
    # print('Processing {}'.format(notionPage["properties"]["Game Title"]["title"][0]["plain_text"]))
    nameSplitted = notionPage.game.title.split()
    isNewGame = False

    if "#" in nameSplitted[-1]:
        title = " ".join(nameSplitted[:-1])
        lastWord =  notionPage.game.title.split()[-1]
        platformWanted = lastWord[:-1] if len(lastWord)>1 else ""
        isNewGame = True
    else:
        title = notionPage.game.title.replace("#","")
        platformWanted = ""

    spinner = Spinner()
    spinner.start(title)
    
    if not isNewGame and not needsUpdate(notionPage):
        if verbose:
            spinner.stop("Already updated", "👍", "grey")
        return
    
    spinner.log(f'Searching in IGDB by {"name" if notionPage.game.igdbId==None else "id"}...', "🔍" if notionPage.game.igdbId==None else "🎯")
    igdbGame = igdb.searchGameByTitle(title, listAll=listAll, platformWanted=platformWanted, verbose=verbose) if notionPage.game.igdbId==None else igdb.searchGameById(notionPage.game.igdbId)

    if not igdbGame:
        spinner.error("Not found in IGDB")
        return

   
    nameDif = abs(len(igdbGame.title) - len(title))
    if nameDif > 2:
        print('⚠️ Original name ({}) and found name ({}) differ by {} characters'.format(title, igdbGame.title, nameDif))

    igdbGame = removeComas(igdbGame)

    
    overwrittedFields = overwrittenFields(notionPage.game, igdbGame)
    missedFields = missingFields(igdbGame)

    if not overwrittedFields:
        if missedFields:
            spinner.log(f'Could not get missing fields: {missedFields}', "🌵", 'grey')
            spinner.stop()
            return
        else:
            spinner.warn("this line shouldn't be reached")
    
    spinner.log("Updating Notion page...")
    code = updatePage(notionPage, igdbGame)

    if overwrittedFields:
        if missedFields and missedFields!=["franchises"]:
            spinner.warn(f'Updated {overwrittedFields}, missing {missedFields}')
        else:
            spinner.log(f'Updated successfully {list(overwrittedFields.keys())}', "✔️", 'green')
        
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

def processPages(filterParams, verbose=False, listAll=False):
    pages = requestPages(filterParams)
    
    if not pages or len(pages)==0:
        print(f'⚠️ Notion returned 0 results for your filter')
        return
    
    for page,i in pages:
        print(i)
        processPage(page, verbose=verbose, listAll=listAll)
    
    print(f'{len(pages)} pages processed')