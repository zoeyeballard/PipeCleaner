"""
person1_parser.py — Instruction Parser & Decoder
ECE 5367 Final Project: Pipelined Performance Analyzer
Owner: Ricardo Perez

RESPONSIBILITY:
    Take a MIPS assembly program (as a text string or file path) and return
    a list of instruction dicts using make_instruction() from common.py.
    This module has NO dependencies on any other team member's code.

INTERFACE CONTRACT:
    parse_program(source)
    parse_line(line)
    resolve_labels(instructions, label_map)

TESTING:
    Run this file directly: python person1_parser.py
"""

from common import (
    make_instruction,
    SUPPORTED_INSTRUCTIONS,
    REGISTER_NAMES,
)

def parse_program(source):
    # Break the giant block of text into individual lines we can actually read
    raw_lines = source.split('\n')

    # --- PASS 1: CLEANUP ---
    clean_lines = []
    
    for line in raw_lines:
        # If there's a comment, we only want the actual code before the '#'
        if '#' in line:
            parts = line.split('#')
            line = parts[0]
            
        # Strip off any weird invisible spaces or newlines from the edges
        line = line.strip()

        # Throw away blank lines so they don't crash our parser later
        if line != "":
            clean_lines.append(line)

    # --- PASS 2: FIND LABELS ---
    label_map = {}
    pc_index = 0
    instructions_only = []

    for line in clean_lines:
        # Check if the line has a label (like "LOOP:")
        if ':' in line:
            parts = line.split(':')
            label_name = parts[0].strip() 
            instruction_part = parts[1].strip() 

            # Map the label name to the current line number (Program Counter)
            label_map[label_name] = pc_index

            # Sometimes people put the label and instruction on the same line
            if instruction_part != "":
                instructions_only.append(instruction_part)
                pc_index = pc_index + 1
        else:
            # It's just a normal instruction
            instructions_only.append(line)
            pc_index = pc_index + 1

    # --- PASS 3: PARSE INSTRUCTIONS ---
    parsed_instructions = []
    for line in instructions_only:
        inst_dict = parse_line(line)
        if inst_dict != None:
            parsed_instructions.append(inst_dict)

    # --- PASS 4: LINK LABELS ---
    # We have to do this at the very end so that forward-jumping branches work
    final_instructions = resolve_labels(parsed_instructions, label_map)
    
    return final_instructions


def decode_machine_code(binary_string):
    """Helper function to decode 32-bit binary strings."""
    # Hardcode the slices based on the official MIPS hardware reference
    opcode_bin = binary_string[0:6]
    rs_bin     = binary_string[6:11]
    rt_bin     = binary_string[11:16]
    rd_bin     = binary_string[16:21]
    funct_bin  = binary_string[26:32]
    imm_bin    = binary_string[16:32]
    
    # Convert the raw binary text (like '1010') into real integers
    opcode = int(opcode_bin, 2)
    rs_num = int(rs_bin, 2)
    rt_num = int(rt_bin, 2)
    rd_num = int(rd_bin, 2)
    
    op = None
    imm = None
    label_ref = None
    instr_type = None

    # R-Type instructions all share opcode 0, so we have to check 'funct'
    if opcode == 0:
        instr_type = "R"
        funct = int(funct_bin, 2)
        if funct == 32: op = "add"
        elif funct == 34: op = "sub"
        elif funct == 36: op = "and"
        elif funct == 37: op = "or"
        elif funct == 42: op = "slt"
        
    # I-Type / J-Type instructions
    else:
        rd_num = None # I-Types don't use the destination register
        
        # Two's complement trick to handle negative numbers in binary
        if imm_bin[0] == '1': 
            imm = int(imm_bin, 2) - 65536 
        else:
            imm = int(imm_bin, 2)

        if opcode == 8: 
            op = "addi"
            instr_type = "I"
        elif opcode == 35: 
            op = "lw"
            instr_type = "I"
        elif opcode == 43: 
            op = "sw"
            instr_type = "I"
        elif opcode == 4: 
            op = "beq"
            instr_type = "I"
        elif opcode == 5: 
            op = "bne"
            instr_type = "I"
        elif opcode == 2:
            op = "j"
            instr_type = "J"

    return make_instruction(
        op=op, type=instr_type, rs=rs_num, rt=rt_num, rd=rd_num, 
        imm=imm, label=label_ref, raw=binary_string
    )


def parse_line(line):
    """
    Parse a single MIPS assembly instruction line into an instruction dict.
    """
    # 1. THE SNIFFER: Did Person 6 give us a machine code string?
    # Check if it's exactly 32 chars long and only contains 1s and 0s
    is_machine_code = True
    if len(line) != 32:
        is_machine_code = False
    else:
        for char in line:
            if char != '0' and char != '1':
                is_machine_code = False

    if is_machine_code == True:
        return decode_machine_code(line)

    # 2. NORMAL ASSEMBLY PARSING
    raw_line = line
    
    # Delete commas to make splitting the string 100x easier
    line = line.replace(",", "")
    words = line.split()
    
    op = words[0]
    rs_str = None
    rt_str = None
    rd_str = None
    imm = None
    label_ref = None
    instr_type = None
    
    # R-Type: simple 3-register operations
    if op == "add" or op == "sub" or op == "and" or op == "or" or op == "slt":
        instr_type = "R"
        rd_str = words[1]
        rs_str = words[2]
        rt_str = words[3]
        
    # I-Type: math with an immediate value
    elif op == "addi":
        instr_type = "I"
        rt_str = words[1]
        rs_str = words[2]
        imm = int(words[3]) 
        
    # Memory: MIPS syntax is weird here (e.g., 0($zero)), so we split on '('
    elif op == "lw" or op == "sw":
        instr_type = "I"
        rt_str = words[1]
        memory_part = words[2]
        mem_split = memory_part.split('(') 
        
        imm = int(mem_split[0]) # the offset number
        rs_str = mem_split[1].replace(")", "") # strip the trailing bracket
        
    # Branches
    elif op == "beq" or op == "bne":
        instr_type = "I"
        rs_str = words[1]
        rt_str = words[2]
        label_ref = words[3] 

    # Jumps
    elif op == "j":
        instr_type = "J"
        label_ref = words[1]

    # Map the human-readable string names ("$t0") to integer indices (8) 
    # so Person 2's register array can actually use them
    rs_num = None
    rt_num = None
    rd_num = None

    if rs_str in REGISTER_NAMES:
        rs_num = REGISTER_NAMES.index(rs_str)
    if rt_str in REGISTER_NAMES:
        rt_num = REGISTER_NAMES.index(rt_str)
    if rd_str in REGISTER_NAMES:
        rd_num = REGISTER_NAMES.index(rd_str)

    # Package everything up into the team's shared dictionary format
    return make_instruction(
        op=op, type=instr_type, rs=rs_num, rt=rt_num, rd=rd_num, 
        imm=imm, label=label_ref, raw=raw_line
    )


def resolve_labels(instructions, label_map):
    """
    Replace label strings in branch/jump instructions with PC indices.
    """
    for inst in instructions:
        # If this instruction is pointing to a text label...
        if inst["label"] != None:
            target = inst["label"]
            
            # ...and we know where that label is, swap it out for the line number
            if target in label_map:
                inst["imm"] = label_map[target]
                inst["label"] = None            
                
    return instructions


# ─────────────────────────────────────────────
# QUICK SELF-TEST (run: python person1_parser.py)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # A quick test to make sure we don't break the pipeline
    test_program = """
    # Simple test program with Assembly AND Machine Code
    LOOP: addi $t0, $zero, 10
    00000001000010010101000000100000 
    beq  $t0, $t2, LOOP
    """

    try:
        result = parse_program(test_program)
        print("Parsed {} instructions:".format(len(result)))
        for i, instr in enumerate(result):
            print("  [{}] {}".format(i, instr))
    except Exception as e:
        print("Error: {}".format(e))
