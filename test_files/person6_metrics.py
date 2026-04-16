"""
person6_metrics.py — Analyzer Metrics, Reporting, and CLI
ECE 5367 Final Project: Pipelined Performance Analyzer
"""

from pathlib import Path
import argparse

from common import make_metrics
from person1_parser import parse_program
from person3_single_cycle import run_single_cycle, classify_instruction, DEFAULT_TIMING_PS
from person4_pipeline import run_pipeline


def compute_metrics(log, total_instructions, clock_period_ps=1.0):
    m = make_metrics()
    if not log or total_instructions == 0:
        return m

    total_cycles = max(entry["cycle"] for entry in log) + 1
    m["total_instructions"] = total_instructions
    m["total_cycles"] = total_cycles
    m["stall_cycles"] = sum(1 for entry in log if entry.get("event") == "stall")
    m["flush_cycles"] = sum(1 for entry in log if entry.get("event") == "flush")
    m["cpi"] = total_cycles / total_instructions
    m["latency"] = total_cycles * clock_period_ps
    m["throughput"] = total_instructions / total_cycles
    return m


def compare_simulators(single_log, pipeline_log, n_instructions, clock_period_ps=1.0):
    single_metrics = compute_metrics(single_log, n_instructions, clock_period_ps)
    pipeline_metrics = compute_metrics(pipeline_log, n_instructions, clock_period_ps)

    sc_cycles = single_metrics.get("total_cycles", 0)
    pp_cycles = pipeline_metrics.get("total_cycles", 0)
    speedup = (sc_cycles / pp_cycles) if pp_cycles else 0.0

    return {
        "single_cycle": single_metrics,
        "pipelined": pipeline_metrics,
        "speedup": speedup,
        "cpi_overhead": pipeline_metrics.get("cpi", 0.0) - 1.0,
    }


def _instruction_breakdown(instructions):
    counts = {"lw": 0, "sw": 0, "R": 0, "beq": 0, "other": 0}
    for instr in instructions:
        counts[classify_instruction(instr)] += 1
    return counts


def _throughput_instr_per_sec(total_instructions, total_time_ps):
    if total_time_ps <= 0:
        return 0.0
    return total_instructions / (total_time_ps * 1e-12)


def _format_project3_style(file_name, instructions, single_metrics, pipeline_metrics):
    counts = _instruction_breakdown(instructions)
    total = len(instructions)

    nonpipe_throughput = _throughput_instr_per_sec(total, single_metrics["total_time_ps"])
    pipe_throughput = _throughput_instr_per_sec(total, pipeline_metrics["total_time_ps"])

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
    lines.append(f"Average CPI: {single_metrics['cpi']:.3f}")
    lines.append(f"Total execution time: {single_metrics['total_time_ps']:.0f} ps")
    lines.append(f"Average instruction latency: {single_metrics['latency_ps']:.3f} ps")
    lines.append(f"Average throughput: {nonpipe_throughput:.3f} instr/s")
    lines.append("")

    lines.append("=== Pipeline mode ===")
    lines.append(f"Single-cycle reference clock: {single_metrics['single_cycle_clock_ps']:.0f} ps")
    lines.append(f"\tPipelined clock: {pipeline_metrics['pipelined_clock_ps']:.0f} ps")
    lines.append("")
    lines.append(f"\tStall cycles: {pipeline_metrics['stall_cycles']}")
    lines.append(f"\tAverage CPI: {pipeline_metrics['cpi']:.3f}")
    lines.append(f"\tTotal execution time: {pipeline_metrics['total_time_ps']:.0f} ps")
    lines.append(f"\tAverage instruction latency: {pipeline_metrics['latency_ps']:.3f} ps")
    lines.append(f"\tAverage throughput: {pipe_throughput:.3f} instr/s")

    return "\n".join(lines)


def analyze_file(file_path):
    source = Path(file_path).read_text(encoding="utf-8")
    instructions = parse_program(source)

    _, _, single_metrics = run_single_cycle(instructions)
    _, _, pipeline_metrics = run_pipeline(instructions)

    report = _format_project3_style(Path(file_path).name, instructions, single_metrics, pipeline_metrics)
    return report, single_metrics, pipeline_metrics


def _discover_input_files(target_dir):
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
    parser = argparse.ArgumentParser(description="MIPS Pipelined Performance Analyzer")
    parser.add_argument("input", nargs="?", help="Input .asm file path")
    parser.add_argument("--all", action="store_true", dest="all_files", help="Analyze all .asm files in target directory")
    parser.add_argument("--dir", default=".", help="Directory used with --all (default: current directory)")

    args = parser.parse_args(argv)

    if args.all_files:
        file_list = _discover_input_files(args.dir)
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


def print_report(comparison, program_name="test"):
    print(f"Program: {program_name}")
    print(f"Speedup: {comparison.get('speedup', 0.0):.6f}x")


if __name__ == "__main__":
    raise SystemExit(run_cli())
