import getopt, sys
import notion
import argparse


def printHelp():
    print("python3 gametracker.py")
    for i in range(0, len(helps)):
        print('\t-{}, --{}:\t {}'.format(options[i], long_options[i], helps[i]))

argumentList = sys.argv[1:]
options = "lrsvmt:"
long_options = ["list-all",  "replace", "show-untouched", "verbose", "mode", "title" ]
helps = [
    "Choose between all posibble matches",
    "Replace existing data for existing fields",
    "Also print message for entries that are not going to be updated",
    "Show updated values",
    "Choose exec mode:\n\t watch: look for new entries to update in database ending in '#'\n\t one: update database entry with title [--title]\n\t all: update all",
    "Title to find when using mode=one"
]
actions = ["store_true", "store_true", "store_true", "store_true", "store", "store"]
defaults = [True, False, True, False, "watch", ""]
parser = argparse.ArgumentParser()

for i in range(0, len(helps)):
    parser.add_argument('-{}'.format(options[i]), '--{}'.format(long_options[i]), help = helps[i], action=actions[i], default=defaults[i])
    
args = parser.parse_args()
print(args)
try:
    arguments, values = getopt.getopt(argumentList, options, long_options)
    LIST = args.list_all
    REPLACE = args.replace
    UNTOUCHED = args.show_untouched
    VERBOSE = args.verbose
    MODE = args.mode
    TITLE = args.title


    if MODE=="watch":
        print('== WATCHING FOR TITLES ENDING IN # {} =='.format("(FORCING REPLACE)" if REPLACE else ""))
        notion.listen(replace=REPLACE, verbose=VERBOSE, showUntouched=UNTOUCHED, listAll=LIST)
    elif MODE=="one":
        print('== TRYING TO UPDATE {} {} =='.format(TITLE, "(FORCING REPLACE)" if REPLACE else ""))
        notion.updateTitle(TITLE, replace=REPLACE, verbose=VERBOSE, showUntouched=UNTOUCHED, listAll=LIST)
    elif MODE=="all":
        print('== TRYING TO UPDATE ALL TITLES {} =='.format("(FORCING REPLACE)" if REPLACE else ""))
        notion.updateAll(replace=REPLACE, verbose=VERBOSE, showUntouched=UNTOUCHED, listAll=LIST)
    else:
        printHelp()
    
        
except getopt.error as err:
    print (str(err))