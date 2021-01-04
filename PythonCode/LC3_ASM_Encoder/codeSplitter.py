"""
        This program is to "encode" the -b.txt into two separate .txt files which will be named
    "name-a.txt" and "name-b.txt".
        It first tests if a line is a pseudocode or a piece of data (by now there should only be
    .ORIG and .END among all pseudocode). If it is a pseudocode, convert it into a simpler form,
    e.g. .ORIG num to num (keeping only the num in hex), .END to "\n" (newLine), and stored in
    each file. Otherwise, break the line into four groups of four binary digits, convert each
    group into an integer, then add an offset of 0x40 to each integer. The first two integer are
    stored in the -a file and the latter two are stored in the -b file. (the integers are stored
    as characters)
"""


def convertTwo(fileName: str):
    binFile = open(fileName + "-bin.txt", "r")
    aFile = open(fileName + "-a.txt", "w")
    bFile = open(fileName + "-b.txt", "w")

    aWrite = ""
    bWrite = ""
    count = 0
    lnIn = binFile.readline()
    while lnIn != "":
        count += 1
        lnIn = lnIn.strip()

        if lnIn[0:4] == ".END":
            aWrite = "@\n"
            bWrite = "@\n"
            count = 0           # reset count
        elif lnIn[0:5] == ".ORIG":
            aWrite = lnIn[7:] + "\n"
            bWrite = lnIn[7:] + "\n"
            count = 0           # reset count
        else:
            aWrite = chr(int(lnIn[0:4], 2) + 0x60)
            aWrite += chr(int(lnIn[4:8], 2) + 0x60)
            bWrite = chr(int(lnIn[8:12], 2) + 0x60)
            bWrite += chr(int(lnIn[12:16], 2) + 0x60)
            if count >= 15:     # the buffer size of Mega and Uno is only 64 bytes, don't blow the buffer! (60 is safe)
                aWrite += "\n"
                bWrite += "\n"
                count = 0

        aFile.write(aWrite)
        bFile.write(bWrite)
        lnIn = binFile.readline()

    binFile.close()
    aFile.close()
    bFile.close()


def convertOne(fileName: str):
    binFile = open(fileName + "-bin.txt", "r")
    file = open(fileName + "-encoded.txt", "w")

    write = ""
    count = 0
    lnIn = binFile.readline()
    while lnIn != "":
        count += 1
        lnIn = lnIn.strip()

        if lnIn[0:4] == ".END":
            write = "@\n"
            count = 0           # reset count
        elif lnIn[0:5] == ".ORIG":
            if lnIn[6] == 'X':
                write = lnIn[7:] + "\n"
            elif lnIn[6] == '#':
                write = hex(int(lnIn[7:]))[2:] + "\n"
            while len(write) < 5:
                write = '0' + write
            count = 0           # reset count
        else:
            write = chr(int(lnIn[0:4], 2) + 0x60)
            write += chr(int(lnIn[4:8], 2) + 0x60)
            write += chr(int(lnIn[8:12], 2) + 0x60)
            write += chr(int(lnIn[12:16], 2) + 0x60)
            if count >= 12:     # the buffer size of Mega and Uno is only 64 bytes, don't blow the buffer! (48 is safe)
                write += "\n"
                count = 0

        file.write(write)
        lnIn = binFile.readline()

    binFile.close()
    file.close()
