#!/bin/bash
# Alphabet of Powers Calculator Helper Shell Script

# Define the path to the Python executable and the script.
# Adjust these if your project structure or Python location is different.

PYTHON_EXE="python" # Assumes python (or python3) is in PATH
SCRIPT_MODULE_PATH="aopl_python_impl.aop_calculator_cli"

# Optional: Activate virtual environment if it exists in the current dir
# and this script is in the project root.
VENV_PATH="./venv" # Assuming venv is in the same directory as this script if run from project root
if [ -d "$VENV_PATH" ] && [ -f "$VENV_PATH/bin/activate" ]; then
    # Check if already in a virtual environment to avoid nested activation issues
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "Activating virtual environment: $VENV_PATH"
        source "$VENV_PATH/bin/activate"
        # PYTHON_EXE="$VENV_PATH/bin/python" # venv python is now on PATH
    else
        echo "Already in a virtual environment: $VIRTUAL_ENV"
    fi
fi

# Check if any arguments were passed (for a simple help message)
if [ -z "$1" ]; then
    echo "Usage: ./aop.sh \"expression\" [options]"
    echo "Example: ./aop.sh \"a*b+c\" --base 10"
    echo "For help on options, type: ./aop.sh --help"
    exit 0
fi

# Execute the Python script with all passed arguments
echo "Executing: $PYTHON_EXE -m $SCRIPT_MODULE_PATH \"$@\""
"$PYTHON_EXE" -m "$SCRIPT_MODULE_PATH" "$@"
