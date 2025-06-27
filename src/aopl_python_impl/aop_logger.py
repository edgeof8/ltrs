# aopl_python_impl/aop_logger.py
import logging
import shutil
import re

class Colors:
    # A palette inspired by the target image (similar to Nord/Catppuccin themes)
    CYAN = '\033[36m'
    MAGENTA = '\033[35m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    GREY = '\033[90m'
    WHITE = '\033[97m'
    RED = '\033[91m' # Added for errors/warnings
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m' # Added for less prominent text
    RESET_BOLD = '\033[22m' # Resets bold/dim without affecting colors

class BG_Colors:
    # Background colors for the section headers
    REPORT_HEADER = '\033[43;30m'  # Yellow BG, Black Text
    EVAL_TRACE = '\033[46m'        # Cyan BG
    FORMAT_ANALYSIS = '\033[42m'   # Green BG
    FINAL_RESULT = '\033[45;37m'   # Magenta BG, White Text (New)

ANSI_REGEX = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

def get_term_width():
    return shutil.get_terminal_size((85, 20)).columns

def print_header(title: str, bg_color: str, top_bottom_char: str = '─'):
    width = get_term_width()

    # Calculate visible length of the title itself (without leading/trailing spaces or bold codes)
    visible_title_only_len = len(title)
    # Total visible length of the line content (title + its padding)
    # We want "   TITLE   " where the spaces are also colored.
    total_content_len = visible_title_only_len + 2 # for the ' ' around the title
    total_padding = width - total_content_len
    left_padding = total_padding // 2
    right_padding = total_padding - left_padding

    # Top border
    logging.debug(f"{bg_color}{top_bottom_char * width}{Colors.ENDC}")
    # Centered title line
    logging.debug(f"{bg_color}{' ' * left_padding}{Colors.BOLD}{title}{Colors.RESET_BOLD}{' ' * right_padding}{Colors.ENDC}")
    # Bottom border
    logging.debug(f"{bg_color}{top_bottom_char * width}{Colors.ENDC}")


def log_line(message: str, indent_level: int = 0, prefix: str = ""):
    indent = "  " * indent_level
    logging.debug(f"{indent}{prefix}{message}")

def print_legend(expression: str, base: int):
    print_header("Calculation Report", BG_Colors.REPORT_HEADER)
    log_line(f"{Colors.BOLD}Input Expression:{Colors.ENDC} {Colors.WHITE}{expression}{Colors.ENDC}")
    log_line(f"{Colors.BOLD}Calculation Base:{Colors.ENDC} {Colors.WHITE}{base}{Colors.ENDC}")
    log_line("")
    log_line(f"{Colors.BOLD}Symbol Glossary:{Colors.ENDC}")
    log_line(f"  {Colors.BLUE}AoP(...) ->{Colors.ENDC} The engine's internal representation of a number (polynomial).")
    log_line(f"  {Colors.BLUE}{{@exp:coeff}}{Colors.ENDC} -> A polynomial term: {Colors.BOLD}coeff{Colors.ENDC} * base^{Colors.BOLD}exp{Colors.ENDC}.")
    log_line(f"  {Colors.CYAN}▶{Colors.ENDC} {Colors.DIM}(Evaluation Step){Colors.ENDC} -> A step in evaluating the expression tree.")
    log_line(f"  {Colors.MAGENTA}⚡︎{Colors.ENDC} {Colors.DIM}(Power Operation){Colors.ENDC} -> A base raised to an exponent.")
    logging.debug("")  # Blank line for separation

def log_eval_report_start(ast_repr: str):
    logging.debug("")  # Additional line space before Evaluation Trace
    print_header("Evaluation Trace", BG_Colors.EVAL_TRACE) # Changed title and color
    log_line("The engine first parses the input into an Abstract Syntax Tree (AST):")
    log_line(f"{Colors.GREY}{ast_repr}{Colors.ENDC}", 1)
    log_line("It then evaluates the tree step-by-step:")

def log_eval(message: str, indent_level: int = 0):
    # Ensure the symbol is always at the start of the effective line
    log_line(message, indent_level, prefix=f"{Colors.CYAN}▶{Colors.ENDC} ")

def log_pow(message: str, indent_level: int = 1):
    # Ensure the symbol is always at the start of the effective line
    log_line(message, indent_level, prefix=f"{Colors.MAGENTA}⚡︎{Colors.ENDC} ")

def log_format_report_start(val_repr: str):
    logging.debug("")  # Additional line space before Formatting Analysis
    print_header("Formatting Analysis", BG_Colors.FORMAT_ANALYSIS)
    log_line("The final numerical result is formatted back into AoP notation.")
    log_line(f"Input AoP Value: {Colors.BLUE}{val_repr}{Colors.ENDC}")

def log_format_details(logs: list, category_name: str):
    if not logs: return
    log_line(f"{Colors.GREEN}--- {category_name} ({len(logs)} total) ---{Colors.ENDC}")
    SAMPLE_SIZE = 4
    if len(logs) > (SAMPLE_SIZE * 2) + 1:
        for i in range(SAMPLE_SIZE): log_line(logs[i], indent_level=1)
        log_line(f"{Colors.GREY}... and {len(logs) - (SAMPLE_SIZE * 2)} more ...{Colors.ENDC}", indent_level=1)
        for i in range(len(logs) - SAMPLE_SIZE, len(logs)): log_line(logs[i], indent_level=1)
    else:
        for log in logs: log_line(log, indent_level=1)
    logging.debug("")  # Additional line space at the end of debug output

def log_final_result(result: str):
    logging.debug("")  # Additional line space before the header
    print_header("Final Result", BG_Colors.FINAL_RESULT) # Changed title and color
    log_line(f"{Colors.BOLD}{result}{Colors.ENDC}", indent_level=0) # Make result bold
    logging.debug("") # Add a final blank line
