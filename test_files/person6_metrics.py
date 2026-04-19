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

from pathlib import Path
import argparse

from common import make_metrics

# -----------------------------------------------------------------------------
# PROTOTYPE MIGRATION NOTES (main branch scaffold only)
# -----------------------------------------------------------------------------
# This file currently compares simulator logs.
# To match the prototype analyzer branch and professor sample output, add:
# - project3-style formatter (Processed N file(s), counts, mode sections)
# - per-file analyzer driver
# - CLI for single file and --all directory mode
# - throughput conversion to instr/s using picosecond totals
#
# Recommended additional top-level functions are scaffolded below.


def format_project3_style_report(file_name, instructions, single_metrics, pipeline_metrics):
    """
    Format output in the project3-style layout used by the analyzer prototype.
    """
    from person3_single_cycle import classify_instruction, DEFAULT_TIMING_PS

    def metric_get(metrics, *keys, default=0.0):
        for key in keys:
            if key in metrics and metrics[key] is not None:
                return metrics[key]
        return default

    counts = {"lw": 0, "sw": 0, "R": 0, "beq": 0, "other": 0}
    for instr in instructions:
        cat = classify_instruction(instr)
        if cat not in counts:
            cat = "other"
        counts[cat] += 1

    total = len(instructions)

    # Match prototype non-pipeline mode: sum per-instruction latencies.
    nonpipe_total_time_ps = 0.0
    for instr in instructions:
        cat = classify_instruction(instr)
        if cat not in DEFAULT_TIMING_PS:
            cat = "other"
        nonpipe_total_time_ps += DEFAULT_TIMING_PS[cat]
    nonpipe_latency_ps = (nonpipe_total_time_ps / total) if total else 0.0

    single_clock_ps = metric_get(
        single_metrics,
        "single_cycle_clock_ps",
        "clock_period_ps",
        default=max(DEFAULT_TIMING_PS["lw"], DEFAULT_TIMING_PS["sw"], DEFAULT_TIMING_PS["R"], DEFAULT_TIMING_PS["beq"]),
    )

    pipeline_total_time_ps = metric_get(pipeline_metrics, "total_time_ps", "latency", default=0.0)
    pipeline_latency_ps = metric_get(pipeline_metrics, "latency_ps", "avg_latency_ps", default=0.0)
    pipelined_clock_ps = metric_get(pipeline_metrics, "pipelined_clock_ps", default=single_clock_ps / 5.0 if single_clock_ps else 0.0)

    nonpipe_throughput = _throughput_instr_per_sec(total, nonpipe_total_time_ps)
    pipe_throughput = _throughput_instr_per_sec(total, pipeline_total_time_ps)

    lines = []
    lines.append(f"Processed 1 file(s): ['{file_name}']")
    lines.append("")
    lines.append("Instruction counts:")
    lines.append(
        f"lw={counts['lw']}, sw={counts['sw']}, R-type={counts['R']}, beq={counts['beq']}"
    )
    lines.append(f"Total instructions: {total}")
    lines.append("")

    lines.append("=== Non-pipeline mode ===")
    lines.append("Per-instruction execution time (ps):")
    lines.append(f"  lw: {DEFAULT_TIMING_PS['lw']}")
    lines.append(f"  sw: {DEFAULT_TIMING_PS['sw']}")
    lines.append(f"  R-type: {DEFAULT_TIMING_PS['R']}")
    lines.append(f"  beq: {DEFAULT_TIMING_PS['beq']}")
    lines.append("Average CPI: 1.000")
    lines.append(f"Total execution time: {nonpipe_total_time_ps:.0f} ps")
    lines.append(f"Average instruction latency: {nonpipe_latency_ps:.3f} ps")
    lines.append(f"Average throughput: {nonpipe_throughput:.3f} instr/s")
    lines.append("")

    lines.append("=== Pipeline mode ===")
    lines.append(f"Single-cycle reference clock: {single_clock_ps:.0f} ps")
    lines.append(f"\tPipelined clock: {pipelined_clock_ps:.0f} ps")
    lines.append("")
    lines.append(f"\tStall cycles: {pipeline_metrics.get('stall_cycles', 0)}")
    lines.append(f"\tAverage CPI: {pipeline_metrics.get('cpi', 0.0):.3f}")
    lines.append(f"\tTotal execution time: {pipeline_total_time_ps:.0f} ps")
    lines.append(f"\tAverage instruction latency: {pipeline_latency_ps:.3f} ps")
    lines.append(f"\tAverage throughput: {pipe_throughput:.3f} instr/s")

    return "\n".join(lines)


def analyze_file(file_path):
    """Parse one file and return project3-style report + both metrics dicts."""
    from person1_parser import parse_program as real_parse_program
    from person3_single_cycle import (
        run_single_cycle as real_run_single_cycle,
        run_single_cycle_analyzer as real_run_single_cycle_analyzer,
    )
    from person4_pipeline import run_pipeline as real_run_pipeline

    source = Path(file_path).read_text(encoding="utf-8")
    instructions = real_parse_program(source)

    # Prefer analyzer mode (prototype behavior) to avoid requiring full
    # simulator execution for reporting-only workflows.
    try:
        analysis = real_run_single_cycle_analyzer(instructions)
        single_log = []
        single_metrics = {
            "total_instructions": analysis.get("total_instructions", len(instructions)),
            "total_cycles": analysis.get("total_cycles", len(instructions)),
            "stall_cycles": 0,
            "flush_cycles": 0,
            "cpi": analysis.get("cpi", 1.0),
            "latency": float(analysis.get("total_time_ps", 0.0)),
            "throughput": float(analysis.get("throughput_instr_per_ps", 0.0)),
            "total_time_ps": float(analysis.get("total_time_ps", 0.0)),
            "latency_ps": float(analysis.get("avg_latency_ps", 0.0)),
            "single_cycle_clock_ps": float(analysis.get("clock_period_ps", 0.0)),
        }
    except Exception:
        # Fallback for compatibility if analyzer helper is unavailable.
        _, single_log, single_metrics = real_run_single_cycle(instructions)

    try:
        _, pipeline_log, pipeline_metrics = real_run_pipeline(instructions)
    except Exception:
        pipeline_log = []
        pipeline_metrics = _pipeline_metrics_fallback(instructions, single_metrics)

    # Ensure basic fields exist even if upstream modules only return partial metrics.
    single_fallback = compute_metrics(single_log, len(instructions), 1.0)
    pipe_fallback = compute_metrics(pipeline_log, len(instructions), 1.0)
    for key, value in single_fallback.items():
        single_metrics.setdefault(key, value)
    for key, value in pipe_fallback.items():
        pipeline_metrics.setdefault(key, value)

    report = format_project3_style_report(
        Path(file_path).name,
        instructions,
        single_metrics,
        pipeline_metrics,
    )
    return report, single_metrics, pipeline_metrics


def discover_input_files(target_dir):
    """Return sorted .asm files from target directory."""
    root = Path(target_dir)
    if not root.exists():
        return []

    files = []
    for p in sorted(root.iterdir()):
        if not p.is_file():
            continue
        if p.suffix.lower() == ".asm":
            files.append(str(p))
    return files


def run_cli(argv=None):
    """CLI entry point for single-file and all-files analyzer execution."""
    parser = argparse.ArgumentParser(description="MIPS Pipelined Performance Analyzer")
    parser.add_argument("input", nargs="?", help="Input .asm file path")
    parser.add_argument("--all", action="store_true", dest="all_files", help="Analyze all .asm files in target directory")
    parser.add_argument("--dir", default=".", help="Directory used with --all (default: current directory)")

    args = parser.parse_args(argv)

    if args.all_files:
        file_list = discover_input_files(args.dir)
    elif args.input:
        file_list = [args.input]
    else:
        parser.error("Provide an input file or use --all.")

    if not file_list:
        print("Processed 0 file(s)")
        return 0

    if len(file_list) == 1:
        report, _, _ = analyze_file(file_list[0])
        print(report)
        return 0

    print(f"Processed {len(file_list)} file(s): {[Path(p).name for p in file_list]}")
    print("")
    for idx, file_path in enumerate(file_list):
        report, _, _ = analyze_file(file_path)
        print(report)
        if idx != len(file_list) - 1:
            print("\n" + "-" * 72 + "\n")

    return 0


def _throughput_instr_per_sec(total_instructions, total_time_ps):
    """Convert instruction/time totals into instructions per second."""
    if total_time_ps <= 0:
        return 0.0
    return total_instructions / (total_time_ps * 1e-12)


def _read_regs(instr):
    op = instr.get("op", "")
    rs = instr.get("rs", 0)
    rt = instr.get("rt", 0)

    if op in {"add", "sub", "and", "or", "slt", "beq", "bne"}:
        return {rs, rt}
    if op in {"addi", "lw", "sw"}:
        return {rs}
    return set()


def _write_reg(instr):
    op = instr.get("op", "")
    if op in {"add", "sub", "and", "or", "slt"}:
        return instr.get("rd", 0)
    if op in {"addi", "lw"}:
        return instr.get("rt", 0)
    return 0


def _analyze_hazards_fallback(instructions):
    raw_hazards = 0
    load_use_hazards = 0
    branch_instructions = 0

    for i in range(1, len(instructions)):
        prev_instr = instructions[i - 1]
        curr_instr = instructions[i]
        if curr_instr.get("op") in {"beq", "bne"}:
            branch_instructions += 1

        prev_write = _write_reg(prev_instr)
        curr_reads = _read_regs(curr_instr)
        if prev_write != 0 and prev_write in curr_reads:
            raw_hazards += 1
            if prev_instr.get("op") == "lw":
                load_use_hazards += 1

    return {
        "raw_hazards": raw_hazards,
        "load_use_hazards": load_use_hazards,
        "branch_instructions": branch_instructions,
        "stall_cycles": load_use_hazards,
    }


def _pipeline_metrics_fallback(instructions, single_metrics):
    n = len(instructions)
    single_clock_ps = single_metrics.get("single_cycle_clock_ps", 0.0)
    pipelined_clock_ps = (single_clock_ps / 5.0) if single_clock_ps else 0.0

    hazards = _analyze_hazards_fallback(instructions)
    stall_cycles = int(hazards["stall_cycles"])

    base_cycles = (n + 4) if n else 0
    total_cycles = base_cycles + stall_cycles

    cpi = (total_cycles / n) if n else 0.0
    total_time_ps = total_cycles * pipelined_clock_ps
    latency_ps = (total_time_ps / n) if n else 0.0
    throughput_per_ps = (1.0 / latency_ps) if latency_ps else 0.0

    return {
        "total_instructions": n,
        "total_cycles": total_cycles,
        "stall_cycles": stall_cycles,
        "flush_cycles": 0,
        "cpi": cpi,
        "latency": total_time_ps,
        "throughput": throughput_per_ps,
        "single_cycle_clock_ps": single_clock_ps,
        "pipelined_clock_ps": pipelined_clock_ps,
        "total_time_ps": total_time_ps,
        "latency_ps": latency_ps,
        "throughput_per_ps": throughput_per_ps,
        "hazards": hazards,
        "pipelined_cycles": total_cycles,
    }

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

# CURRENT FUNCTION: shared simulator test programs.
# PROTOTYPE NOTE: keep for simulator validation; analyzer CLI should consume
# professor-provided files directly.
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

# CURRENT FUNCTION: computes metrics from simulator logs.
# PROTOTYPE NOTE: analytical mode may bypass logs and compute metrics directly
# from counts and timing constants.
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


# CURRENT FUNCTION: compares simulator outputs.
# PROTOTYPE NOTE: retain for compatibility; analyzer branch may compare direct
# analytical metric dictionaries instead.
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


# CURRENT FUNCTION: simulator-style table printer.
# PROTOTYPE CHANGE: add project3-style print path for grading output parity.
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
    raise SystemExit(run_cli())