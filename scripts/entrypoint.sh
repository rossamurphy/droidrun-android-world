#!/bin/bash

# Start Emulator
#============================================
./scripts/start_emu_headless.sh && \
adb root && \
droidrun setup --path /opt/shared/droidrun-portal.apk && \
droidrun-android-world --perform-emulator-setup "$@"
