import os.path
import sys
import re

last_operands = None

def getOperandDescription(operand, load_operand=False):
    if re.match(r"^[aAdD][0-7]$", operand):
        if load_operand:
            return "the value in register " + operand
        else:
            return "register " + operand
    if re.match(r"^\(.*\)$", operand):
        if load_operand:
            return "the value at the address stored in " + operand[1:-1]
        else:
            return "the memory at the address stored in " + operand[1:-1]
    if re.match(r"^#\d+$", operand):
        return "the constant " + operand[1:]
    if re.match(r"^#\w+$", operand):
        return "the address of the varialbe " + operand[1:]
    if re.match(r"^\w+$", operand):
        return "the variable " + operand
    return ">>>>>>>>>>UNKNOWN CONSTRUCT<<<<<<<<<<"


def construct_jump_comment(label, condition=None, operand0=None, operand1=None):
    comment = "Jump to label " + label
    if condition is not None:
        comment += " if " + getOperandDescription(operand1, True) + " " + condition + " " + getOperandDescription(operand0, True)
    return comment


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

    if command.startswith("clr"):
        comment = "Clear " + getOperandDescription(operands[0])
    elif command.startswith("move"):
        comment = "Store " + getOperandDescription(operands[0], True) + " into " + getOperandDescription(operands[1], False)
    elif command.startswith("add"):
        comment = "Add " + getOperandDescription(operands[0], True) + " and " + getOperandDescription(operands[1], True) + " and store the result into " + getOperandDescription(operands[1], False)
    elif command.startswith("cmp"):
        comment = "Compare " + getOperandDescription(operands[0], True) + " and " + getOperandDescription(operands[1], True)
    elif command.startswith("bra"):
        comment = construct_jump_comment(operands[0])
    elif command.startswith("beq"):
        comment = construct_jump_comment(operands[0], "==", last_operands[0], last_operands[1])
    elif command.startswith("ble"):
        comment = construct_jump_comment(operands[0], "<=", last_operands[0], last_operands[1])
    elif command.startswith("org"):
        address = parts[1][1:]
        comment = "Start at address " + address
        if int(address) > 9000:
            comment += " (it's over 9000!)"
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

lines = [comment_line(line) for line in lines]

if ofile == "-":
    ofile = sys.stdout
else:
    ofile = open(ofile, "w")

for line in lines:
    ofile.write(line + "\n")

if ofile != sys.stdout:
    ofile.close()