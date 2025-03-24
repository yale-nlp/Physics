#!/bin/bash

# Ensure the script exits if an error occurs
set -e

# Define the full path of the Python script
PYTHON_SCRIPT=""
SCRIPT_PATH=""

# Ensure environment variables and paths are loaded correctly
export PATH=""

# Start the Python script, run in the background, and log output,
# ensuring it continues execution even if the foreground exits
nohup $PYTHON_SCRIPT $SCRIPT_PATH > final_eva.out 2>&1 &