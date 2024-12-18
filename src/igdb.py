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

def dataFromQuery(query, userTitle):
    date = datetime.utcfromtimestamp(query["first_release_date"]).strftime('%Y-%m-%d') if "first_release_date" in query else ""
    iconURL = f'https://images.igdb.com/igdb/image/upload/t_cover_big/{query["cover"]["image_id"]}.png' if "cover" in query else ""
    screenshotsURLs = [f'https://images.igdb.com/igdb/image/upload/t_1080p/{shotID["image_id"]}.png' for shotID in query["screenshots"][:min(1, len(query["screenshots"]))]] if "screenshots" in query else []
    coverURL = screenshotsURLs[0] if len(screenshotsURLs)>0 else ""
    franchises = [fran["name"] for fran in query["franchises"]]  if "franchises" in query else [] 
    genres = [genre["name"] for genre in query["genres"]] if "genres" in query else []
    platforms = [platform["name"] for platform in query["platforms"]] if "platforms" in query else []
    developers = [dev["company"]["name"] for dev in query["involved_companies"] if dev["developer"]] if "involved_companies" in query else []
    rating = round(query["total_rating"], 2) if "total_rating" in query else None
    title = query["name"] if "name" in query else userTitle
    time = hltb.hltb(title)

    result = {
        'title': title, "rating": rating, "developers": developers, "launchDate": date, "franchises": franchises, "genres": genres, "platforms": platforms, "icon": iconURL, "cover": coverURL, "hltb": time
    }

    return result

def update_env_variable(file_path, variable_name, new_value):
    """
    Actualiza el valor de una variable en un archivo .env.
    
    :param file_path: Ruta del archivo .env.
    :param variable_name: Nombre de la variable a modificar.
    :param new_value: Nuevo valor para la variable.
    """
    try:
        # Leer el archivo y guardar las líneas
        with open(file_path, 'r') as file:
            lines = file.readlines()
        
        # Modificar la línea correspondiente
        with open(file_path, 'w') as file:
            for line in lines:
                # Identificar la variable a cambiar
                if line.startswith(f"{variable_name}="):
                    # Actualizar el valor
                    file.write(f"{variable_name}={new_value}\n")
                else:
                    file.write(line)
        print(f"Variable '{variable_name}' actualizada con éxito.")
    except FileNotFoundError:
        print(f"El archivo {file_path} no existe.")
    except Exception as e:
        print(f"Ocurrió un error: {e}")


def renewToken() -> bool:
    response = requests.post(f'https://id.twitch.tv/oauth2/token?client_id={os.getenv("IGDB_ID")}&client_secret={os.getenv("IGDB_SECRET")}&grant_type=client_credentials').json()

    print(response)
    if "access_token" in response:
        update_env_variable('.env', 'IGDB_TOKEN', response["access_token"])
        token = response["access_token"]
        return True

    return False

def searchGame(title, listAll=False, platformWanted="", verbose=False):
    data = f'search "{title}";  fields id, artworks, cover.image_id, first_release_date, franchises.name, genres.name, involved_companies.company.name, involved_companies.developer, name, platforms.name, total_rating, screenshots.image_id, genres.name;'
    response = requests.post('https://api.igdb.com/v4/games', headers=headers, data=data).json()
       
    if "message" in response and "Authorization" in response["message"]:
        ok = renewToken()

        if ok:
            print("IGDB token updated. Retrying...")
            return searchGame(title, listAll, platformWanted, verbose)
        else:
            print("Error updating IGDB token.")
            exit(1)

    if len(response) == 0 or not response[0]["id"]:
        return {}
    
    similars = [dataFromQuery(query, title) for query in response]

    best_fit = None
    # filter by platform wanted
    if platformWanted:
        similars_filtered = [game for game in similars if len(difflib.get_close_matches(
            platformWanted,
            game["platforms"],
            n=1,cutoff=0.6)) > 0
        ]
        
        if len(similars_filtered)>0:
            similars = similars_filtered
       
    if not listAll:
        # get most close title
        best_fit = similars[0]
        title_matches = difflib.get_close_matches(title, [sim["title"] for sim in similars], n=1, cutoff=0)
        if len(title_matches) > 0:
            best_fit = [sim for sim in similars if sim["title"]==title_matches[0]][0]
    else:
        platforms = []

        if len(similars)>1:
            print('Multiple matches found for {} ({}). Choose what you prefer:'.format(title, len(similars)))
            for i in range(len(similars)):
                print('{}. {} ({}, {})'.format(i, similars[i]["title"],  similars[i]["launchDate"],  similars[i]["platforms"]))
            
            user_input = input("Enter option (Press enter to skip) -> ")
            if not user_input:
                return None

            try:
                user_input_id = int(user_input)
            except ValueError:
                user_input_id = 0
            
            if user_input_id>=0 and user_input_id<len(similars):
                best_fit = similars[user_input_id]
            else:
                best_fit = similars[0]
        else:
            best_fit = similars[0]

    return best_fit

#print(searchGame("Super Mario Galaxy", platformWanted="wii", listAll=False))
