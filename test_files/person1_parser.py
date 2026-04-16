# person1_parser.py
# ECE 5367 Final Project
# Owner: Ricardo Perez

from common import make_instruction, SUPPORTED_INSTRUCTIONS, REGISTER_NAMES

def parse_program(source):
    raw_lines = source.split('\n')

    clean_lines = []
    # clean up the comments and blank lines first
    for line in raw_lines:
        if '#' in line:
            line = line.split('#')[0]
            
        line = line.strip()
        if line != "":
            clean_lines.append(line)

    label_map = {}
    pc = 0
    instructions = []

    # find labels and map them to the PC
    for line in clean_lines:
        if ':' in line:
            parts = line.split(':')
            lbl = parts[0].strip() 
            inst = parts[1].strip() 

            label_map[lbl] = pc

            # check if instruction is on the same line as the label
            if inst != "":
                instructions.append(inst)
                pc += 1
        else:
            instructions.append(line)
            pc += 1

    parsed = []
    for line in instructions:
        # print("debug line:", line)
        res = parse_line(line)
        if res != None:
            parsed.append(res)

    # fix the labels at the very end
    final_instructions = resolve_labels(parsed, label_map)
    return final_instructions


def decode_machine_code(bin_str):
    # slice up the 32 bits based on MIPS spec
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

    # R-Type
    if opcode == 0:
        i_type = "R"
        funct = int(funct_bin, 2)
        if funct == 32: op = "add"
        elif funct == 34: op = "sub"
        elif funct == 36: op = "and"
        elif funct == 37: op = "or"
        elif funct == 42: op = "slt"
        
    # I-Type / J-Type
    else:
        rd_num = None 
        
        # handle negative immediate values (two's complement)
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
    # sniffer to check if it's machine code
    is_bin = True
    if len(line) != 32:
        is_bin = False
    else:
        for char in line:
            if char != '0' and char != '1':
                is_bin = False

    if is_bin:
        return decode_machine_code(line)

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
    
    # figure out instruction pieces
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
        # split 0($zero) into pieces
        mem_part = words[2]
        split_mem = mem_part.split('(') 
        imm = int(split_mem[0]) 
        rs_str = split_mem[1].replace(")", "") 
        
    elif op == "beq" or op == "bne":
        i_type = "I"
        rs_str = words[1]
        rt_str = words[2]
        lbl = words[3] 

    elif op == "j":
        i_type = "J"
        lbl = words[1]

    rs_num = None
    rt_num = None
    rd_num = None

    # convert strings to ints for the common dict
    if rs_str in REGISTER_NAMES:
        rs_num = REGISTER_NAMES.index(rs_str)
    if rt_str in REGISTER_NAMES:
        rt_num = REGISTER_NAMES.index(rt_str)
    if rd_str in REGISTER_NAMES:
        rd_num = REGISTER_NAMES.index(rd_str)

    return make_instruction(
        op=op, type=i_type, rs=rs_num, rt=rt_num, rd=rd_num, 
        imm=imm, label=lbl, raw=raw
    )


def resolve_labels(instructions, label_map):
    for inst in instructions:
        if inst["label"] != None:
            target = inst["label"]
            
            # swap label text for the actual line number
            if target in label_map:
                inst["imm"] = label_map[target]
                inst["label"] = None            
                
    return instructions


if __name__ == "__main__":
    # quick test block
    test_program = """
    # test program
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
