#!/usr/bin/env bash

# Android Emulator Startup Script
# Usage: ./emulator-up.sh [emulator_name]

# Set default emulator name or use environment variable
DEFAULT_EMULATOR_NAME="AndroidWorldAvd"
EMULATOR_NAME="${1:-${EMULATOR_NAME:-$DEFAULT_EMULATOR_NAME}}"

# Check if emulator name is provided
if [[ "$EMULATOR_NAME" == "your_emulator_name_here" ]]; then
    echo "Error: Please set EMULATOR_NAME environment variable or pass emulator name as argument"
    echo "Usage: $0 [emulator_name]"
    echo "   or: EMULATOR_NAME=my_emulator $0"
    exit 1
fi

# Check if Android SDK emulator exists
EMULATOR_PATH="$HOME/Library/Android/sdk/emulator/emulator"
if [[ ! -f "$EMULATOR_PATH" ]]; then
    echo "Error: Android emulator not found at $EMULATOR_PATH"
    echo "Please check your Android SDK installation"
    exit 1
fi

echo "Starting Android emulator: $EMULATOR_NAME"
echo "Command: $EMULATOR_PATH -avd $EMULATOR_NAME -no-snapshot -grpc 8554"
echo ""

# Start the emulator
"$EMULATOR_PATH" -avd "$EMULATOR_NAME" -no-snapshot -grpc 8554