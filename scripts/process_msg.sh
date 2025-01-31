#!/bin/bash

# Input should be release(<image-name>): <version>
# echo <image-name> when $2 is 1 and <version> otherwise
if [ $2 -eq 1 ]; then
    echo $(awk -F'[()]' '{print $2}' <<< $1)
else
    echo $(awk -F'[ ]' '{print $2}' <<< $1)
fi
