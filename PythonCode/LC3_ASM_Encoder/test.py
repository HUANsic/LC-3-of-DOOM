import codeSplitter
import cleaner
import LC3


fileName = "draft0"
cleaner.cleanUp(fileName)   # creates the -cln.txt

myLC3 = LC3.LC3Assembler()
myLC3.getLabel(fileName)    # scans through the -cln.txt to save all labels
myLC3.feedDoc(fileName)     # creates the -bin.txt
codeSplitter.convertTwo(fileName)  # creates the -a.txt and -b.txt
codeSplitter.convertOne(fileName)   # creates the -encoded.txt
