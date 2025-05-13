#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <profile_name> <since> <output_file>"
    echo "Example: $0 htop '10 minutes ago' logs.txt"
    exit 1
fi

PROFILE_NAME="$1"
SINCE="$2"
OUTPUT_FILE="$3"

journalctl -g 'profile=\"'$PROFILE_NAME'\"' --since "$SINCE" --no-pager -k --output=short-iso-precise | grep 'apparmor=' > "$OUTPUT_FILE"

