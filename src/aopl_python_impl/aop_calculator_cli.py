# aopl_python_impl/aop_calculator_cli.py
#
# This script provides two modes of operation:
# 1. Direct Command-Line Execution: `ltrs "expression"` for single calculations.
# 2. Interactive REPL Mode: `ltrs` to start a persistent session.
import argparse
import sys
import logging
from typing import Optional
from .aop_calculator import AoP_Calculator
from .definitions import AoPError
# Import the new setup function
from .aop_logger import enable_explainer, enable_debug_timer, capture_logs

# Import rich for beautiful terminal output. It's an optional dependency.
try:
    from rich.console import Console
    from rich.markdown import Markdown
except ImportError:
    Console, Markdown = None, None

def handle_repl_command(line: str, calc: AoP_Calculator, console, session=None):
    """Processes a single line of input from the REPL."""
    line = line.strip()
    if not line:
        return
    if session is None:
        session = {"mode": "num"}

    # Meta-commands start with '!'
    if line.startswith('!'):
        parts = line.split()
        command = parts[0].lower()
        if command == '!help':
            print("Meta-commands: !base <num>, !mode <num|aop>, !explain <expr>, !debug <expr>, !exit, !quit")
        elif command == '!base':
            try:
                new_base = int(parts[1])
                calc.base = new_base
                print(f"Calculation base set to {new_base}.")
            except (IndexError, ValueError):
                print("Usage: !base <integer>")
        elif command == '!mode':
            try:
                new_mode = parts[1].lower()
                if new_mode not in ['num', 'aop']:
                    raise ValueError()
                session["mode"] = new_mode
                print(f"Default output mode set to '{new_mode}'.")
            except (IndexError, ValueError):
                print("Usage: !mode <num|aop>")
        elif command in ['!exit', '!quit']:
            raise EOFError # Signal to exit the loop
        elif command in ['!explain', '!debug']:
            expression = " ".join(parts[1:])
            if not expression:
                print(f"Usage: {command} <expression>")
                return

            is_debug = command == '!debug'
            enable_explainer() # AI explainer needs the logger enabled
            if is_debug:
                enable_debug_timer()
            try:
                with capture_logs() as log_buffer:
                    result, ast = calc.evaluate_expression(expression, mode=session["mode"])
                debug_log = log_buffer.getvalue()
            except AoPError as e:
                print(f"Error: {e}")
                return

            if is_debug:
                print(debug_log, end="")

            print(result)

            if command == '!explain' and ast:
                from .aop_ai_explainer import get_ai_explanation_and_session
                conversation, initial_explanation = get_ai_explanation_and_session(expression, result, calc.base, ast)
                if console and initial_explanation and Markdown:
                    console.print(Markdown("--- \n" + initial_explanation.strip(), style="monokai"))
                elif initial_explanation:
                    print("\n🤖 AI Explanation:\n" + initial_explanation)
                else:
                    print("Error: No AI explanation received.")
        else:
            print(f"Unknown command: {command}. Type !help for options.")
    else:
        try:
            value, _ = calc.evaluate(line)
            if value is None:
                return
            print(calc.format_value(value, session["mode"]))
        except AoPError as e:
            print(f"Error: {e}")


def start_interactive_session(conversation):
    """Starts an interactive session with the AI conversation."""
    print("\nStarting interactive AI session. Type 'exit' or 'quit' to end.")
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['exit', 'quit']:
                print("Ending interactive session.")
                break
            response = conversation.ask(user_input)
            print(f"AI: {response}")
        except (EOFError, KeyboardInterrupt):
            print("\nEnding interactive session.")
            break
        except Exception as e:
            print(f"Error during interaction: {e}")

def start_repl(base: int = 10, mode: str = "num"):
    """Starts the interactive REPL session."""
    print(f"Welcome to the Alphabet of Powers (AoP) Calculator.")
    print("Type an expression, or `!help` for meta-commands. `!exit` or Ctrl+C to quit.")

    calc = AoP_Calculator(base=base)
    console = Console() if Console else None
    session = {"mode": mode}

    while True:
        try:
            line = input(f"aopl(b{calc.base}/{session['mode']})> ")
            handle_repl_command(line, calc, console, session)
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break
        except Exception as e:
            logging.error(f"An error occurred: {e}", exc_info=False)

def main():
    parser = argparse.ArgumentParser(description="AoP Calculator - Calculate expressions in various bases.")
    parser.add_argument("expression", nargs='?', default=None, help="The expression to evaluate (e.g., 'a^b + c').")
    parser.add_argument("--base", type=int, default=10, help="The base for calculation (default: 10).")
    parser.add_argument("--mode", choices=["num", "aop"], default="num", help="Output mode: 'num' for numerical, 'aop' for AoP notation (default: 'num').")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode for detailed calculation trace.")
    parser.add_argument("--no-cache", action="store_true", help="Disable loading from and saving to the cache.")
    parser.add_argument("--explain", action="store_true", help="Get an interactive, AI-powered explanation of the result.")
    parser.add_argument("--ai-help", action="store_true", help="Start an interactive session with an AI assistant for general help.")
    parser.add_argument("-o", "--output", type=str, help="Path to an output file to write the result to.")
    args = parser.parse_args()

    console = Console() if Console else None

    # --- AI Help Mode ---
    if args.ai_help:
        # This block is now functional. It calls the necessary functions.
        from .aop_ai_explainer import start_help_session  # Keep import local to avoid circular deps if called elsewhere
        print("Starting AI help session...")
        conversation = start_help_session()
        if conversation:
            start_interactive_session(conversation)
        else:
            print("Could not start AI help session. Please check your configuration.")
        return

    # If no expression is provided, start the REPL (the engine's face).
    if not args.expression:
        start_repl(base=args.base, mode=args.mode)
        return

    # --- Calculation Mode ---

    # Trace logs for --debug or --explain; the performance timer is --debug only.
    if args.debug or args.explain:
        enable_explainer()
    if args.debug:
        enable_debug_timer()

    calc = AoP_Calculator(base=args.base)
    if args.no_cache:
        calc.cache = None

    exit_code = 0
    try:
        # Capture the log during calculation.
        with capture_logs() as log_buffer:
            result, ast = calc.evaluate_expression(args.expression, mode=args.mode)
            debug_log = log_buffer.getvalue()

        # Always print the debug log if the flag is set.
        if args.debug:
            print(debug_log, end="")

        # Handle file output first, as it might suppress console output.
        if args.output:
            try:
                with open(args.output, 'w') as f:
                    f.write(result)
                print(f"Result successfully written to: {args.output}")
            except IOError as e:
                logging.error(f"Could not write to output file: {e}")
            # If writing to file, we might not want to do the interactive session.
            # For now, we allow both. If we exit here, --explain wouldn't work with -o.

        # If --explain is used, print the result, get the explanation, and start the interactive session.
        if args.explain and ast:
            from .aop_ai_explainer import get_ai_explanation_and_session
            # If not writing to a file, print the result to the console.
            if not args.output:
                print(result)

            if console:
                # Use a status spinner while waiting for the AI if console is available
                with console.status("[yellow]🤖 AI is thinking...[/yellow]", spinner="dots") as status:
                    conversation, initial_explanation = get_ai_explanation_and_session(args.expression, result, args.base, ast)
                    # After getting the response, update the status before printing the final message
                    status.update("[green]✓ AI explanation received.[/green]")
            else:
                print("Waiting for AI response...")
                conversation, initial_explanation = get_ai_explanation_and_session(args.expression, result, args.base, ast)

            if console and Markdown and initial_explanation:
                # Strip leading/trailing whitespace from the AI response before rendering.
                console.print(Markdown("--- \n" + initial_explanation.strip(), style="monokai"))
            elif initial_explanation:
                print("\n🤖 AI Explanation:\n" + initial_explanation)
            else:
                print("Error: No AI explanation received.")

            if conversation:
                start_interactive_session(conversation)
            return

        # If not in explain mode, handle standard output.
        elif not args.output:
            print(result)

    except AoPError as e:
        print(f"Error: {e}")
        exit_code = 1
    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=args.debug)
        exit_code = 1

    if not args.no_cache:
        calc.save_cache()
    if exit_code:
        sys.exit(exit_code)

if __name__ == "__main__":
    main()
