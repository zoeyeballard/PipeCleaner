"""
person6_metrics.py — Performance Metrics Engine & Test Suite
ECE 5367 Final Project: Pipelined Performance Analyzer
Owner: Zoey

RESPONSIBILITY:
    1. Consume execution logs from Person 3 (single-cycle) and Person 4
       (pipelined) and compute CPI, latency, throughput, and speedup.
    2. Own the shared test programs that ALL team members run their
       simulators against. Write these from day one — they're useful immediately.
    3. Produce a formatted comparison report.

DEPENDENCY STRATEGY:
    Only depends on common.py (always available).
    Stubs for run_single_cycle and run_pipeline let Person 6 work independently.
    Toggle USE_STUBS = True until Persons 3 & 4 are ready.

INTERFACE CONTRACT (do not change signatures):
    compute_metrics(log, total_instructions, clock_period_ns) -> dict
    compare_simulators(single_log, pipeline_log, n_instructions) -> dict
    print_report(comparison) -> None
    get_test_programs() -> dict

TESTING:
    Run this file directly: python person6_metrics.py
"""

from common import make_metrics

USE_STUBS = True

if not USE_STUBS:
    from person3_single_cycle import run_single_cycle
    from person1_parser import parse_program
    from person4_pipeline import run_pipeline
else:
    # Stub simulators — return fake but structurally correct data
    def parse_program(source):
        from common import make_instruction
        return [
            make_instruction("addi", "I", rs=0, rt=8, imm=5,  raw="addi $t0,$zero,5"),
            make_instruction("addi", "I", rs=0, rt=9, imm=3,  raw="addi $t1,$zero,3"),
            make_instruction("add",  "R", rs=8, rt=9, rd=10,  raw="add  $t2,$t0,$t1"),
        ]

    def run_single_cycle(instructions, initial_state=None):
        from common import make_cpu_state, make_log_entry, make_metrics, make_instruction
        log = [make_log_entry(i, "WB", instr) for i, instr in enumerate(instructions)]
        m = make_metrics()
        m["total_instructions"] = len(instructions)
        m["total_cycles"]       = len(instructions)
        m["cpi"]                = 1.0
        return make_cpu_state(), log, m

    def run_pipeline(instructions, initial_state=None):
        from common import make_cpu_state, make_log_entry, make_metrics
        # Simulate 2 stall cycles for demo
        n = len(instructions)
        log = []
        for i, instr in enumerate(instructions):
            for stage in ["IF","ID","EX","MEM","WB"]:
                log.append(make_log_entry(i + 4, stage, instr))
        m = make_metrics()
        m["total_instructions"] = n
        m["total_cycles"]       = n + 4 + 2   # pipeline fill + 2 stalls
        m["stall_cycles"]       = 2
        m["cpi"]                = m["total_cycles"] / n
        return make_cpu_state(), log, m


# ─────────────────────────────────────────────
# TEST PROGRAMS
# (write these first — everyone uses them)
# ─────────────────────────────────────────────

def get_test_programs() -> dict:
    """
    Shared test programs for all team members.
    Keys are descriptive names; values are MIPS assembly strings.

    Person 6 owns these. Add more as needed.
    Everyone else calls: get_test_programs()["no_hazards"]

    Returns:
        dict: { name: mips_assembly_string }
    """
    return {

        # ── Basic: no hazards, sequential R/I-type only ──
        "no_hazards": """
            addi $t0, $zero, 10
            addi $t1, $zero, 20
            addi $t2, $zero, 30
            add  $t3, $t0, $t1
            sub  $t4, $t3, $t2
        """,

        # ── RAW hazard: add immediately uses result of addi ──
        "raw_hazard": """
            addi $t0, $zero, 5
            add  $t1, $t0, $t0
        """,

        # ── Load-use hazard: LW followed immediately by use ──
        "load_use_hazard": """
            addi $t0, $zero, 4
            sw   $t0, 0($zero)
            lw   $t1, 0($zero)
            add  $t2, $t1, $t0
        """,

        # ── Branch not taken ──
        "branch_not_taken": """
            addi $t0, $zero, 5
            addi $t1, $zero, 3
            beq  $t0, $t1, end
            addi $t2, $zero, 99
            end:
            addi $t3, $zero, 1
        """,

        # ── Branch taken ──
        "branch_taken": """
            addi $t0, $zero, 5
            addi $t1, $zero, 5
            beq  $t0, $t1, end
            addi $t2, $zero, 99
            end:
            addi $t3, $zero, 1
        """,

        # ── Memory: store then load ──
        "memory_ops": """
            addi $t0, $zero, 42
            sw   $t0, 0($zero)
            lw   $t1, 0($zero)
            add  $t2, $t1, $t1
        """,

        # ── Mixed: multiple hazard types ──
        "mixed_hazards": """
            addi $t0, $zero, 1
            addi $t1, $zero, 2
            add  $t2, $t0, $t1
            add  $t3, $t2, $t1
            lw   $t4, 0($zero)
            add  $t5, $t4, $t2
        """,
    }


# ─────────────────────────────────────────────
# METRICS COMPUTATION
# ─────────────────────────────────────────────

def compute_metrics(log: list, total_instructions: int, clock_period_ns: float = 1.0) -> dict:
    """
    Compute performance metrics from an execution log.

    Args:
        log                (list[dict]): Log from run_single_cycle or run_pipeline
        total_instructions (int):        Number of real (non-NOP) instructions
        clock_period_ns    (float):      Clock period in nanoseconds (default 1.0)

    Returns:
        dict: Populated make_metrics() dict

    Formulas:
        total_cycles = max cycle index in log + 1
        stall_cycles = count of log entries where event == "stall"
        flush_cycles = count of log entries where event == "flush"
        cpi          = total_cycles / total_instructions
        latency      = total_cycles * clock_period_ns
        throughput   = total_instructions / total_cycles   (IPC)
    """
    m = make_metrics()

    if not log or total_instructions == 0:
        return m

    # total_cycles = max cycle index in log + 1
    total_cycles = max(entry["cycle"] for entry in log) + 1

    # Count stall and flush events (each log entry that has the event tag)
    stall_cycles = sum(1 for entry in log if entry["event"] == "stall")
    flush_cycles = sum(1 for entry in log if entry["event"] == "flush")

    m["total_instructions"] = total_instructions
    m["total_cycles"]       = total_cycles
    m["stall_cycles"]       = stall_cycles
    m["flush_cycles"]       = flush_cycles
    m["cpi"]                = total_cycles / total_instructions
    m["latency"]            = total_cycles * clock_period_ns
    m["throughput"]         = total_instructions / total_cycles   # IPC

    return m


def compare_simulators(
    single_log: list,
    pipeline_log: list,
    n_instructions: int,
    clock_period_ns: float = 1.0
) -> dict:
    """
    Run both simulators on the same program and build a comparison dict.

    Args:
        single_log     (list): Log from run_single_cycle
        pipeline_log   (list): Log from run_pipeline
        n_instructions (int):  Number of real instructions in the program
        clock_period_ns (float): Clock period for latency calculation

    Returns:
        dict: {
            "single_cycle": metrics dict,
            "pipelined":    metrics dict,
            "speedup":      float,
            "cpi_overhead": float,   # pipelined_cpi - ideal_cpi (1.0)
        }
    """
    single_metrics   = compute_metrics(single_log,   n_instructions, clock_period_ns)
    pipeline_metrics = compute_metrics(pipeline_log, n_instructions, clock_period_ns)

    single_cycles   = single_metrics["total_cycles"]
    pipeline_cycles = pipeline_metrics["total_cycles"]

    # Avoid division by zero if something went wrong
    speedup      = (single_cycles / pipeline_cycles) if pipeline_cycles > 0 else 0.0
    # Ideal pipelined CPI is 1.0; overhead is how much worse we actually did
    cpi_overhead = pipeline_metrics["cpi"] - 1.0

    # Also fill in the cross-comparison fields defined in make_metrics()
    single_metrics["single_cycle_cycles"]   = single_cycles
    single_metrics["pipelined_cycles"]      = pipeline_cycles
    single_metrics["speedup"]               = speedup

    pipeline_metrics["single_cycle_cycles"] = single_cycles
    pipeline_metrics["pipelined_cycles"]    = pipeline_cycles
    pipeline_metrics["speedup"]             = speedup

    return {
        "single_cycle": single_metrics,
        "pipelined":    pipeline_metrics,
        "speedup":      speedup,
        "cpi_overhead": cpi_overhead,
    }


def print_report(comparison: dict, program_name: str = "test") -> None:
    """
    Print a formatted side-by-side comparison report to stdout.

    Args:
        comparison   (dict): Output of compare_simulators()
        program_name (str):  Label for the report header

    Example output:
        ╔══════════════════════════════════════════╗
        ║  MIPS Performance Analysis: raw_hazard   ║
        ╠══════════════════════════════╦═══════════╣
        ║ Metric          │ Single     │ Pipelined ║
        ╠══════════════════════════════╩═══════════╣
        ║ Total Cycles    │     2      │     4     ║
        ║ CPI             │   1.000    │   2.000   ║
        ║ Throughput(IPC) │   1.000    │   0.500   ║
        ║ Stall Cycles    │     0      │     1     ║
        ╠══════════════════════════════════════════╣
        ║ Speedup (single/pipelined): 0.50x        ║
        ╚══════════════════════════════════════════╝
    """
    sc = comparison["single_cycle"]
    pp = comparison["pipelined"]
    speedup      = comparison["speedup"]
    cpi_overhead = comparison["cpi_overhead"]

    # ── Layout constants ──────────────────────────────────────────────────────
    W_TOTAL  = 50          # total inner width (between the outer ║ chars)
    W_LABEL  = 18          # width of the metric label column
    W_COL    = 12          # width of each value column (Single / Pipelined)
    # Total check: 1 (left ║) + W_LABEL + 1 (│) + W_COL + 1 (│) + W_COL + 1 (right ║)
    # = 1 + 18 + 1 + 12 + 1 + 12 + 1 = 46  → pad W_TOTAL to 46 for clean fit

    # Helper: center a string inside a field of given width
    def c(text, width):
        return text.center(width)

    # Helper: right-align a number string inside a field
    def r(text, width):
        return text.rjust(width - 1).ljust(width)

    # Horizontal rule builders
    def rule_top():
        return "╔" + "═" * W_TOTAL + "╗"

    def rule_mid_header():
        # Split rule with ╦ to visually separate the header
        left  = W_LABEL + 1          # label col + separator │
        right = W_TOTAL - left - 1   # remainder minus the ╩ char
        return "╠" + "═" * left + "╦" + "═" * right + "╣"

    def rule_mid():
        left  = W_LABEL + 1
        right = W_TOTAL - left - 1
        return "╠" + "═" * left + "╩" + "═" * right + "╣"

    def rule_sep():
        return "╠" + "═" * W_TOTAL + "╣"

    def rule_bot():
        return "╚" + "═" * W_TOTAL + "╝"

    # ── Row builders ─────────────────────────────────────────────────────────
    def title_row(text):
        inner = c(text, W_TOTAL)
        return "║" + inner + "║"

    def header_row():
        label = c("Metric",     W_LABEL)
        col1  = c("Single",     W_COL)
        col2  = c("Pipelined",  W_COL)
        return "║ " + label + "│" + col1 + "│" + col2 + " ║"

    def data_row(label, single_val, pipe_val):
        lbl  = label.ljust(W_LABEL - 1)
        col1 = c(single_val, W_COL)
        col2 = c(pipe_val,   W_COL)
        return "║ " + lbl + "│" + col1 + "│" + col2 + " ║"

    def summary_row(text):
        inner = (" " + text).ljust(W_TOTAL)
        return "║" + inner + "║"

    # ── Format values ────────────────────────────────────────────────────────
    def fmt_int(v):   return str(int(v))
    def fmt_f3(v):    return f"{v:.3f}"

    # ── Assemble report ───────────────────────────────────────────────────────
    title = f"MIPS Performance Analysis: {program_name}"

    lines = [
        rule_top(),
        title_row(title),
        rule_mid_header(),
        header_row(),
        rule_mid(),
        data_row("Total Instructions",
                 fmt_int(sc["total_instructions"]),
                 fmt_int(pp["total_instructions"])),
        data_row("Total Cycles",
                 fmt_int(sc["total_cycles"]),
                 fmt_int(pp["total_cycles"])),
        data_row("Stall Cycles",
                 fmt_int(sc["stall_cycles"]),
                 fmt_int(pp["stall_cycles"])),
        data_row("Flush Cycles",
                 fmt_int(sc["flush_cycles"]),
                 fmt_int(pp["flush_cycles"])),
        data_row("CPI",
                 fmt_f3(sc["cpi"]),
                 fmt_f3(pp["cpi"])),
        data_row("Throughput (IPC)",
                 fmt_f3(sc["throughput"]),
                 fmt_f3(pp["throughput"])),
        data_row("Latency (ns)",
                 fmt_f3(sc["latency"]),
                 fmt_f3(pp["latency"])),
        rule_sep(),
        summary_row(f"Speedup (single / pipelined): {speedup:.2f}x"),
        summary_row(f"CPI Overhead (vs ideal 1.0):  {cpi_overhead:+.3f}"),
        rule_bot(),
    ]

    print("\n".join(lines))
    print()   # blank line between reports


# ─────────────────────────────────────────────
# QUICK SELF-TEST (run: python person6_metrics.py)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Running with {'STUBS' if USE_STUBS else 'real modules'}...\n")

    programs = get_test_programs()
    print(f"Available test programs: {list(programs.keys())}\n")

    # Run comparison on each test program
    for name, source in programs.items():
        instructions = parse_program(source)
        n = len(instructions)

        _, single_log, _ = run_single_cycle(instructions)
        _, pipeline_log, _ = run_pipeline(instructions)

        try:
            comparison = compare_simulators(single_log, pipeline_log, n)
            print_report(comparison, name)
        except NotImplementedError as e:
            print(f"[STUB] Program '{name}': {e}")
            print(f"  Instructions: {n}")
            print(f"  Single-cycle log entries: {len(single_log)}")
            print(f"  Pipeline log entries:     {len(pipeline_log)}\n")