# person1_parser.py
# ECE 5367 Final Project
# Owner: Ricardo Perez

import os # Needed to check if a string is a file path
from common import make_instruction, SUPPORTED_INSTRUCTIONS, REGISTER_NAMES

# -----------------------------------------------------------------------------
# HELPERS
# -----------------------------------------------------------------------------

def _read_source(source):
    """Return raw source text from either inline text or a file path."""
    # Check if the text provided is actually a file name that exists
    if os.path.isfile(source):
        # Open the file and read all the text inside it
        with open(source, 'r') as file:
            return file.read()
    
    # If it's not a file, it must be a normal string of text, so just return it
    return source


def decode_machine_word(word):
    """Decode a 32-bit integer (hex or binary) into canonical format."""
    # If it starts with 0x, it is Hexadecimal
    if word.startswith("0x"):
        # Convert hex text to an integer, then convert that integer to a 32-bit binary string
        number = int(word, 16)
        # The '032b' tells Python to format it as Binary and pad it to 32 zeros
        bin_str = format(number, '032b') 
    else:
        # It is already binary
        bin_str = word
        
    return decode_machine_code(bin_str)


def _split_mem_operand(token):
    """Parse tokens like 4($t0) into (offset, base_register)."""
    parts = token.split('(')
    imm = int(parts[0])
    rs_str = parts[1].replace(")", "")
    return imm, rs_str


def _reg_num(name):
    """Map register name string to numeric register index."""
    if name in REGISTER_NAMES:
        return REGISTER_NAMES.index(name)
    return None

# -----------------------------------------------------------------------------
# MAIN PARSERS
# -----------------------------------------------------------------------------

def parse_program(source):
    # UPDATE: Use our new helper to read files if necessary
    text_data = _read_source(source)
    raw_lines = text_data.split('\n')

    clean_lines = []
    for line in raw_lines:
        if '#' in line:
            line = line.split('#')[0]
            
        line = line.strip()
        if line != "":
            clean_lines.append(line)

    label_map = {}
    pc = 0
    instructions = []

    for line in clean_lines:
        if ':' in line:
            parts = line.split(':')
            lbl = parts[0].strip() 
            inst = parts[1].strip() 

            label_map[lbl] = pc

            if inst != "":
                instructions.append(inst)
                pc += 1
        else:
            instructions.append(line)
            pc += 1

    parsed = []
    for line in instructions:
        res = parse_line(line)
        if res != None:
            parsed.append(res)

    final_instructions = resolve_labels(parsed, label_map)
    return final_instructions


def decode_machine_code(bin_str):
    op_bin = bin_str[0:6]
    rs_bin = bin_str[6:11]
    rt_bin = bin_str[11:16]
    rd_bin = bin_str[16:21]
    funct_bin = bin_str[26:32]
    imm_bin = bin_str[16:32]
    
    opcode = int(op_bin, 2)
    rs_num = int(rs_bin, 2)
    rt_num = int(rt_bin, 2)
    rd_num = int(rd_bin, 2)
    
    op = None
    imm = None
    lbl_ref = None
    i_type = None

    if opcode == 0:
        i_type = "R"
        funct = int(funct_bin, 2)
        if funct == 32: op = "add"
        elif funct == 34: op = "sub"
        elif funct == 36: op = "and"
        elif funct == 37: op = "or"
        elif funct == 42: op = "slt"
        
    else:
        rd_num = None 
        
        if imm_bin[0] == '1': 
            imm = int(imm_bin, 2) - 65536 
        else:
            imm = int(imm_bin, 2)

        if opcode == 8: 
            op = "addi"
            i_type = "I"
        elif opcode == 35: 
            op = "lw"
            i_type = "I"
        elif opcode == 43: 
            op = "sw"
            i_type = "I"
        elif opcode == 4: 
            op = "beq"
            i_type = "I"
        elif opcode == 5: 
            op = "bne"
            i_type = "I"
        elif opcode == 2:
            op = "j"
            i_type = "J"

    return make_instruction(
        op=op, type=i_type, rs=rs_num, rt=rt_num, rd=rd_num, 
        imm=imm, label=lbl_ref, raw=bin_str
    )


def parse_line(line):
    # UPDATE: Check for Hexadecimal first
    if line.startswith("0x"):
        return decode_machine_word(line)
        
    # Check for Binary
    is_bin = True
    if len(line) != 32:
        is_bin = False
    else:
        for char in line:
            if char != '0' and char != '1':
                is_bin = False

    if is_bin:
        return decode_machine_word(line)

    raw = line
    line = line.replace(",", "")
    words = line.split()
    
    op = words[0]
    rs_str = None
    rt_str = None
    rd_str = None
    imm = None
    lbl = None
    i_type = None
    
    if op in ["add", "sub", "and", "or", "slt"]:
        i_type = "R"
        rd_str = words[1]
        rs_str = words[2]
        rt_str = words[3]
        
    elif op == "addi":
        i_type = "I"
        rt_str = words[1]
        rs_str = words[2]
        imm = int(words[3]) 
        
    elif op == "lw" or op == "sw":
        i_type = "I"
        rt_str = words[1]
        # UPDATE: Using our new helper function
        imm, rs_str = _split_mem_operand(words[2])
        
    elif op == "beq" or op == "bne":
        i_type = "I"
        rs_str = words[1]
        rt_str = words[2]
        lbl = words[3] 

    elif op == "j":
        i_type = "J"
        lbl = words[1]

    # UPDATE: Using our new helper function
    rs_num = _reg_num(rs_str)
    rt_num = _reg_num(rt_str)
    rd_num = _reg_num(rd_str)

    return make_instruction(
        op=op, type=i_type, rs=rs_num, rt=rt_num, rd=rd_num, 
        imm=imm, label=lbl, raw=raw
    )


def resolve_labels(instructions, label_map):
    # We need the index 'i' to calculate PC-relative branches
    for i, inst in enumerate(instructions):
        if inst["label"] != None:
            target = inst["label"]
            
            if target in label_map:
                target_pc = label_map[target]
                
                # UPDATE: Handle relative vs absolute jumping
                if inst["op"] == "beq" or inst["op"] == "bne":
                    # Branches are relative to the current PC
                    inst["imm"] = target_pc - i - 1
                else:
                    # Jumps are absolute (they just go exactly to that line)
                    inst["imm"] = target_pc
                    
                inst["label"] = None            
                
    return instructions


if __name__ == "__main__":
    test_program = """
    # test program
    LOOP: addi $t0, $zero, 10
    00000001000010010101000000100000 
    0x114A0003
    beq  $t0, $t2, LOOP
    """

    try:
        result = parse_program(test_program)
        print("Parsed {} instructions:".format(len(result)))
        for i, instr in enumerate(result):
            print("  [{}] {}".format(i, instr))
    except Exception as e:
        print("Error: {}".format(e))
