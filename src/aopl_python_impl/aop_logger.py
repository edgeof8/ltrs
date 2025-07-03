# aopl_python_impl/aop_logger.py
import logging
import shutil
import re
import time

try:
    import psutil
except ImportError:
    psutil = None

# This global flag controls all output from this module.
_EXPLAIN_MODE_ENABLED = False

def enable_explainer():
    """Turns on the explainer output."""
    global _EXPLAIN_MODE_ENABLED
    _EXPLAIN_MODE_ENABLED = True

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

def print_header(title: str, bg_color: str, top_bottom_char: str = '─'):
    if not _EXPLAIN_MODE_ENABLED: return
    width = shutil.get_terminal_size((85, 20)).columns
    print(f"{bg_color}{top_bottom_char * width}{Colors.ENDC}")
    print(f"{bg_color}{' ' * ((width - len(title)) // 2)}{Colors.BOLD}{title}{Colors.RESET_BOLD}{' ' * ((width - len(title) + 1) // 2)}{Colors.ENDC}")
    print(f"{bg_color}{top_bottom_char * width}{Colors.ENDC}")

def log_line(message: str, indent_level: int = 0, prefix: str = ""):
    if not _EXPLAIN_MODE_ENABLED: return
    print(f"{'  ' * indent_level}{prefix}{message}")

def print_legend(expression: str, base: int):
    if not _EXPLAIN_MODE_ENABLED: return
    print_header("Calculation Report", BG_Colors.REPORT_HEADER)
    log_line(f"{Colors.BOLD}Input Expression:{Colors.ENDC} {Colors.WHITE}{expression}{Colors.ENDC}")
    log_line(f"{Colors.BOLD}Calculation Base:{Colors.ENDC} {Colors.WHITE}{base}{Colors.ENDC}")
    print()

def log_eval_report_start(ast_repr: str):
    if not _EXPLAIN_MODE_ENABLED: return
    print_header("Evaluation Trace", BG_Colors.EVAL_TRACE)
    log_line("The input expression is parsed into an Abstract Syntax Tree (AST):")
    log_line(f"{Colors.GREY}{ast_repr}{Colors.ENDC}", 1)
    log_line("The tree is then evaluated recursively:")

def log_eval(message: str, indent_level: int = 0):
    if not _EXPLAIN_MODE_ENABLED: return
    log_line(message, indent_level, prefix=f"{Colors.CYAN}▶{Colors.ENDC} ")

def log_pow(message: str, indent_level: int = 1):
    if not _EXPLAIN_MODE_ENABLED: return
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
