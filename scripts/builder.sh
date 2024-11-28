#!/bin/bash

base_dir="images/gerd"
# for file in $(git diff --name-only origin/main HEAD); do
#     base_dir=$(awk -F/ 'NF >= 2 { print $1 "/" $2 } NF == 1 { print $1 }' <<< $file)
#     break
# done

# if [ ! -f "$base_dir/Dockerfile" ]; then
#     echo "Builder: ❌ $base_dir does not contain a Dockerfile. Something went wrong during linting"
#     exit 1
# fi
echo "Builder: ✅ using Dockerfile in $base_dir."

# Build the Docker image
cd ${base_dir} && docker buildx build -t gerd:test .
echo "Builder: ✅ $base_dir built successfully."
