"""
try to take a file of asm language and turn it into machine codes
"""


def cleanUp(fileName):
    """
    remove all comments
    :param fileName: (String)the name of file to be cleaned up
    :return: (nothing) (outputs a new file)
    """
    inputFile = open(fileName + ".asm", "r")
    outputFile = open(fileName + "-cln.txt", "w")

    currentLn = inputFile.readline()
    while currentLn != "":
        outputFile.write(cleanLn(currentLn))
        currentLn = inputFile.readline()
    inputFile.close()
    outputFile.close()


def cleanLn(strIn: str) -> str:
    stringStr = ""
    returnStr = ""
    strIn = strIn.strip()
    if strIn == "":
        return returnStr
    if ";" in strIn:
        index = strIn.index(";")
        strIn = strIn[0:index]
    if "\"" in strIn:
        stringStr = strIn[strIn.index("\""):]
        strIn = strIn[0:strIn.index("\"")]
    while "  " in strIn:
        strIn = strIn.replace("  ", " ")
    while ", " in strIn:
        strIn = strIn.replace(", ", ",")
    strIn = strIn.upper()
    returnStr = strIn + stringStr
    returnStr += "\n" if returnStr != "" else ""
    return returnStr


