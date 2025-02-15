from datetime import datetime, timezone
import os
from typing import NamedTuple, List
import difflib

from dotenv import load_dotenv
import requests
from notion_gametracker.spinner import Spinner
from notion_gametracker import hltb


class Game(NamedTuple):
    """
    Encapsulation of a game information. Includes methods to
    check missing fields and compare with other Games
    """
    igdbId: int = -1
    title: str = ""
    rating: int = 0
    developers: List[str] = []
    launchDate: str = ""
    franchises: List[str] = []
    genres: List[str] = []
    platforms: List[str] = []
    icon_url: str = ""
    cover_url: str = ""
    time_to_beat: float = 0.0

    @classmethod
    def create(cls, **kwargs):
        """
        Create a Game instance with default values for unspecified fields.
        """
        default_values = cls._field_defaults
        return cls(**{**default_values, **kwargs})

    def missing_fields(self) -> List[str]:
        """
        Return list of attributes with no assigned value
        """
        return [field for field in self._fields if not getattr(self, field)]  # pylint: disable=no-member

    def overwritten_fields(self, other: "Game") -> dict:
        """
        Return list of attributes differences between both games
        """
        return {
            field: (getattr(self, field), getattr(other, field))
            for field in self._fields  # pylint: disable=no-member
            if getattr(self, field) != getattr(other, field)
        }

    def to_json(self):
        return self._asdict()

load_dotenv()
IGDB_ID = os.getenv('IGDB_ID')
IGDB_TOKEN = os.getenv('IGDB_TOKEN')
IGDB_SECRET = os.getenv('IGDB_SECRET')

if not IGDB_ID or not IGDB_TOKEN or not IGDB_SECRET:
    raise ValueError("Missing IGDB credentials in environment variables.")

headers = {
    "Client-ID": IGDB_ID,
    "Authorization": "Bearer " + IGDB_TOKEN,
    "Content-Type": "application/json",
}

class IGDBError(Exception):
    """Base exception for IGDB-related errors."""
    pass

class TokenRenewalError(IGDBError):
    """Raised when token renewal fails."""
    pass

class RequestTimeoutError(IGDBError):
    """Raised when a request times out."""
    pass

def __data_from_query__(query, user_title="")->Game:
    """
    Create a Game instance given a query result from IGDB
    """
    date = (
        datetime.fromtimestamp(query.get("first_release_date", 0), timezone.utc).strftime('%Y-%m-%d')
        if "first_release_date" in query
        else ""
    )

    icon_url = (
        f'https://images.igdb.com/igdb/image/upload/t_cover_big/{query["cover"]["image_id"]}.png'
        if query.get("cover")
        else ""
    )

    screenshots_urls = ([ 
        f'https://images.igdb.com/igdb/image/upload/t_1080p/{shot["image_id"]}.png'
        for shot in query.get("screenshots", [])[:1]
    ])

    cover_url = screenshots_urls[0] if screenshots_urls else ""
    franchises = [fran["name"] for fran in query.get("franchises", [])]
    genres = [genre["name"] for genre in query.get("genres", [])]
    platforms = [platform["name"] for platform in query.get("platforms", [])]
    developers = ([ 
        dev["company"]["name"]
        for dev in query.get("involved_companies", [])
        if dev.get("developer")
    ])

    rating = round(query.get("total_rating", 0), 2) or None
    title = query.get("name", user_title)
    time_to_beat = hltb.hltb(title)
    igdb_id = query["id"]

    return Game(
        igdb_id, title, rating, developers, date, franchises,
        genres, platforms, icon_url, cover_url, time_to_beat
    )

def __update_env_variable__(file_path: str, variable_name: str, new_value: str):
    """
    Updates the value of a variable in a .env file.

    :param file_path: Path to the .env file.
    :param variable_name: Name of the variable to modify.
    :param new_value: New value for the variable.
    """
    try:
        # Read the file and save the lines
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # Modify the corresponding line
        with open(file_path, 'w', encoding='utf-8') as file:
            for line in lines:
                # Identify the variable to change
                if line.startswith(f"{variable_name}="):
                    # Update the value
                    file.write(f"{variable_name}={new_value}\n")
                else:
                    file.write(line)

    except FileNotFoundError:
        raise FileNotFoundError(f"File {file_path} doesn't exist.")
    except OSError as e:
        raise OSError(f"Error occurred: {e}")

def __renew_token__():
    """
    Renew IGDB token using IGDB_ID and IGDB_SECRET
    and save it in env file
    """
    base_url = 'https://id.twitch.tv/oauth2/token'
    params = (
        f'?client_id={IGDB_ID}'
        f'&client_secret={IGDB_SECRET}'
        f'&grant_type=client_credentials'
    )

    try:
        response = requests.post(
            base_url + params,
            timeout=10
        ).json()
    except requests.exceptions.Timeout:
        raise RequestTimeoutError("Token renewal request timed out.")

    if "access_token" not in response:
        raise TokenRenewalError("Failed to obtain access token.")

    __update_env_variable__('.env', 'IGDB_TOKEN', response["access_token"])

def make_igdb_request(search_clause: str) -> dict:
    """
    Makes a POST request to the IGDB API and returns the response.

    :param search_clause: Clause for filtering the search.
    :return: A dictionary containing the API response, or an
    empty dictionary in case of an error or timeout.
    """
    if not search_clause:
        raise ValueError("No search clause provided for IGDB request")

    fields = [
        "id", "artworks", "cover.image_id", "first_release_date",
        "franchises.name", "genres.name", "involved_companies.company.name",
        "involved_companies.developer", "name", "platforms.name",
        "total_rating", "screenshots.image_id", "genres.name"
    ]

    try:
        data = f'{search_clause}; fields {", ".join(fields)};'
        response = requests.post(
            'https://api.igdb.com/v4/games',
            headers=headers,
            data=data,
            timeout=10
        ).json()
    except requests.exceptions.Timeout:
        raise RequestTimeoutError("IGDB search request timeout")

    if "message" in response and "Authorization" in response["message"]:
        __renew_token__()
        return make_igdb_request(data)

    if len(response) == 0 or ("status" in response[0] and response[0]["status"]!=200) or "id" not in response[0]:
        raise ValueError("IGDB game not found")

    return response

def search_game_by_id(igdb_id: int) -> Game:
    """
    Return Game instance given the game ID in IGDB
    """
    
    response = make_igdb_request(f'where id={igdb_id}')
    return __data_from_query__(response[0])

def search_game_by_title(title, list_all=True, platform_wanted="")->Game:
    """
    Perform a search in IGDB with the given params and return game instance
    :param title: Game to search
    :type a: string
    :param list_all: Whether a list of possible matches should
    be shown or just use the first one
    :type list_all: bool
    :param platform_wanted: Filter searches by platform
    :type platform_wanted: string
    :return: Found game
    :rtype: Game
    """

    try:
        response = make_igdb_request(f'search "{title}"')
    except:
        return {}

    similars = [__data_from_query__(query, title) for query in response]
    best_fit = None

    # filter by platform wanted
    if platform_wanted:
        similars_filtered = [game for game in similars if len(difflib.get_close_matches(
            platform_wanted,
            game.platforms,
            n=1,cutoff=0.8)) > 0
        ]

        if len(similars_filtered)>0:
            similars = similars_filtered

    if not list_all:
        # get closest title
        best_fit = similars[0]
        title_matches = difflib.get_close_matches(
            title, [sim.title for sim in similars],
            n=1, cutoff=0.6
        )

        if len(title_matches) > 0:
            best_fit = [sim for sim in similars if sim.title==title_matches[0]][0]
    else:
        if len(similars)>1:
            spinner = Spinner()
            spinner.stop()
            print(
                f'Multiple matches found for {title} ({len(similars)}). '
                'Choose what you prefer:'
            )

            for i, g in enumerate(similars):
                print(f'{i}. {g.title} ({g.launchDate}, {g.platforms})')

            user_input = input("Enter option (Press enter to skip) -> ")
            spinner.resume(f'Selected option {user_input}')

            if not user_input:
                return {}

            try:
                user_input_id = int(user_input)
            except ValueError:
                user_input_id = 0

            if 0 <= user_input_id < len(similars):
                best_fit = similars[user_input_id]
            else:
                best_fit = similars[0]
        else:
            best_fit = similars[0]

    return best_fit

def list_games_by_title(title, platform_wanted="")->list[tuple[int, str, str, str]]:
    """
    Perform a search in IGDB with the given params and returns a list of possible matches
    :param title: Game to search
    :type a: string
    :param platform_wanted: Filter searches by platform
    :type platform_wanted: string
    :return: List of info about matching games
    :rtype: list[{id, title, launchdate, platforms}]
    """

    try:
        response = make_igdb_request(f'search "{title}"')
    except:
        return []
    similars = [__data_from_query__(query, title) for query in response]
    res = []

    if platform_wanted:
        similars_filtered = [game for game in similars if len(difflib.get_close_matches(
            platform_wanted,
            game.platforms,
            n=1,cutoff=0.6)) > 0
        ]

        if len(similars_filtered)>0:
            similars = similars_filtered

    for i, g in enumerate(similars):
        res.append((g.igdbId, g.title, g.launchDate, g.platforms))

    return res
