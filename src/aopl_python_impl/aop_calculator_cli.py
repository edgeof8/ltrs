# aopl_python_impl/aop_calculator_cli.py
#
# This script serves as the command-line interface (CLI) for the AoP Calculator.
# It handles argument parsing, orchestrates the calculation, and manages output,
# including file writing and triggering the AI explainer.
import argparse
import sys
import logging
import threading
from .aop_calculator import AoP_Calculator
# Import the new setup function
from .aop_logger import enable_explainer, capture_logs
# Import the AI session functions
from .aop_ai_explainer import get_ai_explanation_and_session, start_help_session

# Import rich for beautiful terminal output. It's an optional dependency.
try:
    from rich.console import Console
    from rich.markdown import Markdown
except ImportError:
    Console, Markdown = None, None

def interactive_ai_session(conversation):
    """Handles the interactive Q&A loop with the user."""
    console = Console() if Console else None
    print("\n" + "="*40)
    print("Entering interactive explanation mode.")
    print("Ask a question, or type 'exit' or 'quit' to end.")
    print("="*40)
    while True:
        try:
            question = input("\n[You] > ")
            if question.lower() in ['exit', 'quit']:
                break
            response = conversation.ask(question)
            if console and Markdown:
                # Strip leading/trailing whitespace from the AI response before rendering.
                console.print(Markdown(response.strip(), style="monokai"))
            else:
                print(f"\n[AI]  > {response}")
        except (KeyboardInterrupt, EOFError):
            break

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
        print("Starting AI Help session...")
        if console is None and Console:
            console = Console()
        elif Console is None:
            print("Rich library not found. For a better experience, please run: pip install rich")

        conversation = start_help_session()
        if conversation:
            print("Hello! I'm AoP Helper. Ask me anything about the calculator, or type 'exit' to quit.")
            while True:
                question = input("\n[You] > ")
                if question.lower() in ['exit', 'quit']:
                    break
                response = conversation.ask(question)
                if console and Markdown:
                    console.print(Markdown(response, style="monokai"))
                else:
                    print(f"\n[AI]  > {response}")
        return

    # If no expression is provided and we're not in help mode, show help.
    if not args.expression:
        parser.print_help()
        return

    # --- Calculation Mode ---

    # Enable logging if --debug or --explain is used.
    if args.debug or args.explain:
        enable_explainer()

    calc = AoP_Calculator(base=args.base)
    if args.no_cache:
        calc.cache = None

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

        # Handle explanation mode.
        if args.explain and ast:
            # If not writing to a file, print the result to the console.
            if not args.output:
                print(result)

            conversation, initial_explanation = get_ai_explanation_and_session(args.expression, result, args.base, ast)

            if console and Markdown:
                if initial_explanation:
                    # Strip leading/trailing whitespace from the AI response before rendering.
                    console.print(Markdown("--- \n" + initial_explanation.strip(), style="monokai"))
                else:
                    print("Error: No AI explanation received.")
            else:
                if initial_explanation:
                    print("\n🤖 AI Explanation:\n" + initial_explanation)
                else:
                    print("Error: No AI explanation received.")

            if conversation:
                interactive_ai_session(conversation)

        # If not explaining and not writing to a file, print the result.
        elif not args.output:
            print(result)

    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=args.debug)

    if not args.no_cache:
        calc.save_cache()

if __name__ == "__main__":
    main()
