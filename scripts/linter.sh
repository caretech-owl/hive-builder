#!/bin/bash

# Rule 1: Changes must be limited to a single subfolder

base_dir=""
echo $(git diff --name-only origin/${{ GITHUB_BASE_REF }}..${{ GITHUB_SHA }})
for file in $(git diff --name-only origin/${{ GITHUB_BASE_REF }}..${{ GITHUB_SHA }}); do
    echo "Linter: Checking $file"
    # Check if base_dir is set
    if [ -z "$base_dir" ]; then
        base_dir=$(awk -F/ 'NF >= 2 { print $1 "/" $2 } NF == 1 { print $1 }' <<< $file)
        if [[ $base_dir != images/* ]]; then
            echo "Linter: ❌ $file appears to be outside of an image directory. Changes must be limited to a single image. You might need to rebase your PR."
            exit 1
        fi
    else
        candidate_dir=$(awk -F/ 'NF >= 2 { print $1 "/" $2 } NF == 1 { print $1 }' <<< $file)
        if [ "$base_dir" != "$candidate_dir" ]; then
            echo "Linter: ❌ Found changes in $base_dir and $candidate_dir. Changes must be limited to a single image. You might need to rebase your PR."
            exit 1
        fi
    fi
done
echo "Linter: ✅ Changes must be limited to a single image (${base_dir})."

# Rule 2: image directory must contain a Dockerfile
if [ ! -f "$base_dir/Dockerfile" ]; then
    echo "Linter: ❌ $base_dir does not contain a Dockerfile. Please add a Dockerfile to the image directory."
    exit 1
fi
echo "Linter: ✅ ${base_dir} contains a Dockerfile."
