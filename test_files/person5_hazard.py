"""
person5_hazard.py — Static Hazard Analyzer
ECE 5367 Final Project: Pipelined Performance Analyzer
"""

from common import make_hazard_signals


def _read_regs(instr):
    op = instr.get("op", "")
    rs = instr.get("rs", 0)
    rt = instr.get("rt", 0)

    if op in {"add", "sub", "and", "or", "slt", "beq", "bne"}:
        return {rs, rt}
    if op in {"addi", "lw", "sw"}:
        return {rs}
    return set()


def _write_reg(instr):
    op = instr.get("op", "")
    if op in {"add", "sub", "and", "or", "slt"}:
        return instr.get("rd", 0)
    if op in {"addi", "lw"}:
        return instr.get("rt", 0)
    return 0


def analyze_hazards(instructions):
    raw_hazards = 0
    load_use_hazards = 0
    branch_instructions = 0

    for i in range(1, len(instructions)):
        prev_instr = instructions[i - 1]
        curr_instr = instructions[i]

        prev_write = _write_reg(prev_instr)
        curr_reads = _read_regs(curr_instr)

        if curr_instr.get("op") in {"beq", "bne"}:
            branch_instructions += 1

        if prev_write != 0 and prev_write in curr_reads:
            raw_hazards += 1
            if prev_instr.get("op") == "lw":
                load_use_hazards += 1

    stall_cycles = load_use_hazards

    return {
        "raw_hazards": raw_hazards,
        "load_use_hazards": load_use_hazards,
        "branch_instructions": branch_instructions,
        "stall_cycles": stall_cycles,
    }


def detect_hazards(*args):
    """
    Compatibility wrapper.

    Preferred usage:
        detect_hazards(instructions)
    """
    if len(args) == 1 and isinstance(args[0], list):
        return analyze_hazards(args[0])

    signals = make_hazard_signals()
    return signals


def needs_stall(ID_EX, EX_MEM):
    if not EX_MEM.get("mem_read", False):
        return False
    write_reg = EX_MEM.get("write_reg", 0)
    return write_reg != 0 and write_reg in {ID_EX.get("rs", 0), ID_EX.get("rt", 0)}


def needs_flush(EX_MEM):
    return bool(EX_MEM.get("branch_taken", False))


def forwarding_unit(ID_EX, EX_MEM, MEM_WB):
    forward_a = "REG"
    forward_b = "REG"

    rs = ID_EX.get("rs", 0)
    rt = ID_EX.get("rt", 0)

    ex_reg_write = EX_MEM.get("reg_write", False)
    ex_write_reg = EX_MEM.get("write_reg", 0)
    wb_reg_write = MEM_WB.get("reg_write", False)
    wb_write_reg = MEM_WB.get("write_reg", 0)

    if ex_reg_write and ex_write_reg != 0 and ex_write_reg == rs:
        forward_a = "EX_MEM"
    elif wb_reg_write and wb_write_reg != 0 and wb_write_reg == rs:
        forward_a = "MEM_WB"

    if ex_reg_write and ex_write_reg != 0 and ex_write_reg == rt:
        forward_b = "EX_MEM"
    elif wb_reg_write and wb_write_reg != 0 and wb_write_reg == rt:
        forward_b = "MEM_WB"

    return forward_a, forward_b


if __name__ == "__main__":
    from person1_parser import parse_program

    sample = """
    lw   $t0, 0($zero)
    add  $t1, $t0, $t2
    add  $t3, $t1, $t4
    beq  $t3, $t0, done
    done: sw $t3, 4($zero)
    """

    instructions = parse_program(sample)
    result = analyze_hazards(instructions)
    print("Hazard analyzer self-test")
    print(result)
