import Virtual_Raw
from pynput import keyboard
from tkinter import *


class InvalidFormatError(Exception):
    def __init__(self, lineNum):
        self.lineNum = lineNum
        super().__init__()

    def __str__(self):
        return f"Invalid format in line {self.lineNum}"


class ImmediateOutOfBound(Exception):
    def __init__(self, bits, intIn):
        self.bits = bits
        self.intIn = intIn
        super().__init__()

    def __str__(self):
        return f'{self.intIn} can\'t be represented as 2\'s complement in {self.bits} bits.'


class UnknownLabelError(Exception):
    def __init__(self, line: str):
        self.line = line
        super().__init__()

    def __str__(self):
        return f'\n\t{self.line} is not found in the document!'


def toTwosComp(num, bits, isSigned: bool = True):
    retInt: int
    if isSigned:
        if (0 - 2 ** (bits - 1)) <= num < 2 ** (bits - 1):
            retInt = 2 ** 16 + num
            retInt &= 0x0FFFF
        else:
            raise ImmediateOutOfBound(bits, num)
    else:
        if 0 <= num < 2 ** bits:
            retInt = num & 0x0FFFF
        else:
            raise ImmediateOutOfBound(bits, num)

    return retInt & ((1 << bits) - 1)


class Assembler(object):
    registerDict = {
        "R0": 0,
        "R1": 1,
        "R2": 2,
        "R3": 3,
        "R4": 4,
        "R5": 5,
        "R6": 6,
        "R7": 7
    }

    trapDict = {
        "GETC": 0xF020,
        "OUT": 0xF021,
        "PUTS": 0xF022,
        "IN": 0xF023,
        "PUTSP": 0xF024,
        "HALT": 0xF025
    }

    opcodeList = ["ADD", "AND", "BR", "BRN", "BRZ", "BRP", "BRNZ", "BRNP", "BRZP", "BRNZP", "JMP", "JSR",
                  "JSRR", "LD", "LDI", "LDR", "LEA", "NOT", "RET", "RTI", "ST", "STI", "STR", "TRAP"]

    pseudocodeList = [".FILL", ".ORIG", ".END", ".BLKW", ".STRINGZ"]

    labels: dict = {}
    virtual_machine: Virtual_Raw.virtual_lc3
    virtual_kb: Virtual_Raw.Keyboard
    virtual_csl: Virtual_Raw.Console
    virtual_ram: Virtual_Raw.RAM

    lastKeyPressed: int = 0
    lastKeyValid: bool = False

    debug: bool
    debugAddress: int
    PC: int

    def __init__(self, machine: Virtual_Raw.virtual_lc3, kb: Virtual_Raw.Keyboard, csl: Virtual_Raw.Console,
                 ram: Virtual_Raw.RAM, doDebug: bool):
        self.virtual_machine = machine
        self.virtual_kb = kb
        self.virtual_csl = csl
        self.virtual_ram = ram
        self.virtual_machine.addDevice(self.virtual_kb, 0xFE00, 0xFE02)
        self.virtual_machine.addDevice(self.virtual_csl, 0xFE04, 0xFE06)
        self.virtual_machine.addDevice(self.virtual_ram, 0xFE10, 0xFE12)
        self.debug = doDebug

    # it turns out that I didn't even need this thing
    """
    # returns (list of 16-bit data, set new address, address/increment, hasEnded)
    def pseudoCode(self, code: str, arg, labels: dict = None):
        if labels is None:
            labels = self.labels
        if code == ".END":  # .END
            return [None], False, 0, True
        elif code == ".ORIG":  # .ORIG arg
            return [None], True, (int(arg[1:], 16) if arg[0] == "X" else int(arg[1:])), False
        elif code == ".FILL":  # .FILL arg
            return [int(arg[1:], 16) if arg[0] == "X" else (
                int(arg[1:]) if arg[0] == "#" else labels.setdefault(arg, None))], False, 1, False
        elif code == ".BLKW":  # .BLKW arg
            num = int(arg[1:], 16) if arg[0] == "X" else int(arg[1:])
            return [0] * num, False, num, False
        elif code == ".STRINGZ":  # .STRINGZ arg
            myList = []
            count = 0
            string = arg[1:-1].replace("\\n", "\n").replace("\\t", "\t")
            string = string.replace("\\\"", "\"").replace("\\\'", "\'").replace("\\\\", "\\")
            for ch in string:
                myList.append(ord(ch))
                count += 1
            myList.append(0)
            count += 1
            return myList, False, count, False
        else:
            raise InvalidFormatError("\"" + code + "\"")
    """

    # returns the 16-bit data
    def opCode(self, address, code: str, arg, labels: dict):
        retInt: int
        if code == "ADD":
            arg = arg.split(',', 2)
            retInt = 0b0001 << 12
            DR = self.registerDict.setdefault(arg[0], -1)
            SR1 = self.registerDict.setdefault(arg[1], -1)
            if (DR == -1) or (SR1 == -1):
                raise InvalidFormatError("\"" + code + "\"")
            SR2 = self.registerDict.setdefault(arg[2], -1)
            if SR2 == -1:
                SR2 = toTwosComp(int(arg[2][1:], 16) if arg[2][0] == "X" else int(arg[2][1:]), 5)
                retInt += 1 << 5
            retInt += (DR << 9) + (SR1 << 6) + SR2

        elif code == "AND":
            arg = arg.split(',', 2)
            retInt = 0b0101 << 12
            DR = self.registerDict.setdefault(arg[0], -1)
            SR1 = self.registerDict.setdefault(arg[1], -1)
            if (DR == -1) or (SR1 == -1):
                raise InvalidFormatError("\"" + code + "\"")
            SR2 = self.registerDict.setdefault(arg[2], -1)
            if SR2 == -1:
                SR2 = toTwosComp(int(arg[2][1:], 16) if arg[2][0] == "X" else int(arg[2][1:]), 5)
                retInt += 1 << 5
            retInt += (DR << 9) + (SR1 << 6) + SR2

        elif code == "BR":
            retInt = 0
            if arg[0][0] not in "X#":
                labelAdd = labels.setdefault(arg, None)
                if labelAdd is None:
                    raise UnknownLabelError(arg)
                offset = toTwosComp(labelAdd - address - 1, 9)
            else:
                offset = toTwosComp(int(arg[1:], 16) if arg[0] == "X" else int(arg[1:]), 9)
            retInt += offset

        elif code == "BRN":
            retInt = 0b100 << 9
            if arg[0] not in "X#":
                labelAdd = labels.setdefault(arg, None)
                if labelAdd is None:
                    raise UnknownLabelError(arg)
                offset = toTwosComp(labelAdd - address - 1, 9)
            else:
                offset = toTwosComp(int(arg[1:], 16) if arg[0] == "X" else int(arg[1:]), 9)
            retInt += offset

        elif code == "BRZ":
            retInt = 0b010 << 9
            if arg[0] not in "X#":
                labelAdd = labels.setdefault(arg, None)
                if labelAdd is None:
                    raise UnknownLabelError(arg)
                offset = toTwosComp(labelAdd - address - 1, 9)
            else:
                offset = toTwosComp(int(arg[1:], 16) if arg[0] == "X" else int(arg[1:]), 9)
            retInt += offset

        elif code == "BRP":
            retInt = 0b001 << 9
            if arg[0] not in "X#":
                labelAdd = labels.setdefault(arg, None)
                if labelAdd is None:
                    raise UnknownLabelError(arg)
                offset = toTwosComp(labelAdd - address - 1, 9)
            else:
                offset = toTwosComp(int(arg[1:], 16) if arg[0] == "X" else int(arg[1:]), 9)
            retInt += offset

        elif code == "BRNZ":
            retInt = 0b110 << 9
            if arg[0] not in "X#":
                labelAdd = labels.setdefault(arg, None)
                if labelAdd is None:
                    raise UnknownLabelError(arg)
                offset = toTwosComp(labelAdd - address - 1, 9)
            else:
                offset = toTwosComp(int(arg[1:], 16) if arg[0] == "X" else int(arg[1:]), 9)
            retInt += offset

        elif code == "BRNP":
            retInt = 0b101 << 9
            if arg[0] not in "X#":
                labelAdd = labels.setdefault(arg, None)
                if labelAdd is None:
                    raise UnknownLabelError(arg)
                offset = toTwosComp(labelAdd - address - 1, 9)
            else:
                offset = toTwosComp(int(arg[1:], 16) if arg[0] == "X" else int(arg[1:]), 9)
            retInt += offset

        elif code == "BRZP":
            retInt = 0b011 << 9
            if arg[0] not in "X#":
                labelAdd = labels.setdefault(arg, None)
                if labelAdd is None:
                    raise UnknownLabelError(arg)
                offset = toTwosComp(labelAdd - address - 1, 9)
            else:
                offset = toTwosComp(int(arg[1:], 16) if arg[0] == "X" else int(arg[1:]), 9)
            retInt += offset

        elif code == "BRNZP":
            retInt = 0b111 << 9
            if arg[0] not in "X#":
                labelAdd = labels.setdefault(arg, None)
                if labelAdd is None:
                    raise UnknownLabelError(arg)
                offset = toTwosComp(labelAdd - address - 1, 9)
            else:
                offset = toTwosComp(int(arg[1:], 16) if arg[0] == "X" else int(arg[1:]), 9)
            retInt += offset

        elif code == "JMP":
            retInt = 0b1100 << 12
            baseR = self.registerDict.setdefault(arg[0], -1)
            if baseR == -1:
                raise InvalidFormatError("\"" + code + "\"")
            retInt += baseR << 6

        elif code == "RET":
            retInt = 0b1100 << 12
            retInt += 0b111 << 6

        elif code == "JSR":
            retInt = 0b0100 << 12
            retInt += 1 << 11
            if arg[0] not in "X#":
                labelAdd = labels.setdefault(arg, None)
                if labelAdd is None:
                    raise UnknownLabelError(arg)
                offset = toTwosComp(labelAdd - address - 1, 11)
            else:
                offset = toTwosComp(int(arg[1:], 16) if arg[0] == "X" else int(arg[1:]), 11)
            retInt += offset

        elif code == "JSRR":
            retInt = 0b0100 << 12
            baseR = self.registerDict.setdefault(arg, -1)
            if baseR == -1:
                raise InvalidFormatError("\"" + code + "\"")
            retInt += baseR << 6

        elif code == "LD":
            arg = arg.split(',', 1)
            retInt = 0b0010 << 12
            DR = self.registerDict.setdefault(arg[0], -1)
            if DR == -1:
                raise InvalidFormatError("\"" + code + "\"")
            retInt += DR << 9
            if arg[1][0] not in "X#":
                labelAdd = labels.setdefault(arg[1], None)
                if labelAdd is None:
                    raise UnknownLabelError(arg[1])
                offset = toTwosComp(labelAdd - address - 1, 9)
            else:
                offset = toTwosComp(int(arg[1][1:], 16) if arg[1][0] == "X" else int(arg[1][1:]), 9)
            retInt += offset

        elif code == "LDI":
            arg = arg.split(',', 1)
            retInt = 0b1010 << 12
            DR = self.registerDict.setdefault(arg[0], -1)
            if DR == -1:
                raise InvalidFormatError("\"" + code + "\"")
            retInt += DR << 9
            if arg[1][0] not in "X#":
                labelAdd = labels.setdefault(arg[1], None)
                if labelAdd is None:
                    raise UnknownLabelError(arg[1])
                offset = toTwosComp(labelAdd - address - 1, 9)
            else:
                offset = toTwosComp(int(arg[1][1:], 16) if arg[1][0] == "X" else int(arg[1][1:]), 9)
            retInt += offset

        elif code == "LDR":
            arg = arg.split(',', 2)
            retInt = 0b0110 << 12
            DR = self.registerDict.setdefault(arg[0], -1)
            BaseR = self.registerDict.setdefault(arg[1], -1)
            if (DR == -1) or (BaseR == -1):
                raise InvalidFormatError("\"" + code + "\"")
            offset = toTwosComp(int(arg[2][1:], 16) if arg[2][0] == "X" else int(arg[2][1:]), 6)
            retInt += (DR << 9) + (BaseR << 6) + offset

        elif code == "ST":
            arg = arg.split(',', 1)
            retInt = 0b0011 << 12
            DR = self.registerDict.setdefault(arg[0], -1)
            if DR == -1:
                raise InvalidFormatError("\"" + code + "\"")
            retInt += DR << 9
            if arg[1][0] not in "X#":
                labelAdd = labels.setdefault(arg[1], None)
                if labelAdd is None:
                    raise UnknownLabelError(arg[1])
                offset = toTwosComp(labelAdd - address - 1, 9)
            else:
                offset = toTwosComp(int(arg[1][1:], 16) if arg[1][0] == "X" else int(arg[1][1:]), 9)
            retInt += offset

        elif code == "STI":
            arg = arg.split(',', 1)
            retInt = 0b1011 << 12
            DR = self.registerDict.setdefault(arg[0], -1)
            if DR == -1:
                raise InvalidFormatError("\"" + code + "\"")
            retInt += DR << 9
            if arg[1][0] not in "X#":
                labelAdd = labels.setdefault(arg[1], None)
                if labelAdd is None:
                    raise UnknownLabelError(arg[1])
                offset = toTwosComp(labelAdd - address - 1, 9)
            else:
                offset = toTwosComp(int(arg[1][1:], 16) if arg[1][0] == "X" else int(arg[1][1:]), 9)
            retInt += offset

        elif code == "STR":
            arg = arg.split(',', 2)
            retInt = 0b0111 << 12
            DR = self.registerDict.setdefault(arg[0], -1)
            BaseR = self.registerDict.setdefault(arg[1], -1)
            if (DR == -1) or (BaseR == -1):
                raise InvalidFormatError("\"" + code + "\"")
            offset = toTwosComp(int(arg[2][1:], 16) if arg[2][0] == "X" else int(arg[2][1:]), 6)
            retInt += (DR << 9) + (BaseR << 6) + offset

        elif code == "LEA":
            arg = arg.split(',', 1)
            retInt = 0b1110 << 12
            DR = self.registerDict.setdefault(arg[0], -1)
            if DR == -1:
                raise InvalidFormatError("\"" + code + "\"")
            retInt += DR << 9
            if arg[1][0] not in "X#":
                labelAdd = labels.setdefault(arg[1], None)
                if labelAdd is None:
                    raise UnknownLabelError(arg[1])
                offset = toTwosComp(labelAdd - address - 1, 9)
            else:
                offset = toTwosComp(int(arg[1][1:], 16) if arg[1][0] == "X" else int(arg[1][1:]), 9)
            retInt += offset

        elif code == "NOT":
            arg = arg.split(',', 1)
            retInt = 0b1001 << 12
            DR = self.registerDict.setdefault(arg[0], -1)
            SR = self.registerDict.setdefault(arg[1], -1)
            if (DR == -1) or (SR == -1):
                raise InvalidFormatError("\"" + code + "\"")
            retInt += (DR << 9) + (SR << 6) + 0b111111

        elif code == "RTI":
            retInt = 1 << 15

        elif code == "TRAP":
            retInt = 0b1111 << 12

        else:
            raise InvalidFormatError("\"" + code + "\"")

        return retInt

    # scan for labels
    def getLabel(self, cleanedList: list) -> dict:
        rawLabels = {}
        address = 0
        hasEnded: bool = True
        for line in cleanedList:
            parts = line.split(" ", 1)  # split only once
            if self.debug:
                print("\t\t" + line)

            # look for ".ORIG" first to update hasEnded (".ORIG" can only be 2 words long)
            if len(parts) == 2:  # also possible for ".BLKW", ".STRINGZ", ".FILL" and OpCodes
                if parts[0] == ".ORIG":
                    address = int(parts[1][1:], 16) if parts[1][0] == "X" else int(parts[1][1:])
                    hasEnded = False
                elif hasEnded:
                    continue
                elif parts[0] == ".BLKW":
                    address += int(parts[1][1:], 16) if parts[1][0] == "X" else int(parts[1][1:])
                elif parts[0] == ".STRINGZ":
                    address += len(
                        parts[1][1:-1].replace("\\n", "\n").replace("\\t", "\t").replace("\\\"", "\"").replace(
                            "\\\'", "\'").replace("\\\\", "\\")) + 1
                elif parts[0] == ".FILL" or parts[0] in self.opcodeList or parts[0] in self.trapDict:
                    address += 1
                else:
                    parts = [parts[0]] + parts[1].split(" ", 1)
                    if len(parts) == 3:  # ".BLKW", ".STRINGZ", ".FILL" and OpCodes with a label in front
                        if parts[1] == ".ORIG":
                            raise InvalidFormatError("\"" + line + "\"")
                        if hasEnded:
                            continue
                        if parts[1] == ".BLKW":
                            rawLabels[parts[0]] = address
                            address += int(parts[2][1:], 16) if parts[2][0] == "X" else int(parts[2][1:])
                        elif parts[1] == ".STRINGZ":
                            rawLabels[parts[0]] = address
                            address += len(
                                parts[2][1:-1].replace("\\n", "\n").replace("\\t", "\t").replace("\\\"", "\"").replace(
                                    "\\\'", "\'").replace("\\\\", "\\")) + 1
                        elif parts[1] == ".FILL" or parts[1] in self.opcodeList or parts[1] in self.trapDict:
                            rawLabels[parts[0]] = address
                            address += 1
                    elif len(parts) == 2 and not hasEnded:
                        if parts[1] == ".END":  # in pseudocode, it could only be ".END"
                            raise InvalidFormatError("\"" + line + "\"")
                        elif parts[1] in self.opcodeList or parts[1] in self.trapDict:
                            rawLabels[parts[0]] = address
                            address += 1
                        else:
                            raise InvalidFormatError("\"" + line + "\"")
            elif len(parts) == 1 and not hasEnded:
                if parts[0] == ".END":  # in pseudocode, it could only be ".END"
                    hasEnded = True
                elif parts[0] in self.opcodeList or parts[0] in self.trapDict:
                    address += 1
                else:
                    raise InvalidFormatError("\"" + line + "\"")
            else:
                raise InvalidFormatError("\"" + line + "\"")

        return rawLabels

    def assemble(self, memory: list):
        """ turn user input into memory map and feed it to the LC-3"""
        if self.debug:
            print("\tStarting at", self.PC)
        memory[memory.index(0x3000, 0x200)] = self.PC
        if self.debug:
            print("\tChecked with no error! Nice!")
            print("\tGot memory map:")
            print("\t\t", memory)
        self.virtual_machine.setMemory(memory)
        self.virtual_machine.PC = 0x200

    def run(self, debugAddress=-1):
        if debugAddress < -1 or debugAddress > 0xFFFF:
            self.debugAddress = -1
        else:
            self.debugAddress = debugAddress

        # start the machine
        self.virtual_machine.MCR.value[0] |= 0x8000
        while (self.virtual_machine.MCR.value[0] & 0x8000) != 0:
            if self.virtual_machine.PC == self.debugAddress:
                break
            self.step()
            # self.updatePhysicalKeyboard()     # under development
        if self.debug:
            print("\t\tEnded at", self.virtual_machine.PC - 1)

    def step(self):
        self.virtual_machine.control()

    """
    def updatePhysicalKeyboard(self):
        # The event listener will be running in this block
        event = keyboard.Events().get(0.01)
        if self.debug:
            print("\t", event)
        if event is None:
            return
        self.virtual_kb.statusRegister[0] |= (1 if self.lastKeyValid else 0) << 15
        self.virtual_kb.dataRegister[0] = event.key
        self.virtual_kb.statusRegister[0] |= 0x8000
        """
    # returns list of strings (cleaned user input)
    def cleanup(self, text: str) -> list:
        """ remove comments and extra whitespaces"""
        retLst = []
        stringSeg = ""
        lst = text.splitlines(False)
        lastLabel: str = ""  # the label if last label occupies a line alone
        for line in lst:
            if len(line) == 0:
                continue
            # add the last label if any
            line = lastLabel + " " + line

            # swap all \" in strings to avoid confusion
            line = line.replace("\\\"", chr(128))
            if "\"" in line:
                if ";" in line:
                    if line.index("\"") > line.index(";"):
                        # if first ; is before first "
                        line = line[0:line.index(";")]
                    elif line.index("\"", line.index("\"") + 1) < line.index(";"):
                        # if first ; is after second " (outside the string)
                        line = line[0:line.index(";")]
                        # pick out the string
                        stringSeg = line[line.index("\""): line.index("\"", line.index("\"") + 1)]
                        line = line.replace(stringSeg, chr(129))
                    else:
                        # otherwise the first ; is in the string, then pick out the string
                        stringSeg = line[line.index("\""): line.index("\"", line.index("\"") + 1)]
                        line = line.replace(stringSeg, chr(129))

                    if ";" in line:
                        # if there's still a comment, remove it
                        line = line[0:line.index(";")]

                else:
                    # pick out the string
                    stringSeg = line[line.index("\""): line.index("\"", line.index("\"") + 1)]
                    line = line.replace(stringSeg, chr(129))
            elif ";" in line:
                # if there's still a comment, remove it
                line = line[0:line.index(";")]

            # everything should be ready to be striped and turned into upper case now
            line = line.upper().strip()
            while "  " in line:
                line = line.replace("  ", " ")
            while ", " in line:
                line = line.replace(", ", ",")

            # put back the string, and \" as ", and replace \' with '
            if chr(129) in line:
                if chr(128) in stringSeg:
                    stringSeg = stringSeg.replace(chr(128), "\"")
                if "\\\'" in stringSeg:
                    stringSeg = stringSeg.replace("\\\'", "\'")
                line = line.replace(chr(129), stringSeg)
                line = line.strip()

            if len(line) == 0:
                continue

            # check if it is a label alone
            if (" " not in line) and not (line in self.trapDict or line in self.opcodeList) and (line[0] != "."):
                lastLabel = line
                continue

            # otherwise, set last label to empty and add cleaned line to the collection
            lastLabel = ""
            retLst.append(line)

        # after going through the entire text, return the strings
        return retLst

    # returns list of int (memory)
    def encode(self, text: list, mapIn: list = None, labels=None) -> list:
        """ intakes a cleaned string list and returns a memory map (int list)"""
        if labels is None:
            labels = self.labels

        hasEnded: bool = True
        address = 0
        retMem: list = self.getNewMemMap() if mapIn is None else mapIn
        self.PC = None
        for line in text:
            if self.debug:
                print("\t\t" + line)
            parts = line.split(" ", 1)  # split only once

            if parts[0] in labels:
                parts = parts[1].split(" ", 1)
            if self.debug:
                print("\t\t\t", parts, "\n", end="")

            # look for ".ORIG" first to update hasEnded (".ORIG" can only be 2 words long)
            if len(parts) == 2:  # also possible for ".BLKW", ".STRINGZ", ".FILL" and OpCodes
                if parts[0] == ".ORIG":
                    address = int(parts[1][1:], 16) if parts[1][0] == "X" else int(parts[1][1:])
                    hasEnded = False
                    if self.PC is None:
                        self.PC = address
                        if self.debug:
                            print("\t\tPC =", address)
                elif hasEnded:
                    continue
                elif parts[0] == ".BLKW":
                    for i in range(int(parts[1][1:], 16) if parts[1][0] == "X" else int(parts[1][1:])):
                        retMem[address] = 0
                        address += 1
                elif parts[0] == ".STRINGZ":
                    for ch in parts[1][1:-1].replace("\\n", "\n").replace("\\t", "\t").replace("\\\"", "\"").replace(
                            "\\\'", "\'").replace("\\\\", "\\"):
                        retMem[address] = ord(ch)
                        address += 1
                    retMem[address] = 0  # null terminator
                    address += 1
                elif parts[0] == ".FILL":
                    number = int(parts[1][1:], 16) if parts[1][0] == "X" else (
                        int(parts[1][1:]) if parts[1][0] == "#" else labels[parts[1]])
                    retMem[address] = number if 0 < number < 65536 else (number + 65536)
                    address += 1
                elif parts[0] in self.opcodeList:
                    retMem[address] = self.opCode(address, parts[0], parts[1], labels)
                    address += 1
                else:  # couldn't be a TRAP (no second arg for TRAP)
                    raise InvalidFormatError("\"" + line + "\"")
            elif len(parts) == 1 and not hasEnded:
                if parts[0] == ".END":  # in pseudocode, it could only be ".END"
                    hasEnded = True
                elif parts[0] in self.opcodeList:
                    retMem[address] = self.opCode(address, parts[0], None, labels)
                    address += 1
                elif parts[0] in self.trapDict:
                    retMem[address] = self.trapDict[parts[0]]
                    address += 1
                else:
                    raise InvalidFormatError("\"" + line + "\"")
            else:
                raise InvalidFormatError("\"" + line + "\"")
        return retMem

    # returns list of int (new memory)
    def getNewMemMap(self):
        """ returns a memory map"""
        file = open("Default_OS_Code1-cln.asm", "r")
        text = file.read()
        textLst: list = self.cleanup(text)
        tempLabelDict = self.getLabel(textLst)
        if self.debug:
            print(tempLabelDict)
        return self.encode(textLst, [0] * 65536, tempLabelDict)
