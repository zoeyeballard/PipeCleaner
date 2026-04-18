# person1_parser.py
# ECE 5367 Final Project
# Owner: Ricardo Perez

import os # Needed so we can check if a string is a real file on the computer
from common import make_instruction, SUPPORTED_INSTRUCTIONS, REGISTER_NAMES


# HELPERS (Small tools to make the main code easier to read)

def _read_source(source):
    """
    Checks if the user gave us a file name (like 'test.asm') or just raw text.
    If it's a file, it opens it and reads the text inside.
    """
    # Ask the operating system: "Does a file with this exact name exist?"
    if os.path.isfile(source):
        # If yes, open it in 'r' (read) mode so we don't accidentally overwrite it
        with open(source, 'r') as file:
            return file.read() # Spit out all the text from the file
    
    # If the file doesn't exist, we assume 'source' is already just a block of text
    return source


def decode_machine_word(word):
    """
    Takes a string of machine code (either Hexadecimal or Binary) 
    and guarantees it becomes a 32-bit binary string for the CPU to read.
    """
    # Hexadecimal numbers always start with '0x' (like 0x114A0003)
    if word.startswith("0x"):
        # Step 1: Turn the hex text into a standard integer math number
        # The '16' tells Python it's base-16 (Hex)
        number = int(word, 16)
        
        # Step 2: Turn that integer into a string of 1s and 0s. 
        # '032b' means: make it Binary ('b') and pad it with leading Zeros ('0') so it is exactly 32 characters long.
        bin_str = format(number, '032b') 
    else:
        # If it doesn't start with 0x, we assume it's already a binary string
        bin_str = word
        
    # Send our clean 32-bit string to the main decoding function
    return decode_machine_code(bin_str)


def _split_mem_operand(token):
    """
    Takes a memory text like '4($t0)' and splits it into the number and the register.
    """
    # Cut the string into two halves at the open parenthesis
    # '4($t0)' becomes -> parts[0] = '4' and parts[1] = '$t0)'
    parts = token.split('(')
    
    imm = int(parts[0]) # Turn the '4' into a real integer
    rs_str = parts[1].replace(")", "") # Erase the closing parenthesis to just get '$t0'
    
    return imm, rs_str


def _reg_num(name):
    """
    Takes a string like '$t0' and looks up its official MIPS hardware number.
    """
    # If the name exists in our team's shared list of registers
    if name in REGISTER_NAMES:
        # Return its index (its position in the list)
        return REGISTER_NAMES[name]
    return None


# MAIN PARSERS 


def parse_program(source):
    """
    The main boss function. It takes the entire program, cleans it, finds labels,
    and translates every line into a dictionary the CPU simulator can understand.
    """
    # Get the text (either by reading the file or using the text directly)
    text_data = _read_source(source)
    
    # Split the giant block of text into a list of individual lines
    raw_lines = text_data.split('\n')

    # PHASE 1: Clean the text
    clean_lines = []
    for line in raw_lines:
        # If there is a comment (#), chop it off and only keep the code before it
        if '#' in line:
            line = line.split('#')[0]
            
        # Erase any invisible spaces or tabs at the very beginning or end of the line
        line = line.strip()
        
        # If the line isn't totally empty, save it to our clean list
        if line != "":
            clean_lines.append(line)

    # PHASE 2: Find Labels
    label_map = {} # A dictionary to remember where labels point (e.g., {"LOOP": 5})
    pc = 0         # The Program Counter (keeps track of what line number we are on)
    instructions = [] # A list to hold just the pure instruction text

    for line in clean_lines:
        # A colon means this line contains a label
        if ':' in line:
            # Cut the line in half at the colon
            parts = line.split(':')
            lbl = parts[0].strip()   # The label name (e.g., 'LOOP')
            inst = parts[1].strip()  # The instruction next to it (e.g., 'addi $t0, $zero, 10')

            # Save the label name and the current line number to our map
            label_map[lbl] = pc

            # If there was actually an instruction next to the label, save it
            if inst != "":
                instructions.append(inst)
                pc += 1 # We only increase the PC when we find a real instruction
        else:
            # It's a normal instruction without a label, so just save it
            instructions.append(line)
            pc += 1

    # PHASE 3: Translate Instructions
    parsed = []
    for line in instructions:
        # Send the pure text line to be broken down into pieces
        res = parse_line(line)
        # If it successfully parsed, add the dictionary to our final list
        if res != None:
            parsed.append(res)

    # PHASE 4: Fix the Branches
    # Now that we know where all the labels are, go replace words like "LOOP" with real numbers
    final_instructions = resolve_labels(parsed, label_map)
    
    return final_instructions


def decode_machine_code(bin_str):
    """
    Takes a 32-character string of 1s and 0s and slices it up according to the MIPS architecture manual.
    """
    # Slice the string into the specific bit-ranges for MIPS
    op_bin = bin_str[0:6]      # First 6 bits are the Opcode
    rs_bin = bin_str[6:11]     # Next 5 bits are the Source Register
    rt_bin = bin_str[11:16]    # Next 5 bits are the Target Register
    rd_bin = bin_str[16:21]    # Next 5 bits are the Destination Register
    funct_bin = bin_str[26:32] # Last 6 bits are the Function code (for R-types)
    imm_bin = bin_str[16:32]   # Last 16 bits are the Immediate number (for I-types)
    
    # Convert those binary slices into standard integer numbers using base-2 math
    opcode = int(op_bin, 2)
    rs_num = int(rs_bin, 2)
    rt_num = int(rt_bin, 2)
    rd_num = int(rd_bin, 2)
    
    # Start with empty values
    op = None
    imm = None
    lbl_ref = None
    i_type = None

    # R-Type Instructions always have an opcode of 0. We rely on the 'funct' code to know what it is.
    if opcode == 0:
        i_type = "R"
        funct = int(funct_bin, 2) # Convert the function bits to a number
        
        # Match the function number to the correct text operation
        if funct == 32: op = "add"
        elif funct == 34: op = "sub"
        elif funct == 36: op = "and"
        elif funct == 37: op = "or"
        elif funct == 42: op = "slt"
        
    # I-Type and J-Type Instructions (Opcode is not 0)
    else:
        rd_num = None # I-types don't use the destination register
        
        # Check if the number is negative. In binary, if the very first bit is a '1', it is negative.
        if imm_bin[0] == '1': 
            # Two's complement math: convert to int and subtract 2^16 to get the negative value
            imm = int(imm_bin, 2) - 65536 
        else:
            # It's positive, so just convert it normally
            imm = int(imm_bin, 2)

        # Match the opcode number to the correct text operation
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

    # Package everything up into the shared dictionary format for the team
    return make_instruction(
        op=op, instr_type=i_type, rs=rs_num, rt=rt_num, rd=rd_num, 
        imm=imm, label=lbl_ref, raw=bin_str
    )


def parse_line(line):
    """
    Takes a single line of text and figures out if it's Machine Code or Assembly Code,
    then parses it accordingly.
    """
    #  SNIFFER: Is this Machine Code?
    # If it starts with 0x, we know immediately it's Hexadecimal machine code
    if line.startswith("0x"):
        return decode_machine_word(line)
        
    # Let's check if it's pure binary (exactly 32 characters of just 1s and 0s)
    is_bin = True
    if len(line) != 32:
        is_bin = False # Too long or too short to be binary
    else:
        for char in line:
            if char != '0' and char != '1':
                is_bin = False # Found a letter or symbol, so it's not pure binary

    # If it passed the binary test, decode it as machine code
    if is_bin:
        return decode_machine_word(line)

    #  It must be Assembly Code (like "add $t0, $t1, $t2")
    raw = line
    # Delete all commas to make splitting the words easier
    line = line.replace(",", "")
    # Split the string by spaces into a list of words
    words = line.split()
    
    op = words[0] # The operation (like 'add') is always the first word
    
    # Start with empty variables
    rs_str = None
    rt_str = None
    rd_str = None
    imm = None
    lbl = None
    i_type = None
    
    # If it's a basic math operation (R-Type)
    if op in ["add", "sub", "and", "or", "slt"]:
        i_type = "R"
        rd_str = words[1] # Destination is the first register listed
        rs_str = words[2] # Source 1 is the second
        rt_str = words[3] # Source 2 is the third
        
    # If it's immediate addition (I-Type)
    elif op == "addi":
        i_type = "I"
        rt_str = words[1] # Target is the first register
        rs_str = words[2] # Source is the second
        imm = int(words[3]) # The last part is the number, convert it to an integer
        
    # If it's loading or storing memory (I-Type)
    elif op == "lw" or op == "sw":
        i_type = "I"
        rt_str = words[1]
        # Use our helper function to break apart "0($zero)"
        imm, rs_str = _split_mem_operand(words[2])
        
    # If it's a branch instruction (I-Type)
    elif op == "beq" or op == "bne":
        i_type = "I"
        rs_str = words[1]
        rt_str = words[2]
        lbl = words[3] # The text name of the label (like 'LOOP')

    # If it's a jump instruction (J-Type)
    elif op == "j":
        i_type = "J"
        lbl = words[1] # The text name of the label

    # Convert the string register names (like '$t0') into their hardware numbers
    rs_num = _reg_num(rs_str)
    rt_num = _reg_num(rt_str)
    rd_num = _reg_num(rd_str)

    # Package it into the team's shared dictionary format
    return make_instruction(
        op=op, instr_type=i_type, rs=rs_num, rt=rt_num, rd=rd_num, 
        imm=imm, label=lbl, raw=raw
    )


def resolve_labels(instructions, label_map):
    """
    Goes through the finished list of instructions. If an instruction is trying to 
    jump to a word (like 'LOOP'), it replaces that word with the correct math to get there.
    """
    # 'enumerate' gives us both the current instruction AND its line number ('i')
    for i, inst in enumerate(instructions):
        # Does this instruction have a label saved?
        if inst["label"] != None:
            target = inst["label"] # Grab the word (e.g., 'LOOP')
            
            # Does this word exist in our saved map?
            if target in label_map:
                target_pc = label_map[target] # Get the line number it points to
                
                # Branches (beq, bne) are "PC-Relative"
                # They don't jump to an exact line; they jump a certain distance from where we are currently standing.
                if inst["op"] == "beq" or inst["op"] == "bne":
                    # Calculate the distance: (Destination Line) - (Current Line) - (1 step for the next cycle)
                    inst["imm"] = target_pc - i - 1
                else:
                    # Jumps (j) are "Absolute"
                    # They ignore where we are standing and just go exactly to the target line number.
                    inst["imm"] = target_pc
                    
                # Erase the text label now that we have done the math
                inst["label"] = None            
                
    return instructions


if __name__ == "__main__":
    # A quick test block to run when we execute this file directly
    test_program = """
    # test program
    LOOP: addi $t0, $zero, 10
    00000001000010010101000000100000 
    0x114A0003
    beq  $t0, $t2, LOOP
    """

    try:
        # Run our master parser
        result = parse_program(test_program)
        print("Parsed {} instructions:".format(len(result)))
        # Print each final dictionary to prove it worked
        for i, instr in enumerate(result):
            print("  [{}] {}".format(i, instr))
    except Exception as e:
        print("Error: {}".format(e))
