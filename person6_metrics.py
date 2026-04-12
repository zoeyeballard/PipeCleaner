"""
person6_metrics.py — Performance Metrics Engine & Test Suite
ECE 5367 Final Project: Pipelined Performance Analyzer
Owner: Person 6

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
    # TODO: Person 6 implements this
    raise NotImplementedError("Person 6: implement compute_metrics()")


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
    # TODO: Person 6 implements this
    raise NotImplementedError("Person 6: implement compare_simulators()")


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
    # TODO: Person 6 implements this
    raise NotImplementedError("Person 6: implement print_report()")


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