"""
    This is a general template for assemblers.
    Serves as a parent class.
"""


class ImmediateOutOfBound(Exception):
    """ User input is larger than allowed

    Attributes:
        bits -- the number of bits available for this opcode
        intIn -- what the user typed as input
    """

    def __init__(self, bits, intIn):
        self.bits = bits
        self.intIn = intIn
        super().__init__()

    def __str__(self):
        return f'{self.intIn} can\'t be represented as 2\'s complement in {self.bits} bits.'


class UnknownError(Exception):
    def __init__(self, lineNum):
        self.lineNum = lineNum
        super().__init__()

    def __str__(self):
        return f'Some error occurred in line {self.lineNum}.'


class Assembler:
    registerDict = {
        "R0": "000",
        "R1": "001",
        "R2": "010",
        "R3": "011",
        "R4": "100",
        "R5": "101",
        "R6": "110",
        "R7": "111"
    }
    trapDict = {
        "GETC": "X20",
        "OUT": "X21",
        "PUTS": "X22",
        "IN": "X23",
        "PUTSP": "X24",
        "HALT": "X25",
    }
    opcodeList = ["ADD", "AND", "BR", "BRN", "BRZ", "BRP", "BRNZ", "BRNP", "BRZP", "BRNZP", "JMP", "JSR",
                  "JSRR", "LD", "LDI", "LDR", "LEA", "NOT", "RET", "RTI", "ST", "STI", "STR", "TRAP"]
    pseudocodeList = [".FILL", ".ORIG", ".END", ".BLKW", ".STRINGZ"]

    debug = True

    def ADD(self, dr, sr1, arg2):
        retStr = "0001"
        retStr += self.registerDict[dr]
        retStr += self.registerDict[sr1]
        if arg2[0] in "#X":
            retStr += "1"
            intIn = int(arg2[1:]) if arg2[0] == "#" else \
                (0 - int(arg2[1:], 16) if arg2[1] in "89ABCDEF" else int(arg2[1:], 16))
            retStr += toTwosComp(intIn, 5)
        else:
            retStr += "000"
            if arg2 not in self.registerDict:
                raise UnknownError("--")
            retStr += self.registerDict[arg2]
        return retStr

    def AND(self, dr, sr1, arg2):
        retStr = "0101"
        retStr += self.registerDict[dr]
        retStr += self.registerDict[sr1]
        if arg2[0] in "#X":
            retStr += "1"
            intIn = int(arg2[1:]) if arg2[0] == "#" else \
                (0 - int(arg2[1:], 16) if arg2[1] in "89ABCDEF" else int(arg2[1:], 16))
            retStr += toTwosComp(intIn, 5)
        else:
            retStr += "000"
            if arg2 not in self.registerDict:
                raise UnknownError("--")
            retStr += self.registerDict[arg2]
        return retStr

    def _BR(self, nzpStr, offset):
        retStr = "0000"
        if nzpStr == "BR":
            retStr += "111"
        else:
            retStr += "1" if "N" in nzpStr else "0"
            retStr += "1" if "Z" in nzpStr else "0"
            retStr += "1" if "P" in nzpStr else "0"

        retStr += toTwosComp(offset, 9)
        return retStr

    def JMP(self, baseR):
        retStr = "1100000"
        retStr += self.registerDict[baseR]
        retStr += "000000"
        return retStr

    def JSR(self, offset):
        retStr = "01001"
        retStr += toTwosComp(offset, 11)
        return retStr

    def JSRR(self, baseR):
        retStr = "0100000"
        retStr += self.registerDict[baseR]
        retStr += "000000"
        return retStr

    def LD(self, dr, offset):
        retStr = "0010"
        retStr += self.registerDict[dr]
        retStr += toTwosComp(offset, 9)
        return retStr

    def LDI(self, dr, offset):
        retStr = "1010"
        retStr += self.registerDict[dr]
        retStr += toTwosComp(offset, 9)
        return retStr

    def LDR(self, dr, baseR, offset):
        retStr = "0110"
        retStr += self.registerDict[dr]
        retStr += self.registerDict[baseR]
        retStr += toTwosComp(offset, 6)
        return retStr

    def LEA(self, dr, offset):
        retStr = "1110"
        retStr += self.registerDict[dr]
        retStr += toTwosComp(offset, 9)
        return retStr

    def NOT(self, dr, sr):
        retStr = "1001"
        retStr += self.registerDict[dr]
        retStr += self.registerDict[sr]
        retStr += "111111"
        return retStr

    def RET(self):
        return "1100000111000000"

    def RTI(self):
        return "1000000000000000"

    def ST(self, sr, offset):
        retStr = "0011"
        retStr += self.registerDict[sr]
        retStr += toTwosComp(offset, 9)
        return retStr

    def STI(self, sr, offset):
        retStr = "1011"
        retStr += self.registerDict[sr]
        retStr += toTwosComp(offset, 9)
        return retStr

    def STR(self, sr, baseR, offset):
        retStr = "0111"
        retStr += self.registerDict[sr]
        retStr += self.registerDict[baseR]
        retStr += toTwosComp(offset, 6)
        return retStr

    def TRAP(self, trapvect8):
        retStr = "11110000"
        if trapvect8[0] == "X" or "#":
            retStr += toTwosComp(int(trapvect8[1:], 16) if trapvect8[0] == "X" else int(trapvect8[1:]), 8, False)
        else:
            raise UnknownError("--")
        return retStr

    def pseudoCode(self, code, arg0):
        if code == ".END":      # skip
            return ".END", 0
        if code == ".ORIG":     # set PC
            return ".ORIG " + arg0, (int(arg0[1:], 16) if arg0[0] == "X" else int(arg0[1:]))
        if code == ".FILL":
            if arg0[0] == "X" or "#":
                return toTwosComp(int(arg0[1:], 16) if arg0[0] == "X" else int(arg0[1:]), 16, False), 1
            else:
                raise UnknownError("--")
        if code == ".BLKW":
            if arg0[0] == "X" or "#":
                count = int(arg0[1:], 16) if arg0[0] == "X" else int(arg0[1:])
                if count < 1:
                    raise UnknownError("--")
                retStr = "0000000000000000"
                for i in range(1, count):
                    retStr += "\n0000000000000000"
                return retStr, 1
        if code == ".STRINGZ":
            string = arg0.replace("\"", "").replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r").replace("\\0", "\0")
            retStr = ""
            for ch in string:
                asciiCode = ord(ch)
                retStr += toTwosComp(asciiCode, 16, False)
                retStr += "\n"
            retStr += "0000000000000000"
            return retStr, len(string) + 1

        raise UnknownError(code)


def toTwosComp(num, bits, isSigned: bool = True):
    if num < 0:
        isSigned = True
    if not isSigned:
        if 0 <= num < pow(2, bits):
            numStr = bin(num if num >= 0 else abs(num) - 1)[2:]
            while len(numStr) < bits:
                numStr = "0" + numStr
            return numStr

    elif 0 - pow(2, bits - 1) <= num <= pow(2, bits - 1) - 1:
        numStr = bin(num if num >= 0 else abs(num) - 1)[2:]
        while len(numStr) < bits:
            numStr = "0" + numStr
        if num < 0:
            flippedStr = ""
            for ch in numStr:
                flippedStr += "0" if ch == '1' else "1"
            numStr = flippedStr
        return numStr
    # else:
    raise ImmediateOutOfBound(bits, num)
