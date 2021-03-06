import os.path
import sys
import re

last_operands = None

def get_operand_description(operand, load_operand=False):
    global constants
    if re.match(r"^[aA][0-7]$", operand):
        if load_operand:
            return "the address in the register " + operand
        else:
            return "address register " + operand
    if re.match(r"^[dD][0-7]$", operand):
        if load_operand:
            return "the value in the register " + operand
        else:
            return "data register " + operand
    if re.match(r"^-?\(.*\)\+?$", operand):
        if load_operand:
            return "the value at the address stored in " + get_operand_description(operand[operand.find("(") + 1:operand.find(")")])
        else:
            return "the memory at the address stored in " + get_operand_description(operand[operand.find("(") + 1:operand.find(")")])
    if re.match(r"^#\d+$", operand):
        return "the constant " + operand[1:]
    if re.match(r"^#\w+$", operand):
        if operand[1:].lower() in constants:
            return "the constant " + operand[1:]
        else:
            return "the address of the variable " + operand[1:]
    if re.match(r"^\w+$", operand):
        return "the variable " + operand
    return ">>>>>>>>>>UNKNOWN CONSTRUCT<<<<<<<<<<"

def construct_jump_comment(label, condition=None, operand0=None, operand1=None):
    comment = "Jump to label " + label
    if condition is not None:
        comment += " if " + get_operand_description(operand1, True) + " " + condition + " " + get_operand_description(operand0, True)
    return comment

def get_constants(lines):
    constants = []
    for line in lines:
        line = re.sub(r"\s+", " ", line)
        line = line.lower()
        if "equ" in line:
            constants.append(line[:line.find(" ")])
    return constants


def comment_line(orig_line):
    global last_operands
    if orig_line.startswith("*"):
        return orig_line
    if ";" in orig_line:
        line = orig_line[:orig_line.find(";")]
    else:
        line = orig_line
    line = orig_line.strip()
    line = re.sub(r"\s+", " ", line)
    line = re.sub(r",\s+", ",", line)
    parts = line.split(" ")
    command = parts[0]
    if not re.match("^[A-Z][A-Z0-9_]*:$", command):
        command = command.lower()
    if len(parts) > 1:
        operands = parts[1].split(",")
    else:
        operands = None
    comment = None

    if command.startswith("clr."):
        comment = "Clear " + get_operand_description(operands[0])
    elif command.startswith("move."):
        comment = "Store " + get_operand_description(operands[0], True) + " into " + get_operand_description(operands[1], False)
    elif command.startswith("add."):
        if re.match(r"^#\d+$", operands[0]):
            comment = "Increase " + get_operand_description(operands[1], True) + " by " + operands[0][1:]
        else:
            comment = "Add " + get_operand_description(operands[0], True) + " and " + get_operand_description(operands[1], True) + " and store the result into " + get_operand_description(operands[1], False)
    elif command.startswith("sub."):
        if re.match(r"^#\d+$", operands[0]):
            comment = "Decrease " + get_operand_description(operands[1], True) + " by " + operands[0][1:]
        elif "constant" in get_operand_description(operands[0]):
            comment = "Subtract " + get_operand_description(operands[0], True) + " from " + get_operand_description(operands[1], True) + " and store the result into " + get_operand_description(operands[1], False)
        else:
            comment = "Subtract " + get_operand_description(operands[1], True) + " from " + get_operand_description(operands[0], True) + " and store the result into " + get_operand_description(operands[1], False)
    elif command.startswith("div"):
        comment = "Divide " + get_operand_description(operands[1], True) + " with " + get_operand_description(operands[0], True) + " and store the quotient in the right half and the remainder in the left half of " + get_operand_description(operands[1]);
    elif command.startswith("or."):
        comment = "Bitwise or " + get_operand_description(operands[0], True) + " and " + get_operand_description(operands[1], True) + " and store the result into " + get_operand_description(operands[1], False)
    elif command.startswith("cmp."):
        comment = "Compare " + get_operand_description(operands[0], True) + " and " + get_operand_description(operands[1], True)
    elif command == "swap":
        comment = "Swaps the first two and the last two bytes in " + get_operand_description(operands[0]);
    elif command.startswith("bra"):
        comment = construct_jump_comment(operands[0])
    elif command.startswith("beq"):
        comment = construct_jump_comment(operands[0], "==", last_operands[0], last_operands[1])
    elif command.startswith("ble"):
        comment = construct_jump_comment(operands[0], "<=", last_operands[0], last_operands[1])
    elif command.startswith("bgt"):
        comment = construct_jump_comment(operands[0], ">", last_operands[0], last_operands[1])
    elif command == "bsr":
        comment = "Call subroutine " + operands[0];
    elif command == "rts":
        comment = "Return from the subroutine"
    elif command.startswith("org"):
        address = parts[1][1:]
        comment = "Start at address " + address
        if int(address) > 9000:
            comment += " (it's over 9000!)"

    length_suffix = command[command.find(".") + 1:]

    if operands is not None:
        if length_suffix == "b":
            byte_length = 1
        elif length_suffix == "w":
            byte_length = 2
        else:
            byte_length = 4

        op0_is_prefix = len(operands) > 1 and re.match(r"-\(.*\)", operands[0])
        op1_is_prefix = len(operands) > 1 and re.match(r"-\(.*\)", operands[1])

        if op0_is_prefix and op1_is_prefix:
            prestring = "Decrease " + get_operand_description(operands[0][2:-1], True) + " and " + get_operand_description(operands[1][2:-1], True) + " by " + str(byte_length)
            pass
        elif op0_is_prefix:
            prestring = "Decrease " + get_operand_description(operands[0][2:-1], True) + " by " + str(byte_length)
            pass
        elif op1_is_prefix:
            prestring = "Decrease " + get_operand_description(operands[1][2:-1], True) + " by " + str(byte_length)
            pass
        if op0_is_prefix or op1_is_prefix:
            comment = prestring + ". Then " + comment[0:1].lower() + comment[1:]

        op0_is_suffix = len(operands) > 1 and re.match(r"\(.*\)+", operands[0]);
        op1_is_suffix = len(operands) > 1 and re.match(r"\(.*\)+", operands[1]);
        if op0_is_suffix and op1_is_suffix:
            afterstring = "Afterwards increase " + get_operand_description(operands[0][1:-2], True) + " and " + get_operand_description(operands[1][1:-2], True) + " by " + str(byte_length)
            pass
        elif op0_is_suffix:
            afterstring = "Afterwards increase " + get_operand_description(operands[0][1:-2], True) + " by " + str(byte_length)
            pass
        elif op1_is_suffix:
            afterstring = "Afterwards increase " + get_operand_description(operands[1][1:-2], True) + " by " + str(byte_length)
            pass
        if op0_is_suffix or op1_is_suffix:
            comment += ". " + afterstring



    last_operands = operands

    if comment is not None:
        if ";" in orig_line:
            orig_line = orig_line[:orig_line.find(";")]
        orig_line += " ; " + comment
    return orig_line

if len(sys.argv) != 3:
    sys.stderr.write("Usage: main.py inputfile outputfile\nUse - as filename to read from stdin/write to stdout\n")
    sys.exit(1)

ifile = sys.argv[1]
ofile = sys.argv[2]

if ifile == "-":
    ifile = sys.stdin
else:
    ifile = open(ifile)

lines = ifile.read().split("\n")

if ifile != sys.stdin:
    ifile.close()

constants = get_constants(lines)

lines = [comment_line(line) for line in lines]

linelength = 35
for i in range(0, len(lines)):
    if re.match(r"^\s*\S.*;", lines[i]):
        linelength = max(re.search(r"\s*;", lines[i]).start() + 5, linelength)

for i in range(0, len(lines)):
    if re.match(r"^\s*\S.*;", lines[i]):
        match = re.search(r"\s*;", lines[i])
        command = lines[i][:match.start()]
        comment = lines[i][match.end() - 1:]
        current_linelength = len(command)
        for count in range(0, linelength - current_linelength):
            command += " "
        lines[i] = command + comment

if ofile == "-":
    ofile = sys.stdout
else:
    ofile = open(ofile, "w")

for line in lines:
    ofile.write(line + "\n")

if ofile != sys.stdout:
    ofile.close()