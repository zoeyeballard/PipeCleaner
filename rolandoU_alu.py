"""
rolandoU_alu.py — ALU & Register File
ECE 5367 Final Project: Pipelined Performance Analyzer
Owner: Rolando Steve Uribe

RESPONSIBILITY:
    Implement the ALU (arithmetic/logic operations) and the register file
    (read/write). Pure logic — no dependency on any other team member's code.

INTERFACE CONTRACT (do not change signatures):
    alu_execute(op, a, b)              -> int
    register_read(cpu_state, rs, rt)   -> (int, int)
    register_write(cpu_state, rd, val) -> dict
    sign_extend(imm, bits=16)          -> int

TESTING:
    Run this file directly: python rolandoU_alu.py
"""

from common import make_cpu_state

# -----------------------------------------------------------------------------
# PROTOTYPE FINALIZATION NOTES (treat this as canonical Person 2 module)
# -----------------------------------------------------------------------------
# This file should be considered the single source of truth for ALU/register
# behavior across the project.
#
# Finalization checklist to align with prototype branch integration:
# 1) Keep all imports in other modules pointed at rolandoU_alu.py directly.
# 2) Preserve the four public API signatures unchanged:
#    - alu_execute(op, a, b)
#    - register_read(cpu_state, rs, rt)
#    - register_write(cpu_state, rd, value)
#    - sign_extend(imm, bits=16)
# 3) Keep this module pure logic (no parser/pipeline dependencies).
# 4) If analyzer-specific helpers are needed later, add them as optional helpers
#    without changing existing function contracts.
# 5) Keep self-tests here as the ALU truth test used by the team.


# ─────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────

# CURRENT FUNCTION: canonical ALU operation implementation.
# FINALIZATION NOTE: keep behavior stable because simulator modules depend on
# result and zero_flag semantics exactly as implemented here.
def alu_execute(op: str, a: int, b: int) -> tuple:
    """
    Perform an ALU operation.

    Args:
        op (str): Operation name — "add", "sub", "and", "or", "slt"
        a  (int): First operand (value of rs, after forwarding)
        b  (int): Second operand (value of rt OR sign-extended immediate)

    Returns:
        tuple: (result: int, zero_flag: bool)
               zero_flag is True when result == 0 (used for BEQ)

    Supported ops: "add", "sub", "and", "or", "slt"
    Raise ValueError for unsupported ops.
    """
    if op == "add":
        result = a + b
    elif op == "sub":
        result = a - b
    elif op == "and":
        result = a & b
    elif op == "or":
        result = a | b
    elif op == "slt":
        result = 1 if a < b else 0   # signed "set less than"
    else:
        raise ValueError(f"Unsupported ALU operation: {op}")
    
    zero_flag = (result == 0)
    return result, zero_flag



# CURRENT FUNCTION: canonical register read implementation.
# FINALIZATION NOTE: preserve hardwired $zero read semantics.
def register_read(cpu_state: dict, rs: int, rt: int) -> tuple:
    """
    Read two registers from the register file.

    Args:
        cpu_state (dict): Current CPU state (from make_cpu_state())
        rs        (int):  Index of first source register
        rt        (int):  Index of second source register

    Returns:
        tuple: (val_rs: int, val_rt: int)

    Note: $zero (register 0) always returns 0.
    """
    registers = cpu_state["registers"]
    
    # $zero is hardwired to 0
    val_rs = 0 if rs == 0 else registers[rs]
    val_rt = 0 if rt == 0 else registers[rt]
    
    return val_rs, val_rt


# CURRENT FUNCTION: canonical register write implementation.
# FINALIZATION NOTE: preserve write-ignore behavior for register 0.
def register_write(cpu_state: dict, rd: int, value: int) -> dict:
    """
    Write a value to a register. Returns updated cpu_state.

    Args:
        cpu_state (dict): Current CPU state
        rd        (int):  Destination register index
        value     (int):  Value to write

    Returns:
        dict: Updated cpu_state (modify in-place and return)

    Note: Writes to $zero (register 0) are silently ignored.
    """
    if rd != 0:  # ignore writes to $zero
        cpu_state["registers"][rd] = value
    
    return cpu_state


# CURRENT FUNCTION: canonical sign-extension helper.
# FINALIZATION NOTE: keep this logic as shared immediate normalization helper
# for parser/simulator execution paths.
def sign_extend(imm: int, bits: int = 16) -> int:
    """
    Sign-extend an immediate value from `bits` width to Python int.

    Args:
        imm  (int): Raw immediate value (unsigned, as parsed)
        bits (int): Original bit width (default 16 for MIPS I-type)

    Returns:
        int: Sign-extended value (may be negative)

    Example:
        sign_extend(0xFFFF, 16) -> -1
        sign_extend(0x0005, 16) ->  5
    """
    if imm >= (1 << (bits - 1)):
        imm -= (1 << bits)
    return imm


# ─────────────────────────────────────────────
# QUICK SELF-TEST (run: python person2_alu.py)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        ("add",  5,  3,  8,    False),
        ("sub",  5,  5,  0,    True),
        ("sub",  3,  7, -4,    False),
        ("and",  0b1100, 0b1010, 0b1000, False),
        ("or",   0b1100, 0b1010, 0b1110, False),
        ("slt",  3,  5,  1,    False),
        ("slt",  5,  3,  0,    True),
    ]

    print("ALU Tests:")
    for op, a, b, expected_result, expected_zero in tests:
        try:
            result, zero = alu_execute(op, a, b)
            status = "PASS" if result == expected_result and zero == expected_zero else "FAIL"
            print(f"  [{status}] {op}({a}, {b}) = {result} (zero={zero})")
        except NotImplementedError as e:
            print(f"  [STUB] {e}")
            break

    print("\nRegister File Tests:")
    state = make_cpu_state()
    state["registers"][8] = 42   # $t0 = 42
    state["registers"][9] = 7    # $t1 = 7
    try:
        v_rs, v_rt = register_read(state, 8, 9)
        print(f"  register_read($t0, $t1) = ({v_rs}, {v_rt})  expected (42, 7)")
        state = register_write(state, 10, 99)
        print(f"  register_write($t2, 99) -> $t2 = {state['registers'][10]}  expected 99")
        state = register_write(state, 0, 999)
        print(f"  register_write($zero, 999) -> $zero = {state['registers'][0]}  expected 0")
    except NotImplementedError as e:
        print(f"  [STUB] {e}")

    print("\nSign Extension Tests:")
    se_tests = [(0xFFFF, 16, -1), (0x0005, 16, 5), (0x8000, 16, -32768)]
    for val, bits, expected in se_tests:
        try:
            result = sign_extend(val, bits)
            status = "PASS" if result == expected else "FAIL"
            print(f"  [{status}] sign_extend({hex(val)}, {bits}) = {result}  expected {expected}")
        except NotImplementedError as e:
            print(f"  [STUB] {e}")
            break
