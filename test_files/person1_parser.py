"""
person1_parser.py — Instruction Parser & Decoder
ECE 5367 Final Project: Pipelined Performance Analyzer
"""

from pathlib import Path

from common import make_instruction, SUPPORTED_INSTRUCTIONS, REGISTER_NAMES


R_FUNCT_TO_OP = {
    0x20: "add",
    0x22: "sub",
    0x24: "and",
    0x25: "or",
    0x2A: "slt",
    0x00: "nop",
}

OPCODE_TO_OP = {
    0x08: "addi",
    0x23: "lw",
    0x2B: "sw",
    0x04: "beq",
    0x05: "bne",
    0x02: "j",
}


def parse_program(source: str) -> list:
    """
    Parse either source text or a filesystem path.

    Supported line formats:
    - Assembly: add $t0, $t1, $t2
    - Binary machine code: 010101... (32 bits)
    - Hex machine code: 0x20080000 or 20080000
    """
    raw_text = _read_source(source)
    raw_lines = raw_text.splitlines()

    clean_lines = []
    for line in raw_lines:
        line = line.split("#", 1)[0].strip()
        if line:
            clean_lines.append(line)

    label_map = {}
    instruction_lines = []
    pc = 0

    for line in clean_lines:
        current = line
        while ":" in current:
            label, rest = current.split(":", 1)
            label = label.strip()
            if label:
                label_map[label] = pc
            current = rest.strip()
            if not current:
                break

        if current:
            instruction_lines.append(current)
            pc += 1

    parsed = []
    for line in instruction_lines:
        parsed_instr = parse_line(line)
        if parsed_instr is not None:
            parsed.append(parsed_instr)

    return resolve_labels(parsed, label_map)


def _read_source(source: str) -> str:
    if "\n" in source or "\r" in source:
        return source

    path = Path(source)
    if path.exists() and path.is_file():
        return path.read_text(encoding="utf-8")

    return source


def decode_machine_word(word: int) -> dict:
    opcode = (word >> 26) & 0x3F
    rs = (word >> 21) & 0x1F
    rt = (word >> 16) & 0x1F
    rd = (word >> 11) & 0x1F
    funct = word & 0x3F
    imm_u16 = word & 0xFFFF
    imm_s16 = imm_u16 if imm_u16 < 0x8000 else imm_u16 - 0x10000
    j_addr = word & 0x03FFFFFF

    if opcode == 0:
        op = R_FUNCT_TO_OP.get(funct)
        if op is None:
            raise ValueError(f"Unsupported R-type funct: 0x{funct:02X}")
        return make_instruction(op=op, instr_type="R", rs=rs, rt=rt, rd=rd, imm=0, raw=f"0x{word:08X}")

    op = OPCODE_TO_OP.get(opcode)
    if op is None:
        raise ValueError(f"Unsupported opcode: 0x{opcode:02X}")

    if op == "j":
        return make_instruction(op=op, instr_type="J", rs=0, rt=0, rd=0, imm=j_addr, raw=f"0x{word:08X}")

    return make_instruction(op=op, instr_type="I", rs=rs, rt=rt, rd=0, imm=imm_s16, raw=f"0x{word:08X}")


def parse_line(line: str):
    raw = line.strip()
    if not raw:
        return None

    if len(raw) == 32 and all(ch in "01" for ch in raw):
        return decode_machine_word(int(raw, 2))

    hex_candidate = raw[2:] if raw.lower().startswith("0x") else raw
    if len(hex_candidate) == 8 and all(ch in "0123456789abcdefABCDEF" for ch in hex_candidate):
        return decode_machine_word(int(hex_candidate, 16))

    line_no_commas = raw.replace(",", " ")
    words = [w for w in line_no_commas.split() if w]
    if not words:
        return None

    op = words[0].lower()
    if op not in SUPPORTED_INSTRUCTIONS:
        raise ValueError(f"Unsupported instruction: {op}")

    rs = 0
    rt = 0
    rd = 0
    imm = 0
    label = None
    instr_type = SUPPORTED_INSTRUCTIONS[op]["type"]

    if op in {"add", "sub", "and", "or", "slt"}:
        if len(words) != 4:
            raise ValueError(f"Invalid R-type format: {raw}")
        rd = _reg_num(words[1])
        rs = _reg_num(words[2])
        rt = _reg_num(words[3])

    elif op == "addi":
        if len(words) != 4:
            raise ValueError(f"Invalid addi format: {raw}")
        rt = _reg_num(words[1])
        rs = _reg_num(words[2])
        imm = int(words[3], 0)

    elif op in {"lw", "sw"}:
        if len(words) != 3:
            raise ValueError(f"Invalid {op} format: {raw}")
        rt = _reg_num(words[1])
        imm_str, rs_str = _split_mem_operand(words[2])
        imm = int(imm_str, 0)
        rs = _reg_num(rs_str)

    elif op in {"beq", "bne"}:
        if len(words) != 4:
            raise ValueError(f"Invalid {op} format: {raw}")
        rs = _reg_num(words[1])
        rt = _reg_num(words[2])
        target = words[3]
        if target.lstrip("-").isdigit():
            imm = int(target, 10)
        else:
            label = target

    elif op == "j":
        if len(words) != 2:
            raise ValueError(f"Invalid j format: {raw}")
        target = words[1]
        if target.lstrip("-").isdigit():
            imm = int(target, 10)
        else:
            label = target

    return make_instruction(
        op=op,
        instr_type=instr_type,
        rs=rs,
        rt=rt,
        rd=rd,
        imm=imm,
        label=label,
        raw=raw,
    )


def _split_mem_operand(token: str):
    if "(" not in token or not token.endswith(")"):
        raise ValueError(f"Invalid memory operand: {token}")
    imm_str, rs_part = token.split("(", 1)
    return imm_str, rs_part[:-1]


def _reg_num(name: str) -> int:
    if name not in REGISTER_NAMES:
        raise ValueError(f"Unknown register name: {name}")
    return REGISTER_NAMES[name]


def resolve_labels(instructions: list, label_map: dict) -> list:
    for idx, inst in enumerate(instructions):
        if inst["label"] is None:
            continue

        target = inst["label"]
        if target not in label_map:
            if target.lower() == "end":
                label_map[target] = len(instructions)
            else:
                raise ValueError(f"Undefined label '{target}' referenced by: {inst['raw']}")

        if inst["op"] in {"beq", "bne"}:
            inst["imm"] = label_map[target] - (idx + 1)
        else:
            inst["imm"] = label_map[target]

        inst["label"] = None

    return instructions


if __name__ == "__main__":
    test_program = """
    addi $t0, $zero, 10
    0x01095020
    beq  $t0, $t2, LOOP
    LOOP: j LOOP
    """

    parsed = parse_program(test_program)
    print(f"Parsed {len(parsed)} instructions")
    for i, instr in enumerate(parsed):
        print(f"[{i}] {instr}")
