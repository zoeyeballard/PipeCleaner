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

TESTING:
    Run this file directly: python person3_single_cycle.py
"""

import copy
from common import (
    make_cpu_state,
    make_metrics,
    make_log_entry,
    make_instruction,
)

# -----------------------------------------------------------------------------
# PROTOTYPE MIGRATION NOTES (main branch scaffold only)
# -----------------------------------------------------------------------------
# This file currently performs full single-cycle simulation.
# To match the prototype analyzer branch, add an analytical mode that computes:
# - instruction type counts
# - total non-pipeline execution time in picoseconds
# - average latency and throughput
# - single-cycle reference clock (max stage time)
#
# Recommended scaffold additions:
# - DEFAULT_TIMING_PS lookup table
# - classify_instruction(...) helper
# - run_single_cycle_analyzer(...) path separate from simulation loop


# TODO (prototype parity): use configurable per-type timing constants.
DEFAULT_TIMING_PS = {
    "lw": 800,
    "sw": 700,
    "R": 600,
    "beq": 500,
    "other": 600,
}


# TODO (prototype parity): classify each instruction into reporting categories.
def classify_instruction(instr):
    """Scaffold: map instruction dict -> one of lw/sw/R/beq/other."""
    raise NotImplementedError("Scaffold only: implement classify_instruction for analyzer parity")


# TODO (prototype parity): analytical non-pipeline metrics path.
def run_single_cycle_analyzer(instructions, timing_ps=None):
    """Scaffold: compute timing/count metrics without cycle-accurate execution."""
    raise NotImplementedError("Scaffold only: implement run_single_cycle_analyzer for prototype parity")

# ── Toggle this while Person 1 & 2 are still building ──
USE_STUBS = True

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
# PUBLIC API
# ─────────────────────────────────────────────

# CURRENT FUNCTION: full single-cycle simulator execution loop.
# PROTOTYPE CHANGE: either keep this as compatibility mode or route to
# run_single_cycle_analyzer(...) when analyzer mode is selected.
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
    # Initialise CPU state
    cpu_state = copy.deepcopy(initial_state) if initial_state else make_cpu_state()
    log = []
    cycle = 0

    while True:
        pc = cpu_state["pc"]

        # ── 1. Fetch ──────────────────────────────────────────
        instr = _fetch(instructions, pc)

        # Stop when we fall off the end of the program
        if instr["op"] == "nop" and pc >= len(instructions):
            break

        # ── 2. Decode ─────────────────────────────────────────
        rs_val, rt_val = register_read(cpu_state, instr["rs"], instr["rt"])
        imm = sign_extend(instr["imm"])  # safe for R-type (imm=0)

        # ── 3. Execute ────────────────────────────────────────
        # Determine ALU operation and operands
        op = instr["op"]

        # For I-type arithmetic/memory, second ALU input is the immediate
        alu_b = imm if instr["type"] == "I" else rt_val

        # addi is implemented as add in the ALU
        alu_op = "add" if op == "addi" else op

        # BEQ/BNE: subtract to test equality
        if op in ("beq", "bne"):
            alu_op = "sub"

        # LW/SW: add base + offset to get effective address
        if op in ("lw", "sw"):
            alu_op = "add"

        # NOP or J: dummy ALU call
        if op in ("nop", "j"):
            alu_result, zero_flag = 0, False
        else:
            alu_result, zero_flag = alu_execute(alu_op, rs_val, alu_b)

        # ── 4. Memory ─────────────────────────────────────────
        mem_result = _memory_access(cpu_state, instr, alu_result, rt_val)

        # ── 5. Write-back ─────────────────────────────────────
        if instr["type"] == "R" and op not in ("nop",):
            # R-type: write to rd
            register_write(cpu_state, instr["rd"], alu_result)

        elif op == "addi":
            # I-type arithmetic: write to rt
            register_write(cpu_state, instr["rt"], alu_result)

        elif op == "lw":
            # Load word: write memory value to rt
            register_write(cpu_state, instr["rt"], mem_result)

        # SW, BEQ, BNE, J: no register write-back

        # ── Log this cycle ────────────────────────────────────
        log.append(make_log_entry(
            cycle=cycle,
            stage="WB",          # single-cycle: all stages collapse into one cycle
            instruction=instr,
            event=None,
        ))

        # ── 6. Advance PC ─────────────────────────────────────
        cpu_state["pc"] = _compute_next_pc(pc, instr, zero_flag, alu_result)
        cycle += 1

        # Safety: prevent infinite loops in programs with tight jumps
        if cycle > 10_000:
            raise RuntimeError("Exceeded 10,000 cycles — possible infinite loop in program.")

    # ── Build metrics ─────────────────────────────────────────
    metrics = make_metrics()
    metrics["total_instructions"]  = len(log)
    metrics["total_cycles"]        = cycle
    metrics["stall_cycles"]        = 0   # no stalls in single-cycle
    metrics["flush_cycles"]        = 0   # no flushes in single-cycle
    metrics["cpi"]        = (cycle / len(log)) if log else 0.0
    metrics["latency"]    = float(cycle)       # caller can multiply by clock period
    metrics["throughput"] = (len(log) / cycle) if cycle else 0.0
    metrics["single_cycle_cycles"] = cycle

    return cpu_state, log, metrics


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

# CURRENT FUNCTION: fetch helper for simulator mode.
# PROTOTYPE NOTE: analyzer mode typically does not need stage-level fetch.
def _fetch(instructions: list, pc: int) -> dict:
    """Return instruction at index pc, or a NOP if out of bounds."""
    if 0 <= pc < len(instructions):
        return instructions[pc]
    return make_instruction("nop", "R")


# CURRENT FUNCTION: memory stage helper for simulator mode.
# PROTOTYPE NOTE: analyzer mode replaces this with static timing aggregation.
def _memory_access(cpu_state: dict, instr: dict, alu_result: int, write_data: int) -> int:
    """
    Handle LW and SW memory operations.

    For LW: reads from cpu_state["memory"] at the word address computed
            by the ALU (base + sign-extended offset). Returns the value
            read so the caller can write it to a register.

    For SW: writes write_data (the value of rt) into memory at alu_result.
            Returns alu_result (unused by write-back stage for SW).

    For all other instructions: a no-op; returns alu_result unchanged.

    Args:
        cpu_state  (dict): current CPU state (memory dict lives here)
        instr      (dict): the current instruction
        alu_result (int):  effective address (for LW/SW) or ALU output
        write_data (int):  value of rt register — data to store for SW

    Returns:
        int: value read from memory (LW) or alu_result (everything else)
    """
    op = instr["op"]

    if op == "lw":
        # Read from memory; default to 0 for uninitialised addresses
        return cpu_state["memory"].get(alu_result, 0)

    elif op == "sw":
        # Write rt's value to the effective address
        cpu_state["memory"][alu_result] = write_data
        return alu_result  # not used by write-back, but keeps return type consistent

    return alu_result  # pass-through for all other ops


# CURRENT FUNCTION: PC update helper for simulator mode.
# PROTOTYPE NOTE: analyzer mode does not execute control flow dynamically.
def _compute_next_pc(pc: int, instr: dict, zero_flag: bool, alu_result: int) -> int:
    """
    Determine the next PC value after this instruction.

    Rules:
        BEQ: branch to pc + 1 + imm  if zero_flag is True  (rs == rt)
        BNE: branch to pc + 1 + imm  if zero_flag is False (rs != rt)
        J:   jump  to instr["imm"]   unconditionally
        *:   sequential, pc + 1

    Note: PC here is an instruction index (not a byte address), so
    branch offset arithmetic is word-aligned by default — no shift needed.

    Args:
        pc         (int):  current instruction index
        instr      (dict): the current instruction
        zero_flag  (bool): ALU zero flag from this cycle's execute stage
        alu_result (int):  ALU output (unused here, kept for signature parity)

    Returns:
        int: next PC value
    """
    op = instr["op"]
    sequential = pc + 1

    if op == "beq":
        return sequential + instr["imm"] if zero_flag else sequential

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
    except NotImplementedError as e:
        print(f"[STUB] {e}")
        print("Expected: $r8=10, $r9=20, $r10=30 after 3 cycles")