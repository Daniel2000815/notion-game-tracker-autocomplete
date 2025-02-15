"""
Main module. Parses the program arguments and calls the notion module with those.
"""

import sys
import time
import argparse

from typing import Callable, Dict

from notion_gametracker import notion
from notion_gametracker import notion_filter
from notion_gametracker.status import Status

# Diccionario para registrar acciones disponibles
actions: Dict[str, Dict] = {}

def register_action(name: str, handler, arg_name: str, arg_help: str, optional_args=None):
    """Registra una acción con su argumento principal y argumentos opcionales"""
    actions[name] = {
        "handler": handler,
        "arg_name": arg_name,
        "arg_help": arg_help,
        "optional_args": optional_args or []
    }

def watch(verbose=False, list_all=False, loop=False) -> Status:
    """ Continuously watches for games with titles ending in '#' """
    print('== WATCHING FOR TITLES ENDING IN # ==')
    filters = [notion_filter.create("Game Title", "ends_with", "#")]
    
    lastStatus = Status.UNTOUCHED
    
    try:
        while True:
            
            notion.update_pages(
                notion_filter.generate_params(filters),
                verbose=verbose,
                list_all=list_all
            )

            if not loop:
                return
            
            print("Listening...")
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nExiting watch mode...")

def create_game(title, status="Wishlist") -> Status:
    """ Creates a new game entry with the given status (default is Wishlist) """
    print(f'== TRYING TO CREATE {title} ==')

    status = notion.create_page(title, status)
    print(status)

    return status

def delete_game(identifier: str | int) -> tuple[Status]:
    print(f'== TRYING TO DELETE {identifier} ==')
    status = []
    filter = [notion_filter.create_from_name_or_id(identifier)]
    filter_params = notion_filter.generate_params(filter)
    for page in notion.search_pages(filter_params):
        s = page.delete()
        status.append(s)
        print(s)

    return status

def update_games(identifier: str | int, *, additional_filters: list = [], verbose=False, list_all=False):
    """ Updates a game by its IGDB ID or title. """
    print(f'== TRYING TO UPDATE GAME WITH ID/TITLE {identifier} ==')
        
    for page in notion.search_pages_by_name_id(identifier, additional_filters=additional_filters):
        page.process(verbose=verbose, list_all=list_all)


def update_all(verbose=False, list_all=False):
    """ Updates all games """
    print('== TRYING TO UPDATE ALL TITLES ==')
    notion.update_pages(
        notion_filter.generate_params([]),
        verbose=verbose,
        list_all=list_all
    )



def main():
    """ Parses command-line arguments and calls the appropriate function """
    common_args = [
        ("-l", "--list_all", "Choose between all possible matches", "store_true"),
        ("-v", "--verbose", "Verbose mode", "store_true"),
    ]

    # Registro de acciones
    register_action("create", create_game, "title", "Title of the game")
    register_action("delete", delete_game, "id|name", "ID (int) or name (str) of the game to delete")
    register_action("update", update_games, "id|name", "ID (int) or name (str) of the game to update or use '--all' to update all games")
    register_action("watch", watch, "loop", "Enable infinite pulling")

    # Configuración de argparse dinámicamente
    parser = argparse.ArgumentParser(description="Update games based on mode and options.")
    subparsers = parser.add_subparsers(dest="action", required=True)

    for action_name, action_info in actions.items():
        subparser = subparsers.add_parser(action_name, help=f"{action_name} a game")
        subparser.add_argument(action_info["arg_name"], help=action_info["arg_help"])

        # Agregar parámetros opcionales a update y watch
        if action_name in ['update', 'watch']:
            subparser.add_argument("-l", "--list-all", help="Choose between all possible matches", action="store_true")
            subparser.add_argument("-v", "--verbose", help="Verbose mode", action="store_true")
            subparser.add_argument("-f", "--filter", help="Filter options: <property_name>:<filter_action>:<property_value>", action="append")

    args = parser.parse_args()

    # Lógica para ejecutar la acción correspondiente
    if args.action in actions:
        action_func = actions[args.action]["handler"]
        action_arg = getattr(args, actions[args.action]["arg_name"])

        if args.action == "update":
            filters = []
            if args.filter:
                for filter_str in args.filter:
                    parts = filter_str.split(':')
                    if len(parts) == 3:
                        property_name, filter_action, property_value = parts
                        filters.append(notion_filter.create(property_name, filter_action, property_value))
                    else:
                        print(f"Invalid filter format: {filter_str}. Use <name>:<action>:<value>")

            # Llamar a update_game con título vacío y filtros
            update_games(action_arg, additional_filters=filters,list_all=args.list_all, verbose=args.verbose)

        # Si la acción es alguna otra (como create, delete, watch), se ejecuta normalmente
        else:
            action_func(action_arg)

if __name__ == "__main__":
    main()