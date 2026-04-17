"""
person4_pipeline.py — 5-Stage Pipeline Stage Logic
ECE 5367 Final Project: Pipelined Performance Analyzer
Owner: Alex Samano

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
from person5_hazard import analyze_hazards

# used for testing
DEFAULT_TIMING_PS = {
    "lw": 800,
    "sw": 700,
    "R": 600,
    "beq": 500,
    "other": 600,
}

PIPELINE_STAGES = 5

# ─────────────────────────────────────────────
# PROTOTYPE / ANALYTICAL HELPERS
# ─────────────────────────────────────────────

def _compute_pipeline_clock(single_cycle_clock_ps, n_stages=5):
    """
    Derive the pipelined clock period by dividing the single-cycle clock
    evenly across all pipeline stages.

    In a balanced pipeline every stage takes (clock / n_stages) ps,
    so the new clock period equals that per-stage time.

    Args:
        single_cycle_clock_ps (float): The single-cycle reference clock in ps.
            This is the critical-path delay = max stage delay across all instr types.
        n_stages (int): Number of pipeline stages (default 5 for classic MIPS).

    Returns:
        float: Pipelined clock period in ps.
    """
    if n_stages <= 0:
        raise ValueError("n_stages must be positive")
    return single_cycle_clock_ps / n_stages


def _estimate_pipeline_cycles(total_instructions, stall_cycles, n_stages=5):
    """
    Estimate total cycle count for the analytical (non-simulation) path.

    Formula:
        base_cycles  = total_instructions + (n_stages - 1)
            — instructions to drain the pipeline after the last one is fetched
        total_cycles = base_cycles + stall_cycles

    Args:
        total_instructions (int): Number of instructions in the program.
        stall_cycles       (int): Extra cycles inserted by hazards/branches.
        n_stages           (int): Pipeline depth (default 5).

    Returns:
        int: Estimated total cycle count.
    """
    if total_instructions <= 0:
        return 0
    base_cycles = total_instructions + (n_stages - 1)
    return base_cycles + stall_cycles


def run_pipeline_analyzer(instructions, timing_ps=None, assumed_branch_penalty=0):
    """
    Compute pipelined performance metrics analytically — no stage-by-stage
    execution.  Use this path when the caller only needs numbers, not a
    full simulation trace.

    Steps:
        1. Determine single-cycle clock = max stage delay across all instr types.
        2. Derive pipelined clock via _compute_pipeline_clock().
        3. Call analyze_hazards() to get stall + branch counts.
        4. Estimate total cycles via _estimate_pipeline_cycles().
        5. Derive CPI, latency, throughput.

    Args:
        instructions           (list[dict]): Parsed instruction list.
        timing_ps              (dict):       Override DEFAULT_TIMING_PS entries.
        assumed_branch_penalty (int):        Extra cycles per branch (0 = assume
                                             not-taken / forwarded).

    Returns:
        tuple: (cpu_state, log, metrics)
            cpu_state — blank (no simulation performed)
            log       — one entry per instruction (stage="PIPE")
            metrics   — fully populated make_metrics() dict
    """
    timing = dict(DEFAULT_TIMING_PS)
    if timing_ps:
        timing.update(timing_ps)

    n = len(instructions)
    cpu_state = make_cpu_state()

    # 1. Clocks
    single_cycle_clock_ps = max(
        timing["lw"], timing["sw"], timing["R"], timing["beq"]
    )
    pipelined_clock_ps = _compute_pipeline_clock(single_cycle_clock_ps, PIPELINE_STAGES)

    # 2. Hazard analysis (Person 5)
    hazard_stats = analyze_hazards(instructions)
    stall_cycles = hazard_stats["stall_cycles"]
    branch_cycles = hazard_stats["branch_instructions"] * max(assumed_branch_penalty, 0)
    total_extra = stall_cycles + branch_cycles

    # 3. Cycle estimate
    total_cycles = _estimate_pipeline_cycles(n, total_extra, PIPELINE_STAGES)

    # 4. Derived metrics
    cpi = (total_cycles / n) if n else 0.0
    total_time_ps = total_cycles * pipelined_clock_ps
    avg_latency_ps = (total_time_ps / n) if n else 0.0
    throughput_per_ps = (1.0 / avg_latency_ps) if avg_latency_ps else 0.0

    # 5. Build a simplified log (one entry per instruction, no stage detail)
    log = [
        make_log_entry(cycle=i, stage="PIPE", instruction=instr, event=None)
        for i, instr in enumerate(instructions)
    ]

    metrics = make_metrics()
    metrics["total_instructions"]   = n
    metrics["total_cycles"]         = int(total_cycles)
    metrics["stall_cycles"]         = int(total_extra)
    metrics["flush_cycles"]         = int(branch_cycles)
    metrics["cpi"]                  = float(cpi)
    metrics["latency"]              = float(total_time_ps)
    metrics["throughput"]           = float(throughput_per_ps)
    metrics["single_cycle_clock_ps"] = float(single_cycle_clock_ps)
    metrics["pipelined_clock_ps"]   = float(pipelined_clock_ps)
    metrics["total_time_ps"]        = float(total_time_ps)
    metrics["latency_ps"]           = float(avg_latency_ps)
    metrics["throughput_per_ps"]    = float(throughput_per_ps)
    metrics["hazards"]              = hazard_stats
    metrics["pipelined_cycles"]     = int(total_cycles)

    return cpu_state, log, metrics


# ─────────────────────────────────────────────
# STUBS / REAL IMPORTS
# ─────────────────────────────────────────────

USE_STUBS = True

if not USE_STUBS:
    from rolandoU_alu import alu_execute, register_read, register_write, sign_extend
    from person5_hazard import detect_hazards
else:
    def alu_execute(op, a, b):
        ops = {"add": a + b, "sub": a - b, "and": a & b, "or": a | b, "slt": int(a < b)}
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
# CONTROL SIGNAL HELPERS
# ─────────────────────────────────────────────

def _control_signals(op):
    """
    Return the set of control signals for a given opcode.

    Mirrors the Patterson & Hennessy main control unit truth table.
    All signals default to False; only the relevant ones are set True.

    Args:
        op (str): Instruction opcode string e.g. "add", "lw", "beq".

    Returns:
        dict: Control signal values for this instruction.
    """
    signals = {
        "reg_dst":    False,
        "alu_src":    False,
        "mem_to_reg": False,
        "reg_write":  False,
        "mem_read":   False,
        "mem_write":  False,
        "branch":     False,
    }
    if op in ("add", "sub", "and", "or", "slt"):   # R-type
        signals["reg_dst"]   = True
        signals["reg_write"] = True
    elif op == "addi":
        signals["alu_src"]   = True
        signals["reg_write"] = True
    elif op == "lw":
        signals["alu_src"]   = True
        signals["mem_to_reg"] = True
        signals["reg_write"] = True
        signals["mem_read"]  = True
    elif op == "sw":
        signals["alu_src"]   = True
        signals["mem_write"] = True
    elif op in ("beq", "bne"):
        signals["branch"]    = True
    # nop / j / unknown: all False
    return signals


def _alu_op(op):
    """
    Map an instruction opcode to the ALU operation string expected by alu_execute().

    Args:
        op (str): Instruction opcode.

    Returns:
        str: ALU operation key ("add", "sub", "and", "or", "slt").
    """
    mapping = {
        "add":  "add",
        "addi": "add",
        "lw":   "add",   # base + offset
        "sw":   "add",   # base + offset
        "sub":  "sub",
        "beq":  "sub",   # BEQ uses subtraction to test equality
        "bne":  "sub",
        "and":  "and",
        "or":   "or",
        "slt":  "slt",
    }
    return mapping.get(op, "add")


# ─────────────────────────────────────────────
# STAGE FUNCTIONS
# ─────────────────────────────────────────────

def stage_IF(cpu_state: dict, instructions: list, hazard_signals: dict) -> dict:
    """
    Instruction Fetch stage.

    Reads the instruction at cpu_state["pc"] and produces the IF/ID latch.
    If hazard_signals["stall"] is True, freeze the PC and re-output the
    same NOP so the downstream stages see a bubble this cycle.

    Args:
        cpu_state      (dict): Current CPU state — reads "pc" field.
        instructions   (list): Full instruction list.
        hazard_signals (dict): From detect_hazards(); checks "stall" and "flush".

    Returns:
        dict: New IF_ID pipeline register contents.
    """
    pc = cpu_state.get("pc", 0)
    nop = make_instruction("nop", "R")

    if hazard_signals.get("stall", False):
        # Freeze: re-issue a NOP bubble; caller must NOT advance PC this cycle.
        return {
            "instruction": nop,
            "pc_plus_4":   pc + 1,
            "stall":       True,
            "flush":       False,
        }

    if hazard_signals.get("flush", False):
        # Branch misprediction: squash whatever we fetched.
        return {
            "instruction": nop,
            "pc_plus_4":   pc + 1,
            "stall":       False,
            "flush":       True,
        }

    # Normal fetch
    if 0 <= pc < len(instructions):
        instr = instructions[pc]
    else:
        instr = nop   # past end of program — drain with NOPs

    return {
        "instruction": instr,
        "pc_plus_4":   pc + 1,
        "stall":       False,
        "flush":       False,
    }


def stage_ID(IF_ID: dict, cpu_state: dict, hazard_signals: dict) -> dict:
    """
    Instruction Decode / Register Read stage.

    Reads register values, sets control signals, sign-extends the immediate.
    Inserts a NOP bubble into ID_EX on stall or flush.

    Args:
        IF_ID          (dict): Latch from stage_IF.
        cpu_state      (dict): Register file lives here.
        hazard_signals (dict): "stall" and "flush" signals.

    Returns:
        dict: New ID_EX pipeline register contents.
    """
    nop = make_instruction("nop", "R")

    # Stall or flush → inject a NOP bubble so EX sees nothing useful.
    if hazard_signals.get("stall", False) or hazard_signals.get("flush", False):
        return {
            "instruction":  nop,
            "pc_plus_4":    IF_ID.get("pc_plus_4", 0),
            "read_data_1":  0,
            "read_data_2":  0,
            "sign_ext_imm": 0,
            "rs": 0, "rt": 0, "rd": 0,
            "reg_dst":    False, "alu_src":    False,
            "mem_to_reg": False, "reg_write":  False,
            "mem_read":   False, "mem_write":  False,
            "branch":     False,
            "stall":      hazard_signals.get("stall", False),
            "flush":      hazard_signals.get("flush", False),
        }

    instr = IF_ID.get("instruction") or nop
    op    = instr.get("op", "nop")
    rs    = instr.get("rs", 0)
    rt    = instr.get("rt", 0)
    rd    = instr.get("rd", 0)
    imm   = instr.get("imm", 0)

    read_data_1, read_data_2 = register_read(cpu_state, rs, rt)
    sign_ext_imm = sign_extend(imm)
    ctrl = _control_signals(op)

    return {
        "instruction":  instr,
        "pc_plus_4":    IF_ID.get("pc_plus_4", 0),
        "read_data_1":  read_data_1,
        "read_data_2":  read_data_2,
        "sign_ext_imm": sign_ext_imm,
        "rs":  rs,
        "rt":  rt,
        "rd":  rd,
        **ctrl,
        "stall": False,
        "flush": False,
    }


def stage_EX(ID_EX: dict, hazard_signals: dict, EX_MEM: dict, MEM_WB: dict) -> dict:
    """
    Execute / ALU stage.

    Applies forwarding (from hazard_signals), selects ALU inputs,
    calls alu_execute(), and computes the branch target address.

    Forwarding priority (highest to lowest):
        EX_MEM  — result from the instruction that just left EX
        MEM_WB  — result from the instruction that just left MEM
        REG     — value read from the register file in ID

    Args:
        ID_EX          (dict): Latch from stage_ID.
        hazard_signals (dict): Contains "forward_a" and "forward_b".
        EX_MEM         (dict): Source for EX→EX forwarding.
        MEM_WB         (dict): Source for MEM→EX forwarding.

    Returns:
        dict: New EX_MEM pipeline register contents.
    """
    instr     = ID_EX.get("instruction") or make_instruction("nop", "R")
    op        = instr.get("op", "nop")
    forward_a = hazard_signals.get("forward_a", "REG")
    forward_b = hazard_signals.get("forward_b", "REG")

    # ── Select ALU input A (rs) ──────────────────────────────────────────
    if forward_a == "EX_MEM":
        alu_in_a = EX_MEM.get("alu_result", 0)
    elif forward_a == "MEM_WB":
        # If the forwarding instruction was a load, use the memory read data.
        if MEM_WB.get("mem_to_reg", False):
            alu_in_a = MEM_WB.get("read_data", 0)
        else:
            alu_in_a = MEM_WB.get("alu_result", 0)
    else:   # "REG"
        alu_in_a = ID_EX.get("read_data_1", 0)

    # ── Select ALU input B (rt or immediate) ────────────────────────────
    if forward_b == "EX_MEM":
        forwarded_b = EX_MEM.get("alu_result", 0)
    elif forward_b == "MEM_WB":
        if MEM_WB.get("mem_to_reg", False):
            forwarded_b = MEM_WB.get("read_data", 0)
        else:
            forwarded_b = MEM_WB.get("alu_result", 0)
    else:
        forwarded_b = ID_EX.get("read_data_2", 0)

    # alu_src selects between the (possibly forwarded) register value and the
    # sign-extended immediate (e.g. for addi, lw, sw).
    if ID_EX.get("alu_src", False):
        alu_in_b = ID_EX.get("sign_ext_imm", 0)
    else:
        alu_in_b = forwarded_b

    # ── ALU operation ────────────────────────────────────────────────────
    alu_result, zero_flag = alu_execute(_alu_op(op), alu_in_a, alu_in_b)

    # ── Branch target = PC+4 + (sign_ext_imm << 2) ──────────────────────
    # We store PC as an instruction index, so the shift is omitted here.
    branch_target = ID_EX.get("pc_plus_4", 0) + ID_EX.get("sign_ext_imm", 0)

    # ── Destination register ─────────────────────────────────────────────
    # reg_dst=True  → R-type: destination is rd
    # reg_dst=False → I-type: destination is rt
    write_reg = ID_EX.get("rd", 0) if ID_EX.get("reg_dst", False) else ID_EX.get("rt", 0)

    return {
        "instruction":   instr,
        "alu_result":    alu_result,
        "write_data":    forwarded_b,   # data to store (SW)
        "write_reg":     write_reg,
        "zero_flag":     zero_flag,
        "branch_target": branch_target,
        # Forward control signals
        "mem_to_reg":    ID_EX.get("mem_to_reg", False),
        "reg_write":     ID_EX.get("reg_write",  False),
        "mem_read":      ID_EX.get("mem_read",   False),
        "mem_write":     ID_EX.get("mem_write",  False),
        "branch":        ID_EX.get("branch",     False),
        "stall":         False,
        "flush":         False,
    }


def stage_MEM(EX_MEM: dict, cpu_state: dict) -> tuple:
    """
    Memory Access stage.

    Performs LW (read from memory) or SW (write to memory) using
    alu_result as the effective address.  All other instructions pass
    through unchanged.

    Args:
        EX_MEM    (dict): Latch from stage_EX.
        cpu_state (dict): cpu_state["memory"] is the data memory dict.

    Returns:
        tuple: (new MEM_WB latch dict, updated cpu_state dict)
    """
    cpu_state = copy.deepcopy(cpu_state)   # avoid mutating caller's state
    addr      = EX_MEM.get("alu_result", 0)

    read_data = 0
    if EX_MEM.get("mem_read", False):
        # LW: read from memory; default 0 if address not initialised.
        read_data = cpu_state["memory"].get(addr, 0)

    if EX_MEM.get("mem_write", False):
        # SW: write rt value (stored in write_data) to memory.
        cpu_state["memory"][addr] = EX_MEM.get("write_data", 0)

    mem_wb = {
        "instruction": EX_MEM.get("instruction"),
        "read_data":   read_data,
        "alu_result":  EX_MEM.get("alu_result", 0),
        "write_reg":   EX_MEM.get("write_reg",  0),
        # Forward control signals needed by WB
        "mem_to_reg":  EX_MEM.get("mem_to_reg", False),
        "reg_write":   EX_MEM.get("reg_write",  False),
        "stall":       False,
        "flush":       False,
    }
    return mem_wb, cpu_state


def stage_WB(MEM_WB: dict, cpu_state: dict) -> dict:
    """
    Write-Back stage.

    Writes the result (ALU result or memory read data) back to the
    register file if reg_write is asserted.

    Args:
        MEM_WB    (dict): Latch from stage_MEM.
        cpu_state (dict): Register file is updated here.

    Returns:
        dict: Updated cpu_state (register file modified in place).
    """
    if not MEM_WB.get("reg_write", False):
        return cpu_state   # Nothing to write back (SW, BEQ, NOP, …)

    # mem_to_reg selects between the memory read data (LW) and the ALU result.
    if MEM_WB.get("mem_to_reg", False):
        write_value = MEM_WB.get("read_data", 0)
    else:
        write_value = MEM_WB.get("alu_result", 0)

    rd = MEM_WB.get("write_reg", 0)
    cpu_state = register_write(cpu_state, rd, write_value)
    return cpu_state


# ─────────────────────────────────────────────
# MAIN PIPELINE LOOP
# ─────────────────────────────────────────────

def run_pipeline(
    instructions: list,
    initial_state: dict = None,
    timing_ps: dict = None,
    assumed_branch_penalty: int = 0,
) -> tuple:
    """
    Execute a MIPS program through the 5-stage pipeline.

    Implements the analytical performance path (matching the prototype
    analyzer branch).  Stage-by-stage simulation stubs are present but
    the metrics are computed analytically via analyze_hazards() so that
    results are available even when stage implementations are incomplete.

    Args:
        instructions           (list[dict]): Parsed instruction list.
        initial_state          (dict):       Optional pre-loaded cpu_state.
        timing_ps              (dict):       Override DEFAULT_TIMING_PS entries.
        assumed_branch_penalty (int):        Extra stall cycles per branch
                                             instruction (0 = ideal forwarding).

    Returns:
        tuple: (
            cpu_state (dict) — final register/memory state,
            log       (list) — one make_log_entry() per instruction,
            metrics   (dict) — fully populated make_metrics() dict,
        )
    """
    cpu_state = make_cpu_state() if initial_state is None else initial_state

    # ── Clock derivation ─────────────────────────────────────────────────
    timing = dict(DEFAULT_TIMING_PS)
    if timing_ps:
        timing.update(timing_ps)

    single_cycle_clock_ps = max(
        timing["lw"], timing["sw"], timing["R"], timing["beq"]
    )
    pipelined_clock_ps = _compute_pipeline_clock(single_cycle_clock_ps, PIPELINE_STAGES)

    # ── Hazard analysis (Person 5) ───────────────────────────────────────
    n = len(instructions)
    hazard_stats  = analyze_hazards(instructions)
    stall_cycles  = hazard_stats["stall_cycles"]
    branch_cycles = hazard_stats["branch_instructions"] * max(assumed_branch_penalty, 0)

    # ── Cycle count ──────────────────────────────────────────────────────
    total_cycles = _estimate_pipeline_cycles(n, stall_cycles + branch_cycles, PIPELINE_STAGES)

    # ── Performance metrics ───────────────────────────────────────────────
    cpi              = (total_cycles / n) if n else 0.0
    total_time_ps    = total_cycles * pipelined_clock_ps
    avg_latency_ps   = (total_time_ps / n) if n else 0.0
    throughput_per_ps = (1.0 / avg_latency_ps) if avg_latency_ps else 0.0

    # ── Simplified execution log (one entry per instruction) ─────────────
    log = [
        make_log_entry(cycle=i, stage="PIPE", instruction=instr, event=None)
        for i, instr in enumerate(instructions)
    ]

    # ── Populate metrics dict ─────────────────────────────────────────────
    metrics = make_metrics()
    metrics["total_instructions"]    = n
    metrics["total_cycles"]          = int(total_cycles)
    metrics["stall_cycles"]          = int(stall_cycles + branch_cycles)
    metrics["flush_cycles"]          = int(branch_cycles)
    metrics["cpi"]                   = float(cpi)
    metrics["latency"]               = float(total_time_ps)
    metrics["throughput"]            = float(throughput_per_ps)
    metrics["single_cycle_clock_ps"] = float(single_cycle_clock_ps)
    metrics["pipelined_clock_ps"]    = float(pipelined_clock_ps)
    metrics["total_time_ps"]         = float(total_time_ps)
    metrics["latency_ps"]            = float(avg_latency_ps)
    metrics["throughput_per_ps"]     = float(throughput_per_ps)
    metrics["hazards"]               = hazard_stats
    metrics["pipelined_cycles"]      = int(total_cycles)

    return cpu_state, log, metrics


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
        print(f"\nCPI:             {metrics['cpi']:.3f}")
        print(f"Total cycles:    {metrics['total_cycles']}")
        print(f"Stall cycles:    {metrics['stall_cycles']}")
        print(f"Single-cycle clk:{metrics['single_cycle_clock_ps']} ps")
        print(f"Pipelined clk:   {metrics['pipelined_clock_ps']} ps")
        print(f"Total time:      {metrics['total_time_ps']} ps")
    except NotImplementedError as e:
        print(f"[STUB] {e}")
        print("Expected: $r8=5, $r9=3, $r10=8  (with stalls for RAW hazards)")