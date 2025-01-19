import getopt, sys
import notion
import notion_filter
import argparse
import time

def printHelp():
    print("python3 gametracker.py")
    for i in range(0, len(helps)):
        print('\t-{}, --{}:\t {}'.format(options[i], long_options[i], helps[i]))

argumentList = sys.argv[1:]
options = "lvmtf:"
long_options = ["list-all", "verbose", "mode", "title", "filter"]
helps = [
    "Choose between all posibble matches",
    "Show updated values",
    "Choose exec mode:\n\t watch: look for new entries to update in database ending in '#'\n\t one: update database entry with title [--title]\n\t all: update all",
    "Title to find when using mode=one",
    "Filter options: <property_name>:<filter_action>:<property_value>"
]
actions = ["store_true", "store_true", "store", "store", "append"]
defaults = [False, False, "watch", "", []]
parser = argparse.ArgumentParser()

for i in range(0, len(helps)):
    parser.add_argument('-{}'.format(options[i]), '--{}'.format(long_options[i]), help = helps[i], action=actions[i], default=defaults[i])
    
args = parser.parse_args()

try:
    arguments, values = getopt.getopt(argumentList, options, long_options)
    LIST = args.list_all
    VERBOSE = args.verbose
    MODE = args.mode
    TITLE = args.title
    FILTERS = []

    if args.filter:
        for filter_str in args.filter:
            parts = filter_str.split(':')

            if len(parts) == 3:
                property_name, filter_action, property_value = parts
                filter = notion_filter.newFilter(property_name, filter_action, property_value)

                FILTERS.append(filter)
            else:
                print(f"Invalid filter format: {filter_str}. Use <property_type>:<property_name>:<filter_action>:<property_value>")

    if MODE=="watch":
        print('== WATCHING FOR TITLES ENDING IN #')
        FILTERS.append(notion_filter.newFilter("Game Title", "ends_with", "#"))
        notion_filter.generateFilterParams(FILTERS)
        while True:
            for i in range(5):  
                notion.processPages(notion_filter.generateFilterParams(FILTERS), verbose=VERBOSE, listAll=LIST)
                time.sleep(1)
            
            print("Listening...")
    elif MODE=="one":
        print('== TRYING TO UPDATE {} {} ==')
        FILTERS.append(notion_filter.newFilter("Game Title", "equals", TITLE))
        print(notion_filter.generateFilterParams(FILTERS))
        notion.processPages(notion_filter.generateFilterParams(FILTERS), verbose=VERBOSE, listAll=LIST)
    elif MODE=="all":
        print('== TRYING TO UPDATE ALL TITLES {} ==')
        print(notion_filter.generateFilterParams(FILTERS))
        notion.processPages(notion_filter.generateFilterParams(FILTERS), verbose=VERBOSE, listAll=LIST)
    else:
        printHelp()
    
except getopt.error as err:
    print (str(err))