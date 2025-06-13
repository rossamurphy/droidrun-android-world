#!/bin/bash

ANDROID_WORLD_PATH=$1

if [ -z "$ANDROID_WORLD_PATH" ]; then
    echo "ANDROID_WORLD_PATH is not set"
    echo "Usage: $0 <ANDROID_WORLD_PATH>"
    exit 1
fi

# Detect OS and set SED_INPLACE accordingly
if [[ "$(uname)" == "Darwin" ]]; then
    SED_INPLACE=("-i" "")
else
    SED_INPLACE=("-i")
fi

find $ANDROID_WORLD_PATH/android_world -type d -exec bash -c 'f="$0/__init__.py"; [ -f "$f" ] || touch "$f"' {} \;
sed "${SED_INPLACE[@]}" 's/^packages = /# packages = /' "$ANDROID_WORLD_PATH/pyproject.toml"
sed "${SED_INPLACE[@]}" 's/^android_world = /# android_world = /' "$ANDROID_WORLD_PATH/pyproject.toml"
sed "${SED_INPLACE[@]}" "s/'proto\/\*\.proto'/'proto\/\*\.proto', 'proto\/\*\.textproto'/" "$ANDROID_WORLD_PATH/setup.py"
