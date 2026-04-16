"""
person4_pipeline.py — Pipelined Performance Analyzer
ECE 5367 Final Project: Pipelined Performance Analyzer
"""

from common import make_cpu_state, make_log_entry, make_metrics
from person3_single_cycle import DEFAULT_TIMING_PS
from person5_hazard import analyze_hazards


PIPELINE_STAGES = 5


def stage_IF(cpu_state, instructions, hazard_signals):
    return {"instruction": None, "pc_plus_4": cpu_state.get("pc", 0) + 1}


def stage_ID(IF_ID, cpu_state, hazard_signals):
    return {"instruction": IF_ID.get("instruction")}


def stage_EX(ID_EX, hazard_signals, EX_MEM, MEM_WB):
    return {"instruction": ID_EX.get("instruction")}


def stage_MEM(EX_MEM, cpu_state):
    return {"instruction": EX_MEM.get("instruction")}, cpu_state


def stage_WB(MEM_WB, cpu_state):
    return cpu_state


def run_pipeline(instructions, initial_state=None, timing_ps=None, assumed_branch_penalty=0):
    timing = dict(DEFAULT_TIMING_PS)
    if timing_ps:
        timing.update(timing_ps)

    cpu_state = make_cpu_state() if initial_state is None else initial_state
    n = len(instructions)

    single_cycle_clock_ps = max(
        timing["lw"], timing["sw"], timing["R"], timing["beq"]
    )
    pipelined_clock_ps = single_cycle_clock_ps / PIPELINE_STAGES

    hazard_stats = analyze_hazards(instructions)
    stall_cycles = hazard_stats["stall_cycles"]
    branch_cycles = hazard_stats["branch_instructions"] * max(assumed_branch_penalty, 0)

    base_cycles = (n + PIPELINE_STAGES - 1) if n else 0
    total_cycles = base_cycles + stall_cycles + branch_cycles

    cpi = (total_cycles / n) if n else 0.0
    total_time_ps = total_cycles * pipelined_clock_ps
    avg_latency_ps = (total_time_ps / n) if n else 0.0
    throughput_per_ps = (1.0 / avg_latency_ps) if avg_latency_ps else 0.0

    log = [make_log_entry(cycle=i, stage="PIPE", instruction=instr, event=None) for i, instr in enumerate(instructions)]

    metrics = make_metrics()
    metrics["total_instructions"] = n
    metrics["total_cycles"] = int(total_cycles)
    metrics["stall_cycles"] = int(stall_cycles + branch_cycles)
    metrics["flush_cycles"] = int(branch_cycles)
    metrics["cpi"] = float(cpi)
    metrics["latency"] = float(total_time_ps)
    metrics["throughput"] = float(throughput_per_ps)

    metrics["single_cycle_clock_ps"] = float(single_cycle_clock_ps)
    metrics["pipelined_clock_ps"] = float(pipelined_clock_ps)
    metrics["total_time_ps"] = float(total_time_ps)
    metrics["latency_ps"] = float(avg_latency_ps)
    metrics["throughput_per_ps"] = float(throughput_per_ps)
    metrics["hazards"] = hazard_stats
    metrics["pipelined_cycles"] = int(total_cycles)

    return cpu_state, log, metrics


if __name__ == "__main__":
    from person1_parser import parse_program

    sample = """
    addi $t0, $zero, 1
    lw   $t1, 0($zero)
    add  $t2, $t1, $t0
    beq  $t2, $t0, done
    done: sw $t2, 4($zero)
    """

    instructions = parse_program(sample)
    _, _, m = run_pipeline(instructions)
    print("Pipeline analyzer self-test")
    print(f"Total cycles: {m['total_cycles']}")
    print(f"CPI: {m['cpi']:.3f}")
    print(f"Clock: {m['pipelined_clock_ps']} ps")
