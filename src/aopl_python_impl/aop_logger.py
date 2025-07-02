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
# ... (rest of logger is correct)
def print_header(title: str, bg_color: str, top_bottom_char: str = '─'):
    width = shutil.get_terminal_size((85, 20)).columns
    logging.debug(f"{bg_color}{top_bottom_char * width}{Colors.ENDC}")
    logging.debug(f"{bg_color}{' ' * ((width - len(title)) // 2)}{Colors.BOLD}{title}{Colors.RESET_BOLD}{' ' * ((width - len(title) + 1) // 2)}{Colors.ENDC}")
    logging.debug(f"{bg_color}{top_bottom_char * width}{Colors.ENDC}")
def log_line(message: str, indent_level: int = 0, prefix: str = ""):
    logging.debug(f"{'  ' * indent_level}{prefix}{message}")
def print_legend(expression: str, base: int):
    # ...
    pass
def log_eval_report_start(ast_repr: str):
    # ...
    pass
def log_eval(message: str, indent_level: int = 0):
    # ...
    pass
def log_pow(message: str, indent_level: int = 1):
    # ...
    pass
def log_format_report_start(val_repr: str):
    # ...
    pass
def log_format_details(logs: list, category_name: str):
    # ...
    pass
def log_final_result(result: str):
    # ...
    pass

class DebugTimer:
    def __init__(self):
        self.process = psutil.Process() if psutil else None
        self.laps = []
        self.start_time = time.perf_counter()
        self.last_lap_time = self.start_time
        self.cpu_cores = 1  # Default to 1 if psutil is not available
        if self.process:
            # Get number of logical cores
            if psutil:
                self.cpu_cores = psutil.cpu_count(logical=True) or 1
            # First call is non-blocking and initializes the measurement
            self.process.cpu_percent(interval=None)

    def lap(self, name: str):
        current_time = time.perf_counter()
        duration = current_time - self.last_lap_time
        cpu_usage = 0.0
        if self.process:
            # Get usage relative to one core (can be > 100%)
            process_cpu = self.process.cpu_percent(interval=None)
            # Normalize to total system usage percentage
            cpu_usage = process_cpu / self.cpu_cores

        self.laps.append((name, duration, cpu_usage))
        self.last_lap_time = current_time

    def report(self):
        total_duration = time.perf_counter() - self.start_time
        if not self.laps or total_duration == 0: return

        logging.debug("")
        print_header("Performance Breakdown", BG_Colors.PERF_BREAKDOWN)
        log_line(f"{'Stage':<20} {'Time (s)':>12} {'% of Total':>12} {'CPU Load':>10}")
        log_line(f"{'-'*20} {'-'*12} {'-'*12} {'-'*10}")
        for name, duration, cpu_usage in self.laps:
            percentage = (duration / total_duration) * 100
            cpu_str = f"{cpu_usage:.1%}" if self.process else "N/A"
            log_line(f"{name:<20} {duration:>12.6f}s {percentage:>11.2f}% {cpu_str:>9}")
        log_line(f"{'-'*20} {'-'*12} {'-'*12} {'-'*10}")
        log_line(f"{'Total':<20} {total_duration:>12.6f}s {100.0:>11.2f}%")
