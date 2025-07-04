# aopl_python_impl/aop_logger.py
#
# This module provides all the functionality for the detailed, colorized
# debug trace (`--debug` flag). It uses the 'rich' library to create
# beautifully formatted, consistent output for headers, logs, and tables.
import logging
import sys
import shutil
import re
import time
from io import StringIO
from contextlib import contextmanager

# Import rich components. It's an optional dependency.
try:
    from rich.console import Console
    from rich.rule import Rule
    from rich.table import Table
    from rich.text import Text
except ImportError:
    Console, Rule, Table, Text = None, None, None, None

try:
    import psutil
except ImportError:
    psutil = None

# This global flag controls all output from this module.
_EXPLAIN_MODE_ENABLED = False
# Global console object to manage all rich printing.
console = Console() if Console else None

def enable_explainer():
    """Turns on the explainer output."""
    global _EXPLAIN_MODE_ENABLED
    _EXPLAIN_MODE_ENABLED = True

@contextmanager
def capture_logs():
    """A context manager to capture console output into a string buffer."""
    if not console:
        old_stdout = sys.stdout
        log_capture_buffer = StringIO()
        sys.stdout = log_capture_buffer
        try:
            yield log_capture_buffer
        finally:
            sys.stdout = old_stdout
    else:
        capture_buffer = StringIO()
        # Temporarily replace the console's file with our buffer
        original_file = console.file
        console.file = capture_buffer
        yield capture_buffer
        # Restore the original file
        console.file = original_file

class Colors:
    CYAN = '\033[36m'
    MAGENTA = '\033[35m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    GREY = '\033[90m'
    WHITE = '\033[97m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET_BOLD = '\033[22m'

class BG_Colors:
    REPORT_HEADER = '\033[43;30m'
    EVAL_TRACE = '\033[46m'
    FORMAT_ANALYSIS = '\033[42m'
    PERF_BREAKDOWN = '\033[44m'
    FINAL_RESULT = '\033[45;37m'

def print_header(title: str, style: str):
    """Prints a styled panel header using rich or a fallback method."""
    if not _EXPLAIN_MODE_ENABLED: return
    if console and Rule and Text:
        console.print(Rule(Text(title, style=f"bold {style}"), style=style))
    else:
        width = shutil.get_terminal_size((85, 20)).columns
        bg_color = style if style in [BG_Colors.REPORT_HEADER, BG_Colors.EVAL_TRACE, BG_Colors.FORMAT_ANALYSIS, BG_Colors.PERF_BREAKDOWN, BG_Colors.FINAL_RESULT] else BG_Colors.REPORT_HEADER
        print(f"{bg_color}{'─' * width}{Colors.ENDC}")
        print(f"{bg_color}{' ' * ((width - len(title)) // 2)}{Colors.BOLD}{title}{Colors.RESET_BOLD}{' ' * ((width - len(title) + 1) // 2)}{Colors.ENDC}")
        print(f"{bg_color}{'─' * width}{Colors.ENDC}")

def log_line(text_obj, indent_level=0, prefix=""):
    if not _EXPLAIN_MODE_ENABLED: return
    if console and Text:
        if isinstance(text_obj, str):
            final_text = f"{'  ' * indent_level}{prefix}{text_obj}"
        else:
            final_text = Text("  " * indent_level) + (prefix if isinstance(prefix, Text) else Text(str(prefix))) + text_obj
        console.print(final_text)
    else:
        if Text and isinstance(text_obj, Text) and hasattr(text_obj, 'plain'):
            print(f"{'  ' * indent_level}{prefix}{text_obj.plain}")
        else:
            print(f"{'  ' * indent_level}{prefix}{text_obj}")

def print_legend(expression: str, base: int):
    if not _EXPLAIN_MODE_ENABLED: return
    if console and Text:
        print_header("Calculation Report", "bold blue")
        log_line(Text.assemble(("Input Expression: ", "bold"), (expression, "white")))
        log_line(Text.assemble(("Calculation Base: ", "bold"), (str(base), "white")))
        console.print() # For a blank line
    else:
        print_header("Calculation Report", BG_Colors.REPORT_HEADER)
        log_line(f"{Colors.BOLD}Input Expression:{Colors.ENDC} {Colors.WHITE}{expression}{Colors.ENDC}")
        log_line(f"{Colors.BOLD}Calculation Base:{Colors.ENDC} {Colors.WHITE}{base}{Colors.ENDC}")
        print()

def log_eval_report_start(ast_repr: str):
    if not _EXPLAIN_MODE_ENABLED: return
    if console and Text:
        print_header("Evaluation Trace", "bold cyan")
        log_line(Text("The input expression is parsed into an Abstract Syntax Tree (AST):"))
        log_line(Text(ast_repr, style="dim"), 1)
        log_line(Text("The tree is then evaluated recursively:"))
    else:
        print_header("Evaluation Trace", BG_Colors.EVAL_TRACE)
        log_line("The input expression is parsed into an Abstract Syntax Tree (AST):")
        log_line(f"{Colors.GREY}{ast_repr}{Colors.ENDC}", 1)
        log_line("The tree is then evaluated recursively:")

def log_eval(message: str, indent_level: int = 0):
    if not _EXPLAIN_MODE_ENABLED: return
    if console and Text:
        log_line(Text(message), indent_level, prefix=Text("▶ ", style="cyan"))
    else:
        log_line(message, indent_level, prefix=f"{Colors.CYAN}▶{Colors.ENDC} ")

def log_pow(message: str, indent_level: int = 1):
    if not _EXPLAIN_MODE_ENABLED: return
    if console and Text:
        log_line(Text(message), indent_level, prefix=Text("⚡︎ ", style="magenta"))
    else:
        log_line(message, indent_level, prefix=f"{Colors.MAGENTA}⚡︎{Colors.ENDC} ")

class DebugTimer:
    def __init__(self, enabled=False):
        self.enabled = enabled
        if not self.enabled: return
        self.process = psutil.Process() if psutil else None
        self.laps = []
        self.start_time = time.perf_counter()
        self.last_lap_time = self.start_time
        self.cpu_cores = 1
        if self.process and psutil:
            try:
                self.cpu_cores = psutil.cpu_count(logical=True) or 1
                self.process.cpu_percent(interval=None)
            except Exception:
                self.process = None

    def lap(self, name: str):
        if not self.enabled: return
        current_time = time.perf_counter()
        duration = current_time - self.last_lap_time
        cpu_usage = 0.0
        if self.process and psutil:
            try:
                process_cpu = self.process.cpu_percent(interval=None)
                cpu_usage = process_cpu / self.cpu_cores
            except Exception:
                self.process = None
        self.laps.append((name, duration, cpu_usage))
        self.last_lap_time = current_time

    def report(self):
        if not self.enabled or not self.laps: return
        total_duration = time.perf_counter() - self.start_time
        if total_duration == 0: return

        if console and Table:
            console.print() # Blank line
            print_header("Performance Breakdown", "bold purple")

            if Table:
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Stage", style="cyan", no_wrap=True)
                table.add_column("Time (s)", justify="right", style="green")
                table.add_column("% of Total", justify="right", style="yellow")
                table.add_column("CPU Load", justify="right", style="red")

            for name, duration, cpu_usage in self.laps:
                percentage = (duration / total_duration) * 100
                cpu_str = f"{cpu_usage:.1%}" if self.process else "N/A"
                table.add_row(name, f"{duration:.6f}s", f"{percentage:.2f}%", cpu_str)

            if Table:
                console.print(table)
                if Text:
                    log_line(Text.assemble(("Total Time: ", "bold"), (f"{total_duration:.6f}s", "bold green")))
                else:
                    log_line(f"Total Time: {total_duration:.6f}s")
                console.print()
        else:
            print()
            print_header("Performance Breakdown", BG_Colors.PERF_BREAKDOWN)
            log_line(f"{'Stage':<20} {'Time (s)':>12} {'% of Total':>12} {'CPU Load':>10}")
            log_line(f"{'-'*20} {'-'*12} {'-'*12} {'-'*10}")
            for name, duration, cpu_usage in self.laps:
                percentage = (duration / total_duration) * 100
                cpu_str = f"{cpu_usage:.1%}" if self.process else "N/A"
                log_line(f"{name:<20} {duration:>12.6f}s {percentage:>11.2f}% {cpu_str:>9}")
            log_line(f"{'-'*20} {'-'*12} {'-'*12} {'-'*10}")
            log_line(f"{'Total':<20} {total_duration:>12.6f}s {100.0:>11.2f}%")
            print()
