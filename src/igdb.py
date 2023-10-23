import requests, re
from datetime import datetime
import igdb_platforms
import difflib
import os
from dotenv import load_dotenv
import hltb

load_dotenv()

id = os.getenv('IGDB_ID')
token = os.getenv('IGDB_TOKEN')

headers = {
    "Client-ID": id,
    "Authorization": "Bearer " + token,
    "Content-Type": "application/json",
}

def compareStr(a, b):
    # Convierte ambas cadenas a minúsculas
    a = a.lower()
    b = b.lower()
    
    # Elimina caracteres no deseados (no alfanuméricos ni espacios)
    regex = re.compile(r'[^\s\w]')
    a_cleaned = regex.sub('', a)
    b_cleaned = regex.sub('', b)
    
    # Compara las cadenas limpias
    return a_cleaned == b_cleaned

def strLengthDif(str1, str2):
    return abs(len(str1) - len(str2))

def findPlatform(platform):
    if platform in igdb_platforms.platforms:
        return igdb_platforms.platforms[platform]
    
    query = requests.post('https://api.igdb.com/v4/platforms', headers=headers, data=f'fields *; where id = {platform};').json()
    if(len(query) > 0):
        if "abbreviation" in query[0]:
            return query[0]["abbreviation"]
        return query[0]["name"]
    
    return ""

def searchGame(title, listAll=False, platformWanted="", verbose=False):
    data = f'search "{title}";  fields  id, artworks, name, first_release_date, cover, franchises, genres, platforms, involved_companies.developer, involved_companies.company, total_rating, screenshots ;'
    response = requests.post('https://api.igdb.com/v4/games', headers=headers, data=data).json()

    if len(response) == 0:
        return {}
    
    similars = response[:min(len(response), 10)]

    best_fit = None
    # filter by platform wanted
    if platformWanted:
        similars_filtered = [game for game in similars if len(difflib.get_close_matches(
            platformWanted,
            [findPlatform(platform) for platform in game["platforms"]] if "platforms" in game else [],
            n=1,cutoff=0.6)) > 0
        ]
        
        if len(similars_filtered)>0:
            similars = similars_filtered

    if not listAll:
        # get most close title
        best_fit = similars[0]
        title_matches = difflib.get_close_matches(title, [sim["name"] for sim in similars], n=1, cutoff=0)
        if len(title_matches) > 0:
            best_fit = [sim for sim in similars if sim["name"]==title_matches[0]][0]
    else:
        platforms = []

        if len(similars)>1:
            for i in range(len(similars)):
                dates = map(lambda game: datetime.utcfromtimestamp(game["first_release_date"]).strftime('%Y-%m-%d') if "first_release_date" in game else "", similars)
                platforms.extend([findPlatform(platform) for platform in similars[i]["platforms"]] if "platforms" in similars[i] else [])

            dates = list(dates)
           
            print('Multiple matches found for {} ({}). Choose what you prefer:'.format(title, len(similars)))
            for i in range(len(similars)):
                print('{}. {} ({}, {})'.format(i, similars[i]["name"], dates[i], platforms[i]))
            best_fit = similars[int(input("-> "))]
        else:
            best_fit = similars[0]

    response = best_fit
    date = datetime.utcfromtimestamp(response["first_release_date"]).strftime('%Y-%m-%d') if "first_release_date" in response else ""
    cover = requests.post('https://api.igdb.com/v4/covers', headers=headers, data=f'fields image_id; where id = {response["cover"]};').json() if "cover" in response else None
    coverID = cover[0]["image_id"] if cover!=None and len(cover)>0 else -1

    coverURL = f'https://images.igdb.com/igdb/image/upload/t_cover_big/{coverID}.png' if coverID != -1 else ""

    screenshotsIDs = [requests.post('https://api.igdb.com/v4/screenshots', headers=headers, data=f'fields image_id; where id = {shot};').json()[0]["image_id"] for shot in response["screenshots"]] if "screenshots" in response else []
    screenshotsURLs = [f"https://images.igdb.com/igdb/image/upload/t_1080p/{shot}.png" for shot in screenshotsIDs[:min(1, len(screenshotsIDs))]] if screenshotsIDs else []

    # artworksIDs = [requests.post('https://api.igdb.com/v4/artworks', headers=headers, data=f'fields image_id; where id = {shot};').json()[0]["image_id"] for shot in response["artworks"]] if "screenshots" in response else []

    franchises = [] if not "franchises" in response else [requests.post('https://api.igdb.com/v4/franchises', headers=headers, data=f'fields *; where id = {franchise};').json()[0]["name"] for franchise in response["franchises"]] if "franchises" in response else []
    genres = [requests.post('https://api.igdb.com/v4/genres', headers=headers, data=f'fields *; where id = {genre};').json()[0]["name"] for genre in response["genres"]] if "genres" in response else []

    platforms = [findPlatform(platform) for platform in response["platforms"]] if "platforms" in response else []
    # platformsAb = [platform["abbreviation"] for platform in platforms if "abbreviation" in platform]
    # if len(platformsAb)==0:
    #     platformsAb = platforms

    developerIDs = [company['company'] for company in response["involved_companies"] if company['developer']] if "involved_companies" in response else []
    developers = [requests.post('https://api.igdb.com/v4/companies', headers=headers, data=f'fields *; where id={dev};').json()[0]["name"] for dev in developerIDs] if developerIDs else []
    rating = round(response["total_rating"], 2) if "total_rating" in response else None
    cover = screenshotsURLs[0] if len(screenshotsURLs)>0 else ""
    title = response["name"] if "name" in response else title
    time = hltb.hltb(title)
    result = {
        'title': title, "rating": rating, "developers": developers, "launchDate": date, "coverURL": coverURL, "franchises": franchises, "genres": genres, "platforms": platforms, "icon": coverURL, "cover": cover, "hltb": time
    }

    return result


# print(searchGame("Super Mario Galaxy", platformWanted="wii", listAll=False))
