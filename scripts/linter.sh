#!/bin/bash

# Rule 1: Changes must be limited to a single image

# base_dir=""
# for file in $(git diff --name-only origin/main HEAD); do
#     echo "File changed: $file"
#     # Check if base_dir is set
#     if [ -z "$base_dir" ]; then
#         base_dir=$(awk -F/ 'NF >= 2 { print $1 "/" $2 } NF == 1 { print $1 }' <<< $file)
#     else
#         candidate_dir=$(awk -F/ 'NF >= 2 { print $1 "/" $2 } NF == 1 { print $1 }' <<< $file)
#         if [ "$base_dir" != "$candidate_dir" ]; then
#             echo "Found changes in $base_dir and $candidate_dir. Changes must be limited to a single image."
#             exit 1
#         fi
#     fi
# done

# Rule 2: Changes must be limited to a single image

echo "Something is not right!"
echo "I need to two lines for this!"

exit 1
