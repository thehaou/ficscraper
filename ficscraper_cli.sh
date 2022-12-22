#!/bin/bash

usage() {
  echo "usage: ficscraper_cli.sh [--scrape {bookmarks|history}] [--load {bookmarks|history}] [--generate {year_in_review <year>}]"
  echo "-s, --scrape    {b|bookmarks            Uses HTTP + bs4 to scrape AO3 target."
  echo "                 h|history}             Requires login credentials in SETUP.INI."
  echo "                                        Time intensive."
  echo "-l, --load      {b|bookmarks            Loads results of --scrape into a sqlite db."
  echo "                 h|history}             Use the same argument as you did for --scrape."
  echo "-w, --wrangle   {at|all                 Uses HTTP + bs4 to wrangle tags on a work."
  echo "                 wt|work_tags           EX: 'no beta we die like men' --> 'Not Beta Read'"
  echo "                 ct|character_tags      Wrangled tags are then added to the sqlite db."
  echo "                 ft|fandom_tags}        Can be VERY time intensive."
  echo "-g, --generate  {year_in_review <year>} Generates artifacts based on sqlite db;"
  echo "                                        Therefore requires running -s and -l first."
  echo "                                        (-w is optional.)"
  echo "                                        Artifacts are generated into /output."
  echo "                                        EX: year_in_review generates JPGs into /output/cards"
  echo ""
  echo "Multi-flags not supported at this time. Please do not run something like"
  echo "./ficscraper_cli.sh -s b -l b -w at ; it won't work the way you think it will."
  echo ""
  echo "Example user flow (run in following order):"
  echo "./ficscraper_cli.sh --scrape bookmarks    <-- scrapes user's bookmarks; outputs csvs & json"
  echo "./ficscraper_cli.sh --load bookmarks      <-- loads scraped bookmark csvs into a sqlite db"
  echo "./ficscraper_cli.sh --wrangle work_tags   <-- wrangles additional-category tags on each work"
  echo "./ficscraper_cli.sh --generate year_in_review 2022    <-- generates cool stats as JPGs using"
  echo "                                                          all of the above"
  exit
}

argument_checker() {
  if [ -z "$OPTARG" ] || [ "${OPTARG:0:1}" = "-" ]; then
    echo "Error: -$option requires an argument"
    usage
    exit 1
  fi
}

if [ $# = 0 ]; then
  echo "Error: no arguments provided"
  usage
  exit 1
fi

# Transform any long opts to short (getopts only parses short options)
# https://stackoverflow.com/questions/12022592/how-can-i-use-long-options-with-the-bash-getopts-builtin
for arg in "$@"; do
  shift
  case "$arg" in
    '--help')     set -- "$@" '-h'   ;;
    '--scrape')   set -- "$@" '-s'   ;;
    '--load')     set -- "$@" '-l'   ;;
    '--wrangle')  set -- "$@" '-w'   ;;
    '--generate') set -- "$@" '-g'   ;;
    "--"*)        usage; exit 1;;
    *)            set -- "$@" "$arg" ;;
  esac
done

# Ideally this shell will kick off a script. Figure out which one.
FLOW_DIRECTORY='src/flows/'
script=''

# Process user options
while getopts ':hw:s:g:l:' option; do
  case "$option" in
    h)  usage; exit ;;
    s)  argument_checker
        case "$OPTARG" in
          b|'bookmarks') script='scrape_bookmarks.py' ;;
          h|'history') echo "Currently unsupported, sorry!"; exit 1 ;;
          *) echo "Unrecognized argument passed in to -$option: $OPTARG"
             usage
             exit 1 ;;
        esac
        ;;
    l)  argument_checker
        case "$OPTARG" in
          b|'bookmarks') script='sqlite_populate_or_replace.py' ;;
          h|'history') echo "Currently unsupported, sorry!"; exit 1 ;;
          *) echo "Unrecognized argument passed in to -$option: $OPTARG"
             usage
             exit 1 ;;
        esac
        ;;
    w)  argument_checker
        case "$OPTARG" in
          at|'all') echo "Currently unsupported, sorry!"; exit 1 ;;
          wt|'work_tags')  script='wrangle_unknown_tags.py' ;;
          ct|'character_tags') echo "Currently unsupported, sorry!"; exit 1 ;;
          *) echo "Unrecognized argument passed in to -$option: $OPTARG"
             usage
             exit 1;;
        esac
        ;;
    g)  argument_checker
        case "$OPTARG" in
          y|'year_in_review') script='year_in_review_make_cards.py' ;;
          *) echo "Unrecognized argument passed in to -$option: $OPTARG"
             usage
             exit 1 ;;
        esac
        ;;
    *)  echo "Unrecognized option passed in: $option"
        usage
        exit 1 ;;
  esac
done

if [[ -z "$script" ]]; then
  echo "Error: No script selected"
  usage
  exit 1
fi

# Set up Python path
export PYTHONPATH="$PWD/src"

# Send remaining arguments into the next callable
shift $(( OPTIND - 1 ))
python "$FLOW_DIRECTORY$script" "$@"