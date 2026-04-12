"""
common.py — Shared Data Structures & Interfaces
ECE 5367 Final Project: Pipelined Performance Analyzer
Spring 2026

ALL team members import from this file.
Do NOT modify these structures without group agreement.
"""

# ─────────────────────────────────────────────
# INSTRUCTION REPRESENTATION
# ─────────────────────────────────────────────

def make_instruction(op, instr_type, rs=0, rt=0, rd=0, imm=0, label=None, raw=""):
    """
    Canonical representation of a decoded MIPS instruction.

    Args:
        op       (str): Operation name e.g. "add", "lw", "beq"
        instr_type (str): "R", "I", or "J"
        rs       (int): Source register index (0–31)
        rt       (int): Target register index (0–31)
        rd       (int): Destination register index (R-type only, 0–31)
        imm      (int): Immediate value (I-type) or jump address (J-type)
        label    (str): Optional branch/jump label
        raw      (str): Original instruction string for debugging

    Returns:
        dict: Instruction dictionary
    """
    return {
        "op":    op,
        "type":  instr_type,   # "R", "I", or "J"
        "rs":    rs,
        "rt":    rt,
        "rd":    rd,
        "imm":   imm,
        "label": label,
        "raw":   raw,
    }


# ─────────────────────────────────────────────
# CPU STATE
# ─────────────────────────────────────────────

def make_cpu_state():
    """
    Represents the full architectural state of the MIPS CPU.

    registers[0] is always 0 (hardwired $zero).
    memory maps byte addresses (int) to values (int).

    Returns:
        dict: Initial CPU state
    """
    return {
        "registers": [0] * 32,   # $zero ... $ra
        "memory":    {},          # addr (int) -> value (int)
        "pc":        0,           # program counter (index into instruction list)
    }


# ─────────────────────────────────────────────
# PIPELINE REGISTERS
# (state passed between pipeline stages each cycle)
# ─────────────────────────────────────────────

def make_pipeline_registers():
    """
    The four inter-stage latches of the classic 5-stage pipeline.
    Each latch holds the outputs produced by one stage for the next stage to consume.

    Hazard fields:
        stall (bool): this latch is frozen this cycle (bubble inserted)
        flush (bool): this latch should be cleared (branch misprediction)

    Returns:
        dict: All four pipeline register latches initialised to NOP/zero state
    """
    nop_instr = make_instruction("nop", "R")

    return {
        # After Instruction Fetch
        "IF_ID": {
            "instruction": nop_instr,
            "pc_plus_4":   0,
            "stall":       False,
            "flush":       False,
        },

        # After Instruction Decode / Register Read
        "ID_EX": {
            "instruction":  nop_instr,
            "pc_plus_4":    0,
            "read_data_1":  0,       # Value of rs
            "read_data_2":  0,       # Value of rt
            "sign_ext_imm": 0,       # Sign-extended immediate
            "rs":           0,
            "rt":           0,
            "rd":           0,
            # Control signals
            "reg_dst":      False,   # 0 = rt destination, 1 = rd destination
            "alu_src":      False,   # 0 = register, 1 = immediate
            "mem_to_reg":   False,
            "reg_write":    False,
            "mem_read":     False,
            "mem_write":    False,
            "branch":       False,
            "stall":        False,
            "flush":        False,
        },

        # After Execute / ALU
        "EX_MEM": {
            "instruction":    nop_instr,
            "alu_result":     0,
            "write_data":     0,     # Data to write to memory (for SW)
            "write_reg":      0,     # Destination register index
            "zero_flag":      False, # ALU zero flag (used for BEQ)
            "branch_target":  0,     # Computed branch target PC
            # Control signals forwarded
            "mem_to_reg":     False,
            "reg_write":      False,
            "mem_read":       False,
            "mem_write":      False,
            "branch":         False,
            "stall":          False,
            "flush":          False,
        },

        # After Memory Access
        "MEM_WB": {
            "instruction":  nop_instr,
            "read_data":    0,       # Data read from memory (for LW)
            "alu_result":   0,       # ALU result passed through
            "write_reg":    0,       # Destination register index
            # Control signals forwarded
            "mem_to_reg":   False,
            "reg_write":    False,
            "stall":        False,
            "flush":        False,
        },
    }


# ─────────────────────────────────────────────
# HAZARD / FORWARDING SIGNALS
# ─────────────────────────────────────────────

def make_hazard_signals():
    """
    Output of the Hazard Detection Unit and Forwarding Unit each cycle.

    forward_a / forward_b values:
        "REG"    — use register file value (no forwarding needed)
        "EX_MEM" — forward from EX/MEM latch (1-cycle-old result)
        "MEM_WB" — forward from MEM/WB latch (2-cycle-old result)

    Returns:
        dict: Default signals (no hazard, no forwarding)
    """
    return {
        "stall":       False,       # Insert a pipeline bubble this cycle
        "flush":       False,       # Flush IF/ID and ID/EX (branch taken)
        "forward_a":   "REG",       # Forwarding for ALU input A (rs)
        "forward_b":   "REG",       # Forwarding for ALU input B (rt)
    }


# ─────────────────────────────────────────────
# EXECUTION LOG ENTRY
# (Person 6 collects these to compute metrics)
# ─────────────────────────────────────────────

def make_log_entry(cycle, stage, instruction, event=None):
    """
    One row of the execution trace — used by Person 6 to compute metrics.

    Args:
        cycle       (int): Clock cycle number (0-indexed)
        stage       (str): Pipeline stage name e.g. "IF", "ID", "EX", "MEM", "WB"
        instruction (dict): The instruction in this stage this cycle
        event       (str): Optional — "stall", "flush", "forward", or None

    Returns:
        dict: Log entry
    """
    return {
        "cycle":       cycle,
        "stage":       stage,
        "instruction": instruction,
        "event":       event,        # None | "stall" | "flush" | "forward"
    }


# ─────────────────────────────────────────────
# PERFORMANCE METRICS
# ─────────────────────────────────────────────

def make_metrics():
    """
    Container for performance analysis results (populated by Person 6).

    Returns:
        dict: Zero-initialised metrics structure
    """
    return {
        # Counts
        "total_instructions":  0,
        "total_cycles":        0,
        "stall_cycles":        0,
        "flush_cycles":        0,

        # Derived
        "cpi":        0.0,   # Cycles Per Instruction = total_cycles / total_instructions
        "latency":    0.0,   # total_cycles * clock_period_ns
        "throughput": 0.0,   # total_instructions / total_cycles  (IPC)

        # Comparison (filled by Person 6 after running both simulators)
        "single_cycle_cycles": 0,
        "pipelined_cycles":    0,
        "speedup":             0.0,  # single_cycle_cycles / pipelined_cycles
    }


# ─────────────────────────────────────────────
# SUPPORTED INSTRUCTIONS (reference)
# ─────────────────────────────────────────────

SUPPORTED_INSTRUCTIONS = {
    # R-type
    "add":  {"type": "R", "funct": 0x20},
    "sub":  {"type": "R", "funct": 0x22},
    "and":  {"type": "R", "funct": 0x24},
    "or":   {"type": "R", "funct": 0x25},
    "slt":  {"type": "R", "funct": 0x2A},
    "nop":  {"type": "R", "funct": 0x00},

    # I-type
    "addi": {"type": "I", "opcode": 0x08},
    "lw":   {"type": "I", "opcode": 0x23},
    "sw":   {"type": "I", "opcode": 0x2B},
    "beq":  {"type": "I", "opcode": 0x04},
    "bne":  {"type": "I", "opcode": 0x05},

    # J-type
    "j":    {"type": "J", "opcode": 0x02},
}

REGISTER_NAMES = {
    "$zero": 0,  "$at": 1,  "$v0": 2,  "$v1": 3,
    "$a0":   4,  "$a1": 5,  "$a2": 6,  "$a3": 7,
    "$t0":   8,  "$t1": 9,  "$t2": 10, "$t3": 11,
    "$t4":   12, "$t5": 13, "$t6": 14, "$t7": 15,
    "$s0":   16, "$s1": 17, "$s2": 18, "$s3": 19,
    "$s4":   20, "$s5": 21, "$s6": 22, "$s7": 23,
    "$t8":   24, "$t9": 25,
    "$sp":   29, "$fp": 30, "$ra": 31,
}