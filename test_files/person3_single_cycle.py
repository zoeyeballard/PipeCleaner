"""
person3_single_cycle.py — Single-Cycle Performance Analyzer
ECE 5367 Final Project: Pipelined Performance Analyzer
"""

from collections import Counter

from common import make_cpu_state, make_log_entry, make_metrics


DEFAULT_TIMING_PS = {
    "lw": 800,
    "sw": 700,
    "R": 600,
    "beq": 500,
    "other": 600,
}


def classify_instruction(instr):
    op = instr.get("op", "").lower()
    if op == "lw":
        return "lw"
    if op == "sw":
        return "sw"
    if op == "beq":
        return "beq"
    if instr.get("type") == "R":
        return "R"
    return "other"


def run_single_cycle(instructions, initial_state=None, timing_ps=None):
    timing = dict(DEFAULT_TIMING_PS)
    if timing_ps:
        timing.update(timing_ps)

    cpu_state = make_cpu_state() if initial_state is None else initial_state
    counts = Counter()
    log = []

    total_time_ps = 0
    for cycle, instr in enumerate(instructions):
        category = classify_instruction(instr)
        counts[category] += 1
        step_time_ps = timing.get(category, timing["other"])
        total_time_ps += step_time_ps
        log.append(make_log_entry(cycle=cycle, stage="SC", instruction=instr, event=None))

    n = len(instructions)
    avg_latency_ps = (total_time_ps / n) if n else 0.0
    throughput_per_ps = (1.0 / avg_latency_ps) if avg_latency_ps else 0.0

    metrics = make_metrics()
    metrics["instruction_counts"] = dict(counts)
    metrics["timing_ps"] = timing
    metrics["total_instructions"] = n
    metrics["total_cycles"] = n
    metrics["stall_cycles"] = 0
    metrics["flush_cycles"] = 0
    metrics["cpi"] = 1.0 if n else 0.0
    metrics["total_time_ps"] = float(total_time_ps)
    metrics["latency_ps"] = float(avg_latency_ps)
    metrics["throughput_per_ps"] = float(throughput_per_ps)
    metrics["single_cycle_clock_ps"] = max(
        timing["lw"], timing["sw"], timing["R"], timing["beq"]
    )

    # Keep compatibility with generic metrics fields.
    metrics["latency"] = metrics["total_time_ps"]
    metrics["throughput"] = metrics["throughput_per_ps"]
    metrics["single_cycle_cycles"] = n

    return cpu_state, log, metrics


if __name__ == "__main__":
    from person1_parser import parse_program

    sample = """
    addi $t0, $zero, 5
    lw   $t1, 0($zero)
    add  $t2, $t0, $t1
    beq  $t0, $t1, done
    done: sw $t2, 4($zero)
    """

    instructions = parse_program(sample)
    _, _, m = run_single_cycle(instructions)
    print("Single-cycle analyzer self-test")
    print(f"Instructions: {m['total_instructions']}")
    print(f"Counts: {m['instruction_counts']}")
    print(f"Total time: {m['total_time_ps']} ps")
