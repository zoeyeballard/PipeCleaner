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

# ── Toggle this while Person 1 & 2 are still building ──
USE_STUBS = True

if not USE_STUBS:
    from person1_parser import parse_program
    from person2_alu import alu_execute, register_read, register_write, sign_extend
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
    # TODO: Person 3 implements this
    raise NotImplementedError("Person 3: implement run_single_cycle()")


# ─────────────────────────────────────────────
# HELPERS (suggested — Person 3 may add more)
# ─────────────────────────────────────────────

def _fetch(instructions: list, pc: int) -> dict:
    """Return instruction at index pc, or a NOP if out of bounds."""
    if 0 <= pc < len(instructions):
        return instructions[pc]
    return make_instruction("nop", "R")


def _memory_access(cpu_state: dict, instr: dict, alu_result: int, write_data: int) -> int:
    """
    Handle LW and SW memory operations.

    Returns:
        int: Value read from memory (for LW), or alu_result (for all others)
    """
    # TODO: Person 3 implements this
    raise NotImplementedError("Person 3: implement _memory_access()")


def _compute_next_pc(pc: int, instr: dict, zero_flag: bool, alu_result: int) -> int:
    """
    Determine the next PC value after this instruction.

    For BEQ: if zero_flag is True, branch to pc + 1 + imm
    For J:   jump to imm directly
    Otherwise: pc + 1
    """
    # TODO: Person 3 implements this
    raise NotImplementedError("Person 3: implement _compute_next_pc()")


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