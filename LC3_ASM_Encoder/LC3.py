import genAsmblr


class LC3Assembler(genAsmblr.Assembler):
    PC = 1
    lineNumber = 1
    labels = []

    def encode(self, lineIn) -> str:
        if self.debug:
            print(lineIn, self.lineNumber, self.PC)

        strList = lineIn.split(" ", 1)
        if strList[0] in self.pseudocodeList:
            retTuple = self.pseudoCode(strList[0], strList[1] if len(strList) > 1 else None)
            if strList[0] == ".ORIG":
                self.PC = retTuple[1]
            else:
                self.PC += retTuple[1]
            return retTuple[0]
        elif strList[0] in self.trapDict:
            strList = ["TRAP", self.trapDict[strList[0]]]  # make it in standard form
        elif strList[0] not in self.opcodeList:
            strList = strList[1].split(" ", 1)  # or split again if it is a name

            if strList[0] in self.pseudocodeList:
                retTuple = self.pseudoCode(strList[0], strList[1] if len(strList) > 1 else None)
                if strList[0] == ".ORIG":
                    self.PC = retTuple[1]
                else:
                    self.PC += retTuple[1]
                return retTuple[0]
            elif strList[0] in self.trapDict:
                strList = ["TRAP", self.trapDict[strList[0]]]  # make it in standard form
            elif strList[0] not in self.opcodeList:
                raise genAsmblr.UnknownError(self.lineNumber)  # the first two words are neither a command

        # I wonder if there's a simpler way to do this (too bad python doesn't support switch case)
        inList = strList[1].split(",") if len(strList) > 1 else None
        retStr = ""
        if strList[0] == self.opcodeList[0]:  # ADD
            retStr = self.ADD(inList[0], inList[1], inList[2])

        elif strList[0] == self.opcodeList[1]:  # AND
            retStr = self.AND(inList[0], inList[1], inList[2])

        elif strList[0] in self.opcodeList[2:10]:  # BR to BRNZP (all br)
            retStr += self._BR(strList[0], self.getOffset(inList[0]))

        elif strList[0] == self.opcodeList[10]:  # JMP
            retStr += self.JMP(inList[0])

        elif strList[0] == self.opcodeList[11]:  # JSR
            retStr += self.JSR(self.getOffset(inList[0]))

        elif strList[0] == self.opcodeList[12]:  # JSRR
            retStr += self.JSRR(inList[0])

        elif strList[0] == self.opcodeList[13]:  # LD
            retStr += self.LD(inList[0], self.getOffset(inList[1]))

        elif strList[0] == self.opcodeList[14]:  # LDI
            retStr += self.LDI(inList[0], self.getOffset(inList[1]))

        elif strList[0] == self.opcodeList[15]:  # LDR
            retStr += self.LDR(inList[0], inList[1],
                               int(inList[2][1:]) if inList[1][0] == "#" else int(inList[2][1:], 16))

        elif strList[0] == self.opcodeList[16]:  # LEA
            retStr += self.LEA(inList[0], self.getOffset(inList[1]))

        elif strList[0] == self.opcodeList[17]:  # NOT
            retStr += self.NOT(inList[0], inList[1])

        elif strList[0] == self.opcodeList[18]:  # RET
            retStr += self.RET()

        elif strList[0] == self.opcodeList[19]:  # RTI
            retStr += self.RTI()

        elif strList[0] == self.opcodeList[20]:  # ST
            retStr += self.ST(inList[0], self.getOffset(inList[1]))

        elif strList[0] == self.opcodeList[21]:  # STI
            retStr += self.STI(inList[0], self.getOffset(inList[1]))

        elif strList[0] == self.opcodeList[22]:  # STR
            retStr += self.STR(inList[0], inList[1],
                               int(inList[2][1:]) if inList[1][0] == "#" else int(inList[2][1:], 16))

        elif strList[0] == self.opcodeList[23]:  # TRAP
            retStr += self.TRAP(inList[0])

        else:
            raise genAsmblr.UnknownError(self.lineNumber)

        # if it is an opcode (not a pseudocode)
        self.PC += 1

        return retStr

    def getOffset(self, inStr):
        return int(inStr[1:]) if inStr[0][0] == "#" else \
            ((0 - int(inStr[1:], 16) if inStr[1] in "89ABCDEF" else
              int(inStr[1:], 16)) if inStr[0] == "X" else self.findLabelLineNum(inStr))

    def findLabelLineNum(self, label):
        for lbl in self.labels:
            if label == lbl[0]:
                return lbl[1] - self.PC - 1
        raise genAsmblr.UnknownError(self.lineNumber)

    def getLabel(self, fileName: str):
        file = open(fileName + "-cln.txt", "r")
        countLN = 0
        PC = 1
        thisLn = file.readline()
        while thisLn != "" or None:
            thisLn = thisLn.strip("\n")
            countLN += 1
            strList = thisLn.split(" ", 1)
            if strList[0] not in self.opcodeList and strList[0] not in self.pseudocodeList \
                    and strList[0] not in self.trapDict:
                strList = [strList[0]] + strList[1].split(" ", 1)
                if strList[1] in self.opcodeList or strList[1] in self.pseudocodeList \
                        or strList[1] in self.trapDict:
                    newTuple = [strList[0], PC]
                    self.labels.append(newTuple)
                    if strList[1] == ".STRINGZ":
                        PC += self.pseudoCode(strList[1], strList[2])[1]
                    elif strList[1] == ".ORIG":
                        PC = self.pseudoCode(strList[1], strList[2])[1]
                    else:
                        PC += 1
                else:
                    if self.debug:
                        print(strList[0], strList[1])
                    raise genAsmblr.UnknownError(countLN)
            elif strList[0] == ".STRINGZ":
                PC += self.pseudoCode(strList[0], strList[1])[1]
            elif strList[0] == ".ORIG":
                PC = self.pseudoCode(strList[0], strList[1])[1]
            else:
                PC += 1
            thisLn = file.readline()
        file.close()

        if self.debug:
            print("labels:")
            print(self.labels)
            print()

    def feedDoc(self, fileName: str):
        file = open(fileName + "-cln.txt", "r")
        bFile = open(fileName + "-bin.txt", "w")
        self.PC = 1
        self.lineNumber = 1

        thisLn = file.readline()
        while thisLn != "" or None:
            bFile.write(self.encode(thisLn.strip()) + "\n")
            thisLn = file.readline()
            self.lineNumber += 1

        file.close()
        bFile.close()
