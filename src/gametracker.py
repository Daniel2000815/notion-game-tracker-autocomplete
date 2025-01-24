"""
Main module. Parses the program arguments and calls the notion module with those.
"""

import sys
import time
import argparse

import notion
import notion_filter

parser = argparse.ArgumentParser(description="Update games based on mode and options.")

# Positional argument for mode
parser.add_argument(
    "mode",
    help="How games to update will be selected",
    choices=["create", "all", "title", "id", "watch"]
)

# Optional arguments
parser.add_argument(
    "-l", "--list-all",
    help="Choose between all possible matches",
    action="store_true"
)
parser.add_argument("-v", "--verbose", help="Verbose mode", action="store_true")
parser.add_argument(
    "-f", "--filter",
    help="Filter options: <property_name>:<filter_action>:<property_value>",
    action="append"
)

# Parse arguments
args, remaining_args = parser.parse_known_args()

LIST = args.list_all
VERBOSE = args.verbose
FILTERS = []

if args.filter:
    for filter_str in args.filter:
        parts = filter_str.split(':')

        if len(parts) == 3:
            property_name, filter_action, property_value = parts
            FILTERS.append(
                notion_filter.new_filter(property_name, filter_action, property_value)
            )
        else:
            print(f"Invalid filter format: {filter_str}. Use <name>:<action>:<value>")

try:
    if args.mode == "watch":
        print('== WATCHING FOR TITLES ENDING IN # ==')
        FILTERS.append(notion_filter.new_filter("Game Title", "ends_with", "#"))
        while True:
            for i in range(5):
                notion.update_pages(
                    notion_filter.generate_filter_params(FILTERS),
                    verbose=VERBOSE,
                    list_all=LIST
                )
                time.sleep(1)

            print("Listening...")

    if args.mode == "title":
        if not remaining_args:
            parser.error("The 'title' mode requires a title argument.")

        title = remaining_args[0]
        print(f'== TRYING TO UPDATE {title} ==')
        FILTERS.append(notion_filter.new_filter("Game Title", "equals", title))
        notion.update_pages(
            notion_filter.generate_filter_params(FILTERS),
            verbose=VERBOSE,
            list_all=LIST
        )
    elif args.mode == "create":
        if not remaining_args:
            parser.error("The 'create' mode requires a title argument.")

        title = remaining_args[0]
        print(f'== TRYING TO CREATE {title} ==')
        notion.create_page(title, "Wishlist")
    elif args.mode == "id":
        if not remaining_args:
            parser.error("The 'id' mode requires an ID argument.")
        game_id = remaining_args[0]
        print(f'== TRYING TO UPDATE GAME WITH ID {game_id} ==')
        FILTERS.append(notion_filter.new_filter("IGDB ID", "equals", game_id))
        notion.update_pages(
            notion_filter.generate_filter_params(FILTERS),
            verbose=VERBOSE,
            list_all=LIST
        )

    elif args.mode == "all":
        print('== TRYING TO UPDATE ALL TITLES ==')
        notion.update_pages(
            notion_filter.generate_filter_params(FILTERS),
            verbose=VERBOSE,
            list_all=LIST
        )

    else:
        parser.print_help()

except KeyboardInterrupt:
    print("\nExiting...")
    sys.exit(0)
