"""
person1_parser.py — Instruction Parser & Decoder
ECE 5367 Final Project: Pipelined Performance Analyzer
Owner: Ricardo Perez

RESPONSIBILITY:
    Take a MIPS assembly program (as a text string or file path) and return
    a list of instruction dicts using make_instruction() from common.py.
    This module has NO dependencies on any other team member's code.

INTERFACE CONTRACT (do not change signatures):
    parse_program(source: str) -> list[dict]
    parse_line(line: str)      -> dict | None
    resolve_labels(instructions: list[dict]) -> list[dict]

TESTING:
    Run this file directly: python person1_parser.py
"""

from common import (
    make_instruction,
    SUPPORTED_INSTRUCTIONS,
    REGISTER_NAMES,
)


# ─────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────

def parse_program(source: str) -> list:
    """
    Parse a full MIPS assembly program.

    Args:
        source (str): Multi-line MIPS assembly text
                      (labels allowed, comments with '#')

    Returns:
        list[dict]: Ordered list of instruction dicts ready for simulation.
                    Branch targets are resolved to PC indices (integers).

    Example:
        program = '''
            addi $t0, $zero, 5
            addi $t1, $zero, 3
            add  $t2, $t0, $t1
        '''
        instructions = parse_program(program)
    """
    # TODO: Person 1 implements this
    # Suggested steps:
    #   1. Strip comments and blank lines
    #   2. First pass: collect label -> line_index mapping
    #   3. Second pass: call parse_line() on each non-label line
    #   4. Call resolve_labels() to convert label references to PC offsets
    raise NotImplementedError("Person 1: implement parse_program()")


def parse_line(line: str) -> dict:
    """
    Parse a single MIPS assembly instruction line into an instruction dict.

    Args:
        line (str): A single cleaned instruction string e.g. "add $t0, $t1, $t2"

    Returns:
        dict: Instruction dict from make_instruction(), or None if line is empty/label-only.

    Hints:
        - Split on commas and whitespace
        - Look up register names using REGISTER_NAMES
        - Handle sign extension for immediates (imm can be negative)
        - Use SUPPORTED_INSTRUCTIONS to validate ops
    """
    # TODO: Person 1 implements this
    raise NotImplementedError("Person 1: implement parse_line()")


def resolve_labels(instructions: list, label_map: dict) -> list:
    """
    Replace label strings in branch/jump instructions with PC indices.

    Args:
        instructions (list[dict]): Output of the first parse pass
        label_map    (dict):       { label_name: pc_index }

    Returns:
        list[dict]: Same instructions with imm fields resolved to integers
    """
    # TODO: Person 1 implements this
    raise NotImplementedError("Person 1: implement resolve_labels()")


# ─────────────────────────────────────────────
# QUICK SELF-TEST (run: python person1_parser.py)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    test_program = """
    # Simple test program
    addi $t0, $zero, 10
    addi $t1, $zero, 20
    add  $t2, $t0, $t1
    sw   $t2, 0($zero)
    lw   $t3, 0($zero)
    """

    try:
        result = parse_program(test_program)
        print(f"Parsed {len(result)} instructions:")
        for i, instr in enumerate(result):
            print(f"  [{i}] {instr}")
    except NotImplementedError as e:
        print(f"[STUB] {e}")
        print("Expected output: list of 5 instruction dicts")
