#!/bin/bash

help() {
  echo "usage: ficscraper [-a] ..."
  echo "options:"
  echo "a    "
  exit
}

argument_checker() {
  if [ -z "$OPTARG" ] || [ "${OPTARG:0:1}" = "-" ]; then
    echo "Error: -$option requires an argument"
    help
    exit 1
  fi
}

if [ $# = 0 ]; then
  echo "Error: no arguments provided"
  help
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
    "--"*)        help; exit 1;;
    *)            set -- "$@" "$arg" ;;
  esac
done

# Ideally this shell will kick off a script. Figure out which one.
FLOW_DIRECTORY='src/flows/'
script=''

# Process user options
while getopts ':hw:s:g:l:' option; do
  case "$option" in
    h)  help; exit ;;
    s)  argument_checker
        case "$OPTARG" in
          b|'bookmarks') script='scrape_bookmarks.py' ;;
          h|'history') echo "Currently unsupported, sorry!"; exit 1 ;;
          *) echo "Error"; exit 1 ;;
        esac
        ;;
    w)  argument_checker
        case "$OPTARG" in
          at|'all') echo "all tags";;
          wt|'work_tags')  echo "work tag";;
          ct|'character_tag') echo "character tag";;
          *) echo "Unrecognized argument passed in to -$option: $OPTARG"
            help
            exit 1;;
        esac
        exit ;;
    l)  argument_checker
        case "$OPTARG" in
          b|'bookmarks') script='sqlite_reset_and_populate.py' ;;
          h|'history') echo "Currently unsupported, sorry!"; exit 1 ;;
          *) echo "Error"; exit 1 ;;
        esac
        ;;
    g)  argument_checker
        case "$OPTARG" in
          y|'year_in_review') script='year_in_review_make_cards.py' ;;
        esac
        ;;
    *)  echo "Unrecognized option passed in: $option"
        help
        exit 1 ;;
  esac
done

if [[ -z "$script" ]]; then
  echo "Error: No script selected"
  help
  exit 1
fi

# Set up Python path
export PYTHONPATH="$PWD/src"

# Send remaining arguments into the next callable
shift $(( OPTIND - 1 ))
python "$FLOW_DIRECTORY$script" "$@"