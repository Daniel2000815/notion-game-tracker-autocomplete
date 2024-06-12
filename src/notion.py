import requests, json, igdb, time, re, os
from dotenv import load_dotenv
load_dotenv()

token = os.getenv('NOTION_TOKEN')
databaseID = os.getenv('NOTION_DATABASE_ID')

headers = {
    "Authorization": "Bearer " + token,
    "Content-Type": "application/json",
    "Notion-Version": "2022-02-22"
}

def compareStr(a, b):
    regex = re.compile(r'[^\s\w]')
    return regex.sub('', a) == regex.sub('', b)

def eliminar_comas(valor):
    if isinstance(valor, str):
        return valor.replace(",", "")  # Reemplaza todas las comas por una cadena vacía
    elif isinstance(valor, list):
        return [eliminar_comas(item) for item in valor]  # Recorre la lista y aplica la función a cada elemento
    elif isinstance(valor, dict):
        return {key: eliminar_comas(subvalor) for key, subvalor in valor.items()}  # Recorre el diccionario y aplica la función a cada valor
    else:
        return valor
    
def getAllPages():
    page_count = 1
    params = {"page_size": 100} 
    readUrl = f"https://api.notion.com/v1/databases/{databaseID}/query"
    pages = []
    
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

    return pages
    
# Get all pages ended in #
def getAllPagesTagged():
    page_count = 1
    params = {
        "page_size": 100, 
        "filter": {
            "property": "Game Title",
            "rich_text": {
                "ends_with": "#"
            }
        }
    } 
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

    return pages

def getAllPagesStatus(status):
    page_count = 1
    params = {
        "page_size": 100, 
        "filter": {
            "property": "Status",
            "select": {
                "equals": status
            }
        }
    } 
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

    return pages


def needsUpdate(page):
    pageProperties = page["properties"]

    return "#" in pageProperties["Game Title"]["title"][0]["text"]["content"] or not pageProperties["Developer"]["multi_select"] or not pageProperties["Launch Date"]["date"] or not pageProperties["Genre"]["multi_select"] or not pageProperties["IGDB Rating"]["number"] or not pageProperties["HLTB"]["number"] or not page["icon"] or not page["cover"]

def missingFields(data):
    return [(clave) for clave, valor in data.items() if clave!="platforms" and (valor == "" or (isinstance(valor, list) and not valor))]

def getPageByTitle(title):
    readUrl = f"https://api.notion.com/v1/databases/{databaseID}/query"
    params = {
        "filter": {
            "property": "Game Title",
            "rich_text": {
                "equals": title
            }
        }
    }

    res = requests.request("POST", readUrl, headers=headers, json=params)
    data = res.json()

    with open('./full-properties.json', 'w', encoding='utf8') as f:
        json.dump(data, f, ensure_ascii=False, indent=5)

    return data

def updatePage(pageID, page, apiData, replace=False):
    pageProperties = page["properties"]
    newProperties = pageProperties
    newProperties.pop("Created time")
    
    updateAvailable = False
    if (replace or not pageProperties["Developer"]["multi_select"]) and apiData["developers"]:
        newProperties["Developer"]["multi_select"] = [{'name': dev} for dev in apiData["developers"]]
        updateAvailable = True
    if (replace or not pageProperties["Launch Date"]["date"]) and apiData["launchDate"]:
        newProperties["Launch Date"]["date"] = {"start": apiData["launchDate"]}
        updateAvailable = True
    # if replace or (not pageProperties["Platform"]["multi_select"] and apiData["platforms"]):
    # # if apiData["platforms"]:
    #     newProperties["Platform"]["multi_select"] = [{'name': plat} for plat in apiData["platforms"]]
    #     updateAvailable = True
    if (replace or not pageProperties["Franchise"]["multi_select"]) and len(apiData["franchises"])>0:
        newProperties["Franchise"]["multi_select"] = [{'name': fran} for fran in apiData["franchises"]]
        updateAvailable = True
    if (replace or not pageProperties["Genre"]["multi_select"]) and apiData["genres"]:
        newProperties["Genre"]["multi_select"] = [{'name': genre} for genre in apiData["genres"]]
        updateAvailable = True
    if (replace or pageProperties["IGDB Rating"]["number"]==None) and apiData["rating"]!=None:
        newProperties["IGDB Rating"]["number"] = apiData["rating"]
        updateAvailable = True
    if (replace or pageProperties["HLTB"]["number"]==None) and apiData["hltb"]!=None:
        newProperties["HLTB"]["number"] = apiData["hltb"]
        updateAvailable = True

    updateUrl = f"https://api.notion.com/v1/pages/{pageID}"
    updateData = {"properties": newProperties}

    if (replace or not page["icon"]) and apiData["icon"]:
        updateData["icon"] = {'type': 'external', 'external': {'url': apiData["icon"]}}
        updateAvailable = True
    if (replace or not page["cover"]) and apiData["cover"]:
        updateData["cover"] = {'type': 'external', 'external': {'url': apiData["cover"]}}
        updateAvailable = True
    
    if updateAvailable or "#" in pageProperties["Game Title"]["title"][0]["text"]["content"]:
        newProperties["Game Title"]["title"] =  [{"text": {"content": apiData["title"]}}]
        data = json.dumps(updateData)
        response = requests.request("PATCH", updateUrl, headers=headers, data=data)
        return [response.status_code, response.text]
    else:
        return [2000, ""]

def processPage(page, replace=False, verbose=False, showUntouched=False, listAll=False):
    # print('Processing {}'.format(page["properties"]["Game Title"]["title"][0]["plain_text"]))

    properties = page["properties"]
    id = page["id"]
    splitted = properties["Game Title"]["title"][0]["plain_text"].split()
    if "#" in splitted[-1]:
        title = " ".join(splitted[:-1])
        lastWord = properties["Game Title"]["title"][0]["plain_text"].split()[-1]
        platformWanted = lastWord[:-1] if len(lastWord)>1 else ""
    else:
        title = properties["Game Title"]["title"][0]["plain_text"].replace("#","")
        platformWanted = ""

    replace = replace or page["properties"]["Status"]["select"]["name"] == "Wishlist"

    if not replace and not needsUpdate(page):
        if showUntouched:
            print('👍 {} already updated'.format(title))
            if verbose:
                print(properties)
        return
    
    apiData = igdb.searchGame(title, listAll=listAll, platformWanted=platformWanted, verbose=verbose)
    if not apiData:
        print('❌ {} not found in IGDB'.format(title))
        return

    nameDif = abs(len(apiData["title"]) - len(title))
    if nameDif > 2:
        print('⚠️ Original name ({}) and found name ({}) differ by {} characters'.format(title, apiData["title"], nameDif))

    apiData = eliminar_comas(apiData)
    code = updatePage(id, page, apiData, replace=replace)
    missedFields = missingFields(apiData)

    if not code[0]:
        print('❌ Unkown error updating {}'.format(title))
        return
    elif code[0]==2000:
        if showUntouched:
            print('🌵 {} could not get missing fields: {}'.format(title, missedFields))
            if verbose:
                print(apiData)
        return
    elif code[0]!=200:
        print('❌ Error updating {}: {}'.format(title, code[1]))
        return
        
    
    if missedFields and missedFields!=["franchises"]:
        print('⚠️ {} -> {} updated with missing fields: {}'.format(title, apiData["title"], missedFields))
    else:
        print('✔️ {} -> {} updated successfully {}'.format(title, apiData["title"], "(with no franchise)" if "franchises" in missedFields else ""))
        

    if verbose:
        print(apiData)



def updateAll(replace=False, verbose=False, showUntouched=False, listAll=False):
    pages = getAllPagesStatus("Wishlist")
    count = 0
    for page in pages:
        processPage(page, replace=replace, verbose=verbose, listAll=listAll, showUntouched=showUntouched)
        count += 1

    print("Pages updated: ", count)

def updateTitle(title, replace=False, verbose=False, showUntouched=False, listAll=False):
    query = getPageByTitle(title)
   
    if not query or not "results" in query or not query["results"]:
        print('⚠️ {} not found in Notion database'.format(title))
        return

    processPage(query["results"][0], replace=replace, verbose=verbose, listAll=listAll, showUntouched=showUntouched)
        

def listen(replace=False, verbose=False, showUntouched=False, listAll=False):
    while True:
        for i in range(5):  
            pages = getAllPagesTagged()

            if pages:
                for page in pages:
                    processPage(page, replace=replace, verbose=verbose, listAll=listAll, showUntouched=showUntouched)

            time.sleep(1)
        
        print("Listening...")
