"""
person3_single_cycle.py — Single-Cycle MIPS Simulator
ECE 5367 Final Project: Pipelined Performance Analyzer
Owner: Gyan

RESPONSIBILITY:
    Wire together the parser (Person 1) and ALU (Person 2) into a
    single-cycle execution loop. Each instruction completes in exactly
    1 cycle. Returns an execution log and final CPU state.

DEPENDENCY STRATEGY:
    Import from person1_parser and person2_alu.
    If those aren't ready yet, use the STUBS at the bottom of this file
    by toggling USE_STUBS = True.

INTERFACE CONTRACT (do not change signatures):
    run_single_cycle(instructions, initial_state=None) -> (cpu_state, log, metrics)
    classify_instruction(instr) -> str
    run_single_cycle_analyzer(instructions, timing_ps=None) -> dict
"""

import copy
from common import (
    make_cpu_state,
    make_metrics,
    make_log_entry,
    make_instruction,
)

# ── Toggle this while Person 1 & 2 are still building ──
USE_STUBS = False

if not USE_STUBS:
    from person1_parser import parse_program
    from rolandoU_alu import alu_execute, register_read, register_write, sign_extend
else:
    # ── LOCAL STUBS — delete when real modules are ready ──
    def parse_program(source):
        """Stub: returns a hardcoded tiny program for testing"""
        return [
            make_instruction("addi", "I", rs=0, rt=8,  imm=10, raw="addi $t0,$zero,10"),
            make_instruction("addi", "I", rs=0, rt=9,  imm=20, raw="addi $t1,$zero,20"),
            make_instruction("add",  "R", rs=8, rt=9, rd=10,   raw="add $t2,$t0,$t1"),
        ]

    def alu_execute(op, a, b):
        ops = {
            "add": a + b, "sub": a - b,
            "and": a & b, "or":  a | b,
            "slt": int(a < b),
        }
        result = ops.get(op, 0)
        return result, (result == 0)

    def register_read(cpu_state, rs, rt):
        return cpu_state["registers"][rs], cpu_state["registers"][rt]

    def register_write(cpu_state, rd, value):
        if rd != 0:
            cpu_state["registers"][rd] = value
        return cpu_state

    def sign_extend(imm, bits=16):
        if imm >= (1 << (bits - 1)):
            imm -= (1 << bits)
        return imm


# ─────────────────────────────────────────────
# TIMING CONSTANTS
# ─────────────────────────────────────────────

# Per-instruction-type latency in picoseconds for the analytical mode.
# The single-cycle clock period is the MAX of these values, because the
# critical path must accommodate the slowest instruction class.
DEFAULT_TIMING_PS = {
    "lw":    800,   # IF + ID + EX (add) + MEM read + WB  — longest path
    "sw":    700,   # IF + ID + EX (add) + MEM write       — no WB reg write
    "R":     600,   # IF + ID + EX + WB                    — no memory stage
    "beq":   500,   # IF + ID + EX (sub) + branch logic    — no WB
    "other": 600,   # catch-all (addi, j, bne, nop, …)
}


# ─────────────────────────────────────────────
# CLASSIFY INSTRUCTION
# ─────────────────────────────────────────────

def classify_instruction(instr: dict) -> str:
    """
    Map an instruction dict to one of the timing categories used by the analyzer.

    Categories match the keys of DEFAULT_TIMING_PS:
        "lw"    — load word
        "sw"    — store word
        "R"     — any R-type instruction (add, sub, and, or, slt, nop)
        "beq"   — branch if equal (and bne, treated identically for timing)
        "other" — everything else (addi, j, …)

    Args:
        instr (dict): Instruction dict produced by make_instruction()

    Returns:
        str: One of "lw", "sw", "R", "beq", "other"
    """
    op = instr.get("op", "nop")

    if op == "lw":
        return "lw"
    if op == "sw":
        return "sw"
    if instr.get("type") == "R":
        return "R"
    if op in ("beq", "bne"):
        return "beq"
    return "other"


# ─────────────────────────────────────────────
# ANALYTICAL (NON-SIMULATION) ANALYZER
# ─────────────────────────────────────────────

def run_single_cycle_analyzer(instructions: list, timing_ps: dict = None) -> dict:
    """
    Compute single-cycle performance metrics analytically — without executing
    the program cycle by cycle.

    In a single-cycle implementation every instruction uses the same clock
    period, which must be long enough for the *slowest* instruction class
    (i.e. the critical-path latency).  All other performance numbers follow
    from that constraint.

    Args:
        instructions (list[dict]): Parsed instruction list from Person 1.
        timing_ps    (dict):       Optional override for per-type latencies in
                                   picoseconds. Falls back to DEFAULT_TIMING_PS.

    Returns:
        dict with keys:
            instruction_counts      (dict)  — {category: count} for each type
            total_instructions      (int)   — total number of instructions
            clock_period_ps         (int)   — single-cycle clock = max stage time
            total_time_ps           (int)   — clock_period_ps * total_instructions
            total_cycles            (int)   — same as total_instructions (CPI = 1)
            cpi                     (float) — always 1.0 for single-cycle
            avg_latency_ps          (float) — total_time_ps / total_instructions
            throughput_instr_per_ps (float) — instructions per picosecond
            timing_ps               (dict)  — the timing table actually used
    """
    timing = timing_ps if timing_ps is not None else DEFAULT_TIMING_PS

    # ── Count instructions by category ───────────────────────────────────────
    counts: dict = {cat: 0 for cat in timing}
    for instr in instructions:
        cat = classify_instruction(instr)
        counts[cat] = counts.get(cat, 0) + 1

    total_instructions = len(instructions)

    # ── Derive clock period ───────────────────────────────────────────────────
    # Single-cycle: one global clock period = worst-case (max) instruction time.
    # Every instruction — fast or slow — waits for this period to expire.
    clock_period_ps = max(timing.values()) if timing else 0

    # ── Aggregate timing ──────────────────────────────────────────────────────
    total_cycles    = total_instructions          # CPI = 1.0 always
    total_time_ps   = clock_period_ps * total_instructions

    cpi             = 1.0
    avg_latency_ps  = float(total_time_ps / total_instructions) if total_instructions else 0.0
    throughput      = (1.0 / clock_period_ps) if clock_period_ps else 0.0  # instr/ps

    return {
        "instruction_counts":       counts,
        "total_instructions":       total_instructions,
        "clock_period_ps":          clock_period_ps,
        "total_time_ps":            total_time_ps,
        "total_cycles":             total_cycles,
        "cpi":                      cpi,
        "avg_latency_ps":           avg_latency_ps,
        "throughput_instr_per_ps":  throughput,
        "timing_ps":                timing,
    }


# ─────────────────────────────────────────────
# PUBLIC API — SIMULATION MODE
# ─────────────────────────────────────────────

def run_single_cycle(instructions: list, initial_state: dict = None) -> tuple:
    """
    Execute a MIPS program in single-cycle mode.
    Every instruction takes exactly 1 cycle.

    Args:
        instructions  (list[dict]): Parsed instruction list from Person 1
        initial_state (dict):       Optional pre-loaded cpu_state; fresh if None

    Returns:
        tuple: (
            cpu_state (dict)  — final register/memory state,
            log       (list)  — list of make_log_entry() dicts (one per instruction),
            metrics   (dict)  — populated make_metrics() dict
        )

    Flow per cycle:
        1. Fetch instruction at cpu_state["pc"]
        2. Decode: read registers, sign-extend immediate
        3. Execute: call alu_execute()
        4. Memory: handle LW / SW
        5. Write-back: update destination register
        6. Advance PC (or branch)
    """
    cpu_state = copy.deepcopy(initial_state) if initial_state else make_cpu_state()
    log = []
    cycle = 0

    while True:
        pc = cpu_state["pc"]

        # ── 1. Fetch ──────────────────────────────────────────
        instr = _fetch(instructions, pc)

        if instr["op"] == "nop" and pc >= len(instructions):
            break

        # ── 2. Decode ─────────────────────────────────────────
        rs_val, rt_val = register_read(cpu_state, instr["rs"], instr["rt"])
        imm = sign_extend(instr["imm"])

        # ── 3. Execute ────────────────────────────────────────
        op     = instr["op"]
        alu_b  = imm if instr["type"] == "I" else rt_val
        alu_op = "add" if op == "addi" else op

        if op in ("beq", "bne"):
            alu_op = "sub"
        if op in ("lw", "sw"):
            alu_op = "add"
        if op in ("nop", "j"):
            alu_result, zero_flag = 0, False
        else:
            alu_result, zero_flag = alu_execute(alu_op, rs_val, alu_b)

        # ── 4. Memory ─────────────────────────────────────────
        mem_result = _memory_access(cpu_state, instr, alu_result, rt_val)

        # ── 5. Write-back ─────────────────────────────────────
        if instr["type"] == "R" and op not in ("nop",):
            register_write(cpu_state, instr["rd"], alu_result)
        elif op == "addi":
            register_write(cpu_state, instr["rt"], alu_result)
        elif op == "lw":
            register_write(cpu_state, instr["rt"], mem_result)

        # ── Log this cycle ────────────────────────────────────
        log.append(make_log_entry(
            cycle=cycle,
            stage="WB",
            instruction=instr,
            event=None,
        ))

        # ── 6. Advance PC ─────────────────────────────────────
        cpu_state["pc"] = _compute_next_pc(pc, instr, zero_flag, alu_result)
        cycle += 1

        if cycle > 10_000:
            raise RuntimeError("Exceeded 10,000 cycles — possible infinite loop in program.")

    # ── Build metrics ─────────────────────────────────────────
    # Route through the analytical path so simulation and analyzer modes
    # report consistent clock period / latency / throughput numbers.
    analyzer_metrics = run_single_cycle_analyzer(
        [entry["instruction"] for entry in log]
    )

    metrics = make_metrics()
    metrics["total_instructions"]  = len(log)
    metrics["total_cycles"]        = cycle
    metrics["stall_cycles"]        = 0
    metrics["flush_cycles"]        = 0
    metrics["cpi"]                 = (cycle / len(log)) if log else 0.0
    metrics["latency"]             = float(analyzer_metrics["total_time_ps"])
    metrics["throughput"]          = analyzer_metrics["throughput_instr_per_ps"]
    metrics["single_cycle_cycles"] = cycle

    return cpu_state, log, metrics


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _fetch(instructions: list, pc: int) -> dict:
    """Return instruction at index pc, or a NOP if out of bounds."""
    if 0 <= pc < len(instructions):
        return instructions[pc]
    return make_instruction("nop", "R")


def _memory_access(cpu_state: dict, instr: dict, alu_result: int, write_data: int) -> int:
    """
    Handle LW and SW memory operations.

    For LW: reads from cpu_state["memory"] at the word address computed
            by the ALU (base + sign-extended offset). Returns the value
            read so the caller can write it to a register.

    For SW: writes write_data (the value of rt) into memory at alu_result.
            Returns alu_result (unused by write-back stage for SW).

    For all other instructions: a no-op; returns alu_result unchanged.
    """
    op = instr["op"]
    if op == "lw":
        return cpu_state["memory"].get(alu_result, 0)
    elif op == "sw":
        cpu_state["memory"][alu_result] = write_data
        return alu_result
    return alu_result


def _compute_next_pc(pc: int, instr: dict, zero_flag: bool, alu_result: int) -> int:
    """
    Determine the next PC value after this instruction.

    Rules:
        BEQ: branch to pc + 1 + imm  if zero_flag is True  (rs == rt)
        BNE: branch to pc + 1 + imm  if zero_flag is False (rs != rt)
        J:   jump  to instr["imm"]   unconditionally
        *:   sequential, pc + 1
    """
    op         = instr["op"]
    sequential = pc + 1

    if op == "beq":
        return sequential + instr["imm"] if zero_flag     else sequential
    if op == "bne":
        return sequential + instr["imm"] if not zero_flag else sequential
    if op == "j":
        return instr["imm"]
    return sequential


# ─────────────────────────────────────────────
# QUICK SELF-TEST (run: python person3_single_cycle.py)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Running with {'STUBS' if USE_STUBS else 'real modules'}...\n")

    program_text = """
    addi $t0, $zero, 10
    addi $t1, $zero, 20
    add  $t2, $t0, $t1
    """

    instructions = parse_program(program_text)

    # ── Simulation mode ───────────────────────────────────────
    print("=== SIMULATION MODE ===")
    try:
        final_state, log, metrics = run_single_cycle(instructions)
        print("Final register state:")
        for i, val in enumerate(final_state["registers"]):
            if val != 0:
                print(f"  $r{i} = {val}")
        print(f"\nMetrics: {metrics}")
        print(f"\nExecution log ({len(log)} entries):")
        for entry in log:
            print(f"  Cycle {entry['cycle']}: {entry['instruction']['raw']}")
    except Exception as e:
        print(f"[ERROR] {e}")

    # ── Analytical mode ───────────────────────────────────────
    print("\n=== ANALYZER MODE ===")
    try:
        analysis = run_single_cycle_analyzer(instructions)
        print(f"  Instruction counts : {analysis['instruction_counts']}")
        print(f"  Total instructions : {analysis['total_instructions']}")
        print(f"  Clock period       : {analysis['clock_period_ps']} ps")
        print(f"  Total time         : {analysis['total_time_ps']} ps")
        print(f"  CPI                : {analysis['cpi']}")
        print(f"  Avg latency        : {analysis['avg_latency_ps']:.1f} ps")
        print(f"  Throughput         : {analysis['throughput_instr_per_ps']:.6f} instr/ps")
    except Exception as e:
        print(f"[ERROR] {e}")

    # ── classify_instruction spot-check ──────────────────────
    print("\n=== CLASSIFY CHECK ===")
    tests = [
        make_instruction("lw",   "I", raw="lw $t0, 0($s0)"),
        make_instruction("sw",   "I", raw="sw $t1, 4($s0)"),
        make_instruction("add",  "R", raw="add $t2,$t0,$t1"),
        make_instruction("beq",  "I", raw="beq $t0,$t1,label"),
        make_instruction("addi", "I", raw="addi $t0,$zero,5"),
        make_instruction("j",    "J", raw="j loop"),
    ]
    for t in tests:
        print(f"  {t['raw']:30s} -> '{classify_instruction(t)}'")