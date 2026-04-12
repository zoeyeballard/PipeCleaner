"""
person4_pipeline.py — 5-Stage Pipeline Stage Logic
ECE 5367 Final Project: Pipelined Performance Analyzer
Owner: Person 4

RESPONSIBILITY:
    Implement each of the 5 pipeline stages (IF, ID, EX, MEM, WB) as
    pure functions that transform pipeline register state. Also implement
    the main pipeline loop that advances the CPU one cycle at a time.

    Hazard signals come from Person 5 — use the stub below until ready.

DEPENDENCY STRATEGY:
    Imports from person2_alu and person5_hazard.
    Toggle USE_STUBS = True while those are still in progress.

INTERFACE CONTRACT (do not change signatures):
    stage_IF(cpu_state, instructions, hazard_signals)       -> dict  (new IF_ID latch)
    stage_ID(IF_ID, cpu_state, hazard_signals)              -> dict  (new ID_EX latch)
    stage_EX(ID_EX, hazard_signals, EX_MEM, MEM_WB)        -> dict  (new EX_MEM latch)
    stage_MEM(EX_MEM, cpu_state)                            -> (dict, dict)  (new MEM_WB, updated cpu_state)
    stage_WB(MEM_WB, cpu_state)                             -> dict  (updated cpu_state)
    run_pipeline(instructions, initial_state=None)          -> (cpu_state, log, metrics)

TESTING:
    Run this file directly: python person4_pipeline.py
"""

import copy
from common import (
    make_cpu_state,
    make_pipeline_registers,
    make_hazard_signals,
    make_log_entry,
    make_metrics,
    make_instruction,
)

USE_STUBS = True

if not USE_STUBS:
    from person2_alu import alu_execute, register_read, register_write, sign_extend
    from person5_hazard import detect_hazards
else:
    def alu_execute(op, a, b):
        ops = {"add": a+b, "sub": a-b, "and": a&b, "or": a|b, "slt": int(a<b)}
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

    def detect_hazards(ID_EX, EX_MEM, MEM_WB):
        """Stub: no hazards detected — Person 5 replaces this"""
        return make_hazard_signals()


# ─────────────────────────────────────────────
# STAGE FUNCTIONS
# ─────────────────────────────────────────────

def stage_IF(cpu_state: dict, instructions: list, hazard_signals: dict) -> dict:
    """
    Instruction Fetch stage.

    Reads the instruction at cpu_state["pc"] and produces the IF/ID latch.
    If hazard_signals["stall"] is True, freeze PC and re-output the same latch.

    Args:
        cpu_state      (dict): Current CPU state (read PC from here)
        instructions   (list): Full instruction list
        hazard_signals (dict): From Person 5's detect_hazards()

    Returns:
        dict: New IF_ID pipeline register contents
    """
    # TODO: Person 4 implements this
    raise NotImplementedError("Person 4: implement stage_IF()")


def stage_ID(IF_ID: dict, cpu_state: dict, hazard_signals: dict) -> dict:
    """
    Instruction Decode / Register Read stage.

    Reads register values, sets control signals, sign-extends immediate.
    If hazard_signals["stall"], insert a NOP bubble into ID_EX.
    If hazard_signals["flush"], clear IF_ID and insert NOP into ID_EX.

    Args:
        IF_ID          (dict): Latch from stage_IF
        cpu_state      (dict): Register file lives here
        hazard_signals (dict): Stall / flush signals

    Returns:
        dict: New ID_EX pipeline register contents
    """
    # TODO: Person 4 implements this
    # Control signal hints:
    #   R-type: reg_dst=True,  alu_src=False, reg_write=True,  mem_read=False, mem_write=False
    #   LW:     reg_dst=False, alu_src=True,  reg_write=True,  mem_read=True,  mem_write=False
    #   SW:     reg_dst=False, alu_src=True,  reg_write=False, mem_read=False, mem_write=True
    #   BEQ:    reg_dst=False, alu_src=False, reg_write=False, mem_read=False, branch=True
    raise NotImplementedError("Person 4: implement stage_ID()")


def stage_EX(ID_EX: dict, hazard_signals: dict, EX_MEM: dict, MEM_WB: dict) -> dict:
    """
    Execute / ALU stage.

    Applies forwarding (from hazard_signals), selects ALU inputs,
    calls alu_execute(), computes branch target.

    Args:
        ID_EX          (dict): Latch from stage_ID
        hazard_signals (dict): Contains forward_a and forward_b
        EX_MEM         (dict): Source for EX→EX forwarding
        MEM_WB         (dict): Source for MEM→EX forwarding

    Returns:
        dict: New EX_MEM pipeline register contents
    """
    # TODO: Person 4 implements this
    # Forwarding logic hint:
    #   if forward_a == "EX_MEM": use EX_MEM["alu_result"] as ALU input A
    #   if forward_a == "MEM_WB": use MEM_WB["alu_result"] (or MEM_WB["read_data"] if mem_to_reg)
    #   else: use ID_EX["read_data_1"]
    raise NotImplementedError("Person 4: implement stage_EX()")


def stage_MEM(EX_MEM: dict, cpu_state: dict) -> tuple:
    """
    Memory Access stage.

    Performs LW (read) or SW (write) on cpu_state["memory"].

    Args:
        EX_MEM    (dict): Latch from stage_EX
        cpu_state (dict): Memory lives here

    Returns:
        tuple: (new MEM_WB latch dict, updated cpu_state dict)
    """
    # TODO: Person 4 implements this
    raise NotImplementedError("Person 4: implement stage_MEM()")


def stage_WB(MEM_WB: dict, cpu_state: dict) -> dict:
    """
    Write-Back stage.

    Writes the result (ALU result or memory read) back to the register file.

    Args:
        MEM_WB    (dict): Latch from stage_MEM
        cpu_state (dict): Register file is updated here

    Returns:
        dict: Updated cpu_state
    """
    # TODO: Person 4 implements this
    raise NotImplementedError("Person 4: implement stage_WB()")


# ─────────────────────────────────────────────
# MAIN PIPELINE LOOP
# ─────────────────────────────────────────────

def run_pipeline(instructions: list, initial_state: dict = None) -> tuple:
    """
    Execute a MIPS program through the 5-stage pipeline.

    Args:
        instructions  (list[dict]): Parsed instruction list
        initial_state (dict):       Optional pre-loaded cpu_state

    Returns:
        tuple: (
            cpu_state (dict) — final register/memory state,
            log       (list) — list of make_log_entry() dicts (one per stage per cycle),
            metrics   (dict) — populated make_metrics() dict
        )

    Loop hint (each cycle):
        1. Call detect_hazards(ID_EX, EX_MEM, MEM_WB)  <- Person 5
        2. WB  stage  (MEM_WB  -> register write)
        3. MEM stage  (EX_MEM  -> memory, produces MEM_WB)
        4. EX  stage  (ID_EX   -> ALU,    produces EX_MEM)
        5. ID  stage  (IF_ID   -> decode, produces ID_EX)
        6. IF  stage  (PC      -> fetch,  produces IF_ID)
        7. Update PC based on hazard signals and branch results
        8. Append log entries
        Stop when all stages hold NOPs and PC >= len(instructions)
    """
    # TODO: Person 4 implements this
    raise NotImplementedError("Person 4: implement run_pipeline()")


# ─────────────────────────────────────────────
# QUICK SELF-TEST (run: python person4_pipeline.py)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    from common import make_instruction
    print(f"Running with {'STUBS' if USE_STUBS else 'real modules'}...\n")

    # Minimal test — no hazards
    instructions = [
        make_instruction("addi", "I", rs=0, rt=8,  imm=5,  raw="addi $t0,$zero,5"),
        make_instruction("addi", "I", rs=0, rt=9,  imm=3,  raw="addi $t1,$zero,3"),
        make_instruction("add",  "R", rs=8, rt=9,  rd=10,  raw="add  $t2,$t0,$t1"),
    ]

    try:
        final_state, log, metrics = run_pipeline(instructions)
        print("Final registers (non-zero):")
        for i, v in enumerate(final_state["registers"]):
            if v != 0:
                print(f"  $r{i} = {v}")
        print(f"\nCPI: {metrics['cpi']:.3f}")
        print(f"Total cycles: {metrics['total_cycles']}")
        print(f"Stall cycles: {metrics['stall_cycles']}")
    except NotImplementedError as e:
        print(f"[STUB] {e}")
        print("Expected: $r8=5, $r9=3, $r10=8  (with stalls for RAW hazards)")