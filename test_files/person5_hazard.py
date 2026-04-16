"""
person5_hazard.py — Hazard Detection & Forwarding Unit
ECE 5367 Final Project: Pipelined Performance Analyzer
Owner: Leziga Beage

RESPONSIBILITY:
    Each cycle, inspect the current pipeline latch contents and decide:
      • Whether to stall (insert a bubble)
      • Whether to flush (branch taken)
      • Which forwarding paths to activate for ALU inputs A and B

    This module is PURE LOGIC — it only reads pipeline register dicts
    and returns a hazard signals dict. No dependency on other modules.

INTERFACE CONTRACT (do not change signatures):
    detect_hazards(ID_EX, EX_MEM, MEM_WB) -> dict  (hazard signals)
    needs_stall(ID_EX, EX_MEM)            -> bool
    needs_flush(EX_MEM)                   -> bool
    forwarding_unit(ID_EX, EX_MEM, MEM_WB) -> (str, str)

TESTING:
    Run this file directly: python person5_hazard.py
"""

from common import make_hazard_signals


# ─────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────

def detect_hazards(ID_EX: dict, EX_MEM: dict, MEM_WB: dict) -> dict:
    """
    Master hazard detection function called once per cycle by Person 4's pipeline loop.

    Combines stall detection, flush detection, and forwarding decisions
    into a single hazard signals dict.

    Args:
        ID_EX  (dict): Current ID/EX pipeline register
        EX_MEM (dict): Current EX/MEM pipeline register
        MEM_WB (dict): Current MEM/WB pipeline register

    Returns:
        dict: make_hazard_signals() dict with stall, flush, forward_a, forward_b set
    """
    # TODO: Person 5 implements this
    # Suggested structure:
    #   signals = make_hazard_signals()
    #   signals["stall"]     = needs_stall(ID_EX, EX_MEM)
    #   signals["flush"]     = needs_flush(EX_MEM)
    #   fa, fb               = forwarding_unit(ID_EX, EX_MEM, MEM_WB)
    #   signals["forward_a"] = fa
    #   signals["forward_b"] = fb
    #   return signals
    raise NotImplementedError("Person 5: implement detect_hazards()")


def needs_stall(ID_EX: dict, EX_MEM: dict) -> bool:
    """
    Detect a load-use hazard requiring a stall bubble.

    A stall is needed when:
        - The instruction in EX_MEM is a LW (mem_read=True), AND
        - Its destination register (write_reg) matches rs or rt of
          the instruction currently in ID_EX

    Args:
        ID_EX  (dict): ID/EX latch (contains the consuming instruction)
        EX_MEM (dict): EX/MEM latch (contains the producing LW instruction)

    Returns:
        bool: True if a stall bubble must be inserted
    """
    # Check if current instruction is a load
    if not EX_MEM.get('mem_read', False):
        return False

    load_dest = EX_MEM.get('rt')
    src1 = ID_EX.get('rs')
    src2 = ID_EX.get('rt')

    # Check for hazard
    if load_dest == src1 or load_dest == src2:
        return True

    return False


def needs_flush(EX_MEM: dict) -> bool:
    """
    Detect a branch-taken condition requiring a pipeline flush.

    A flush is needed when:
        - The instruction in EX_MEM is a branch (branch=True), AND
        - The ALU zero_flag is True (for BEQ) or False (for BNE — handle both)

    Args:
        EX_MEM (dict): EX/MEM latch (branch decision is available here)

    Returns:
        bool: True if IF/ID and ID/EX should be flushed (replaced with NOPs)
    """
    #If its a branch it  need to be flushed
    if EX_MEM.get('branch', True):  
        return True
    
    # the ALU zero flag will not be a factor since it returns true for both
    return False


def forwarding_unit(ID_EX: dict, EX_MEM: dict, MEM_WB: dict) -> tuple:
    """
    Determine forwarding paths for ALU inputs A and B.

    EX forwarding (1-cycle-old result, highest priority):
        If EX_MEM.reg_write and EX_MEM.write_reg != 0
        and EX_MEM.write_reg == ID_EX.rs → forward_a = "EX_MEM"

    MEM forwarding (2-cycle-old result, lower priority):
        If MEM_WB.reg_write and MEM_WB.write_reg != 0
        and MEM_WB.write_reg == ID_EX.rs
        and NOT already covered by EX forwarding → forward_a = "MEM_WB"

    Same logic applies for forward_b (using ID_EX.rt).

    Args:
        ID_EX  (dict): Consuming instruction's latch
        EX_MEM (dict): 1-cycle-old producing instruction's latch
        MEM_WB (dict): 2-cycle-old producing instruction's latch

    Returns:
        tuple: (forward_a: str, forward_b: str)
               Each is one of "REG", "EX_MEM", "MEM_WB"
    """
    # TODO: Person 5 implements this
    raise NotImplementedError("Person 5: implement forwarding_unit()")


# ─────────────────────────────────────────────
# QUICK SELF-TEST (run: python person5_hazard.py)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    from common import make_pipeline_registers, make_instruction

    pl = make_pipeline_registers()

    # ── Test 1: Load-use hazard ──
    lw_instr = make_instruction("lw", "I", rs=0, rt=8, imm=0, raw="lw $t0, 0($zero)")
    add_instr = make_instruction("add", "R", rs=8, rt=9, rd=10, raw="add $t2,$t0,$t1")

    pl["EX_MEM"]["instruction"] = lw_instr
    pl["EX_MEM"]["mem_read"]    = True
    pl["EX_MEM"]["write_reg"]   = 8   # LW writes to $t0

    pl["ID_EX"]["instruction"]  = add_instr
    pl["ID_EX"]["rs"]           = 8   # ADD reads $t0 — hazard!
    pl["ID_EX"]["rt"]           = 9

    try:
        stall = needs_stall(pl["ID_EX"], pl["EX_MEM"])
        print(f"Load-use stall test: stall={stall}  expected True")
    except NotImplementedError as e:
        print(f"[STUB] {e}")

    # ── Test 2: No hazard ──
    pl2 = make_pipeline_registers()
    pl2["ID_EX"]["rs"] = 3
    pl2["ID_EX"]["rt"] = 4
    pl2["EX_MEM"]["mem_read"]  = True
    pl2["EX_MEM"]["write_reg"] = 8   # different register — no hazard

    try:
        stall = needs_stall(pl2["ID_EX"], pl2["EX_MEM"])
        print(f"No hazard test:      stall={stall}  expected False")
    except NotImplementedError as e:
        print(f"[STUB] {e}")

    # ── Test 3: EX forwarding ──
    pl3 = make_pipeline_registers()
    pl3["ID_EX"]["rs"]          = 8
    pl3["ID_EX"]["rt"]          = 9
    pl3["EX_MEM"]["reg_write"]  = True
    pl3["EX_MEM"]["write_reg"]  = 8   # EX_MEM writes $t0 — forward A

    try:
        fa, fb = forwarding_unit(pl3["ID_EX"], pl3["EX_MEM"], pl3["MEM_WB"])
        print(f"EX forwarding test:  forward_a={fa} expected EX_MEM, forward_b={fb} expected REG")
    except NotImplementedError as e:
        print(f"[STUB] {e}")