#!/bin/bash

PREFIX="${1:-${PREFIX:-"aa-exec -p tmp_profile"}}"

while true; do
    read -e -p "$ " cmd
    [[ -z "$cmd" ]] && continue

    if [[ "$cmd" =~ ^$PREFIX ]]; then
        eval "$cmd"
    else
        new_cmd="$PREFIX $cmd"
#        echo "Updated cmd: $new_cmd"
        eval "$new_cmd"
    fi
done