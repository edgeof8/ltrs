# aopl_python_impl/aop_logger.py
import logging, shutil, re, time
try:
    import psutil
except ImportError:
    psutil = None

class Colors:
    CYAN = '\033[36m'; MAGENTA = '\033[35m'; YELLOW = '\033[93m'; BLUE = '\033[94m'
    GREEN = '\033[92m'; GREY = '\033[90m'; WHITE = '\033[97m'; RED = '\033[91m'
    ENDC = '\033[0m'; BOLD = '\033[1m'; DIM = '\033[2m'; RESET_BOLD = '\033[22m'

class BG_Colors:
    REPORT_HEADER = '\033[43;30m'; EVAL_TRACE = '\033[46m'; FORMAT_ANALYSIS = '\033[42m'
    PERF_BREAKDOWN = '\033[44m'; FINAL_RESULT = '\033[45;37m'

ANSI_REGEX = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

def get_term_width():
    return shutil.get_terminal_size((85, 20)).columns

def print_header(title, bg_color, char='─'):
    term_width = get_term_width()
    title_padded = f" {title} ".center(term_width, char)
    logging.debug(f"{bg_color}{title_padded}{Colors.ENDC}")

def log_line(message, indent=0, prefix=""):
    indent_str = " " * indent
    logging.debug(f"{indent_str}{prefix}{message}")

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

def log_eval_report_start(ast_repr):
    print_header("Evaluation Trace", BG_Colors.EVAL_TRACE)
    logging.debug(f"Starting evaluation of AST: {ast_repr}")

def log_eval(message, indent=0):
    log_line(message, indent, "[EVAL] ")

def log_pow(message, indent=1):
    log_line(message, indent, "[POW] ")

def log_format_report_start(val_repr):
    print_header("Formatting Analysis", BG_Colors.FORMAT_ANALYSIS)
    logging.debug(f"Starting formatting of value: {val_repr}")

def log_format_details(logs, category):
    print_header(category, BG_Colors.REPORT_HEADER)
    for log in logs:
        logging.debug(log)

def log_final_result(result):
    print_header("Final Result", BG_Colors.FINAL_RESULT)
    logging.debug(result)

class DebugTimer:
    def __init__(self):
        self.process = psutil.Process() if psutil else None
        self.laps = []
        self.start_time = time.perf_counter()
        self.last_lap_time = self.start_time
        self.cpu_cores = 1  # Default to 1 to avoid division by zero
        # --- FIX: Guard the access to psutil ---
        if self.process and psutil:
            self.cpu_cores = psutil.cpu_count(logical=True) or 1
            self.process.cpu_percent(interval=None)

    def lap(self, name: str):
        current_time = time.perf_counter()
        duration = current_time - self.last_lap_time
        cpu_usage = 0.0
        if self.process:
            process_cpu = self.process.cpu_percent(interval=None)
            cpu_usage = process_cpu / self.cpu_cores

        self.laps.append((name, duration, cpu_usage))
        self.last_lap_time = current_time

    def report(self):
        total_duration = time.perf_counter() - self.start_time
        if not self.laps or total_duration == 0:
            return

        logging.debug("")
        print_header("Performance Breakdown", BG_Colors.PERF_BREAKDOWN)
        log_line(f"{'Stage':<20} {'Time (s)':>12} {'% of Total':>12} {'CPU Load':>10}")
        log_line(f"{'-'*20} {'-'*12} {'-'*12} {'-'*10}")
        for name, duration, cpu_usage in self.laps:
            percentage = (duration / total_duration) * 100 if total_duration > 0 else 0.0
            cpu_str = f"{cpu_usage:.1%}" if self.process else "N/A"
            log_line(f"{name:<20} {duration:>12.6f}s {percentage:>11.2f}% {cpu_str:>9}")
        log_line(f"{'-'*20} {'-'*12} {'-'*12} {'-'*10}")
        log_line(f"{'Total':<20} {total_duration:>12.6f}s {100.0:>11.2f}%")
