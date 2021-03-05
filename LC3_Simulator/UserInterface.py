from tkinter import *
from tkinter import ttk, messagebox, simpledialog
from pynput import keyboard
import LC3_Simulator
import Virtual_Raw
import pyperclip
import os

debug: bool = True
kb = Virtual_Raw.Keyboard(4)
csl = Virtual_Raw.Console()
ram = Virtual_Raw.RAM(16, 12)
vm = Virtual_Raw.virtual_lc3(debug=debug)
asmblr = LC3_Simulator.Assembler(vm, kb, csl, ram, debug)

keyboardInputValid: bool = False


def newFile():
    """ just refreshes the old text input box (coding area)"""
    if debug:
        print("\nnewFile initiating")
    result = messagebox.askyesno("Are You Sure?",
                                 "The code will be cleared without saving, do you still want to proceed?")
    if result:
        if debug:
            print("\tClearing console")
        console.delete(1.0, END)
        if debug:
            print("\tCreating new File Name")
        giveName()
        if debug:
            print("\tDone creating new coding area")
    else:
        if debug:
            print("\tnewFile initiation canceled")


def openFile():
    global currentFileName
    if debug:
        print("\nOpenFile Pressed")
    while True:
        fName: str = simpledialog.askstring("Open a file",
                                            "Please enter the file name (without .asm extension)")
        if fName is None:
            if debug:
                print("\tOpen file canceled")
            return
        if fName == "":
            messagebox.showerror("Invalid Input", "File Name Cannot Be Empty!")
        if not os.path.exists(fName + ".asm"):
            messagebox.showerror("Invalid Input", "Could not find target file!")
        else:
            break

    if debug:
        print("\tAttempting to open file ", fName, ".asm\n", end="")
    readStr = None
    try:
        file = open(fName + ".asm", "r")
        readStr = file.read()
        file.close()
        if debug:
            print("\tFile read successfully!")
    except OSError:
        messagebox.showerror("Cannot open file!", "Sorry, the file is unable to be accessed.")
    currentFileName = fName
    if readStr is not None:
        codeInput.delete(1.0, END)
        codeInput.insert(1.0, readStr)
        fileNameEntry.delete(0, END)
        fileNameEntry.insert(0, currentFileName)
        if debug:
            print("\tSuccessfully written file content to coding area!")


def saveFile():
    global currentFileName
    if debug:
        print("\nSaving File")
    readFileName: str = fileNameEntry.get().strip()
    if readFileName == "":
        giveName()
    else:
        currentFileName = readFileName

    if debug:
        print("\tSaving file to", currentFileName + ".asm")
    try:
        file = open(currentFileName + ".asm", "w")
        file.write(codeInput.get(1.0, END)[:-1])
        file.close()
        if debug:
            print("\tFile saved successfully!")
    except OSError:
        if debug:
            print("\tSomething went wrong trying to open the file!")
        else:
            messagebox.showerror("Cannot open file!", "Sorry, the file is unable to be accessed.")


def exitSim():
    if debug:
        print("\nExit Process Initiated")
    result = messagebox.askyesno("You are about to exit", "Are You Sure?")
    if result:
        if debug:
            print("\tLeaving Simulator")
        root.quit()
    else:
        if debug:
            print("\tExit Simulator Canceled")


def aboutSim():
    if debug:
        print("\nMore about this Sim...")
    ...


def setPreference():
    if debug:
        print("\nSet Preference")
    ...


# assembles the entire thing: first, check; then, load memory
def lc3Assemble():
    if debug:
        print("\nAssembling", end="")
    if debug:
        print("\nChecking", end="")
    saveFile()
    cleanedStrLst: list = asmblr.cleanup(codeInput.get(1.0, END))
    if debug:
        print("\tInput cleaned:")
        print("\t\t", cleanedStrLst)
        print("\tGetting Labels")
    try:
        asmblr.labels = asmblr.getLabel(cleanedStrLst)
    except LC3_Simulator.InvalidFormatError as err:
        messagebox.showerror("Oops!", "Invalid Format Error: " + err.__str__())
        return
    if debug:
        print("\tGot labels:")
        print("\t\t", asmblr.labels)
    try:
        memory: list = asmblr.encode(cleanedStrLst)
    except LC3_Simulator.InvalidFormatError as err:
        messagebox.showerror("Oops!", "Invalid Format Error: " + err.__str__())
        return
    asmblr.assemble(memory)
    if debug:
        print("\tMemory in place!")


# goes over the code once, pop up windows if there's an error
def lc3Check():
    if debug:
        print("\nChecking")
    saveFile()
    cleanedStrLst: list = asmblr.cleanup(codeInput.get(1.0, END))
    if debug:
        print("\tInput cleaned")
        print("\tGetting Labels")
    try:
        asmblr.labels = asmblr.getLabel(cleanedStrLst)
    except LC3_Simulator.InvalidFormatError as err:
        messagebox.showerror("Oops!", "Invalid Format Error: " + err.__str__())
        return
    if debug:
        print("\tGot labels")
    try:
        asmblr.encode(cleanedStrLst)
    except LC3_Simulator.InvalidFormatError as err:
        messagebox.showerror("Oops!", "Invalid Format Error: " + err.__str__())
        return
    messagebox.showinfo("Yes!", "The code can be assembled without an exception! Good job!")


# dealing with console
def clearConsole():
    if debug:
        print("\nClearing console")
    console.delete(1.0, END)
    if debug:
        print("\tConsole Cleared!")


def copyConsole():
    if debug:
        print("\nCopying console")
    pyperclip.copy(console.get(1.0, END))
    if debug:
        print("\tConsole Copied!")


# this is for the file
def giveName():
    global currentFileName
    i = 0
    while True:
        currentFileName = "draft" + str(i)
        if not os.path.exists(currentFileName + ".asm"):
            break
        i += 1
    fileNameEntry.delete(1, END)
    fileNameEntry.insert(1, currentFileName)


# these are for the keyboard
# turns out that you can't use the window while the program is executing something
"""
def keyPressed(ch: str):
    global SHIFT_FLAG, CONTROL_FLAG, CAPSLOCK_FLAG
    if CAPSLOCK_FLAG and ord('a') <= ord(ch) <= ord('z'):
        if not SHIFT_FLAG:
            ch = ch.upper()
    elif SHIFT_FLAG:
        ch = upperCases.setdefault(ch, ch)  # pass the upper case (shifted) key into ch, or keep it as if

    kb.dataRegister[0] = ch & 0x00FF
    kb.statusRegister[0] |= 0x8000  # ready bit


def toggleControl():
    global controlButton0, controlButton1, CONTROL_FLAG
    CONTROL_FLAG = not CONTROL_FLAG  # toggle
    controlButton0.config(bg=("lavender" if CONTROL_FLAG else "#F0F0F0"))
    controlButton1.config(bg=("lavender" if CONTROL_FLAG else "#F0F0F0"))


def toggleShift():
    global shiftButton0, shiftButton1, SHIFT_FLAG
    SHIFT_FLAG = not SHIFT_FLAG  # toggle
    shiftButton0.config(bg=("lavender" if SHIFT_FLAG else "#F0F0F0"))
    shiftButton1.config(bg=("lavender" if SHIFT_FLAG else "#F0F0F0"))


def toggleCapslock():
    global capslockButton, CAPSLOCK_FLAG
    CAPSLOCK_FLAG = not CAPSLOCK_FLAG  # toggle
    capslockButton.config(bg=("lavender" if CAPSLOCK_FLAG else "#F0F0F0"))


def addKeyboard(kbf: Frame):
    global shiftButton0, shiftButton1, controlButton0, controlButton1, capslockButton
    # create five rows for buttons
    topRow = Frame(kbf, width=33, height=2)
    secondRow = Frame(kbf, width=33, height=2)
    thirdRow = Frame(kbf, width=33, height=2)
    forthRow = Frame(kbf, width=33, height=2)
    lastRow = Frame(kbf, width=33, height=2)
    # fill in the buttons
    Button(topRow, text="~\n`", height=2, width=3, command=lambda: keyPressed('`')).pack(side=LEFT)
    Button(topRow, text="!\n1", height=2, width=3, command=lambda: keyPressed('1')).pack(side=LEFT)
    Button(topRow, text="@\n2", height=2, width=3, command=lambda: keyPressed('2')).pack(side=LEFT)
    Button(topRow, text="#\n3", height=2, width=3, command=lambda: keyPressed('3')).pack(side=LEFT)
    Button(topRow, text="$\n4", height=2, width=3, command=lambda: keyPressed('4')).pack(side=LEFT)
    Button(topRow, text="%\n5", height=2, width=3, command=lambda: keyPressed('5')).pack(side=LEFT)
    Button(topRow, text="^\n6", height=2, width=3, command=lambda: keyPressed('6')).pack(side=LEFT)
    Button(topRow, text="&\n7", height=2, width=3, command=lambda: keyPressed('7')).pack(side=LEFT)
    Button(topRow, text="*\n8", height=2, width=3, command=lambda: keyPressed('8')).pack(side=LEFT)
    Button(topRow, text="(\n9", height=2, width=3, command=lambda: keyPressed('9')).pack(side=LEFT)
    Button(topRow, text=")\n0", height=2, width=3, command=lambda: keyPressed('0')).pack(side=LEFT)
    Button(topRow, text="_\n-", height=2, width=3, command=lambda: keyPressed('-')).pack(side=LEFT)
    Button(topRow, text="+\n=", height=2, width=3, command=lambda: keyPressed('=')).pack(side=LEFT)
    Button(topRow, text="<---", height=2, width=6, command=lambda: keyPressed(chr(8))).pack(side=LEFT)
    topRow.pack(side=TOP)
    Button(secondRow, text="Tab", height=2, width=5, command=lambda: keyPressed('\t')).pack(side=LEFT)
    Button(secondRow, text="Q\n", height=2, width=3, command=lambda: keyPressed('q')).pack(side=LEFT)
    Button(secondRow, text="W\n", height=2, width=3, command=lambda: keyPressed('w')).pack(side=LEFT)
    Button(secondRow, text="E\n", height=2, width=3, command=lambda: keyPressed('e')).pack(side=LEFT)
    Button(secondRow, text="R\n", height=2, width=3, command=lambda: keyPressed('r')).pack(side=LEFT)
    Button(secondRow, text="T\n", height=2, width=3, command=lambda: keyPressed('t')).pack(side=LEFT)
    Button(secondRow, text="Y\n", height=2, width=3, command=lambda: keyPressed('y')).pack(side=LEFT)
    Button(secondRow, text="U\n", height=2, width=3, command=lambda: keyPressed('u')).pack(side=LEFT)
    Button(secondRow, text="I\n", height=2, width=3, command=lambda: keyPressed('i')).pack(side=LEFT)
    Button(secondRow, text="O\n", height=2, width=3, command=lambda: keyPressed('o')).pack(side=LEFT)
    Button(secondRow, text="P\n", height=2, width=3, command=lambda: keyPressed('p')).pack(side=LEFT)
    Button(secondRow, text="{\n[", height=2, width=3, command=lambda: keyPressed('[')).pack(side=LEFT)
    Button(secondRow, text="}\n]", height=2, width=3, command=lambda: keyPressed(']')).pack(side=LEFT)
    Button(secondRow, text="|\n\\", height=2, width=4, command=lambda: keyPressed('\\')).pack(side=LEFT)
    secondRow.pack(side=TOP)
    capslockButton = Button(thirdRow, text="CapsLk", height=2, width=6, command=lambda: toggleCapslock())
    capslockButton.pack(side=LEFT)
    Button(thirdRow, text="A\n", height=2, width=3, command=lambda: keyPressed('a')).pack(side=LEFT)
    Button(thirdRow, text="S\n", height=2, width=3, command=lambda: keyPressed('s')).pack(side=LEFT)
    Button(thirdRow, text="D\n", height=2, width=3, command=lambda: keyPressed('d')).pack(side=LEFT)
    Button(thirdRow, text="F\n", height=2, width=3, command=lambda: keyPressed('f')).pack(side=LEFT)
    Button(thirdRow, text="G\n", height=2, width=3, command=lambda: keyPressed('g')).pack(side=LEFT)
    Button(thirdRow, text="H\n", height=2, width=3, command=lambda: keyPressed('h')).pack(side=LEFT)
    Button(thirdRow, text="J\n", height=2, width=3, command=lambda: keyPressed('j')).pack(side=LEFT)
    Button(thirdRow, text="K\n", height=2, width=3, command=lambda: keyPressed('k')).pack(side=LEFT)
    Button(thirdRow, text="L\n", height=2, width=3, command=lambda: keyPressed('l')).pack(side=LEFT)
    Button(thirdRow, text=":\n;", height=2, width=3, command=lambda: keyPressed(';')).pack(side=LEFT)
    Button(thirdRow, text="\"\n\'", height=2, width=3, command=lambda: keyPressed('\'')).pack(side=LEFT)
    Button(thirdRow, text="Enter", height=2, width=6, command=lambda: keyPressed('\n')).pack(side=LEFT)
    thirdRow.pack(side=TOP)
    shiftButton0 = Button(forthRow, text="Shift", height=2, width=7, command=lambda: toggleShift())
    shiftButton0.pack(side=LEFT)
    Button(forthRow, text="Z", height=2, width=3, command=lambda: keyPressed('z')).pack(side=LEFT)
    Button(forthRow, text="X", height=2, width=3, command=lambda: keyPressed('x')).pack(side=LEFT)
    Button(forthRow, text="C", height=2, width=3, command=lambda: keyPressed('c')).pack(side=LEFT)
    Button(forthRow, text="V", height=2, width=3, command=lambda: keyPressed('v')).pack(side=LEFT)
    Button(forthRow, text="B", height=2, width=3, command=lambda: keyPressed('b')).pack(side=LEFT)
    Button(forthRow, text="N", height=2, width=3, command=lambda: keyPressed('n')).pack(side=LEFT)
    Button(forthRow, text="M", height=2, width=3, command=lambda: keyPressed('m')).pack(side=LEFT)
    Button(forthRow, text="<\n,", height=2, width=3, command=lambda: keyPressed(',')).pack(side=LEFT)
    Button(forthRow, text=">\n.", height=2, width=3, command=lambda: keyPressed('.')).pack(side=LEFT)
    Button(forthRow, text="?\n/", height=2, width=3, command=lambda: keyPressed('/')).pack(side=LEFT)
    shiftButton1 = Button(forthRow, text="Shift", height=2, width=7, command=lambda: toggleShift())
    shiftButton1.pack(side=LEFT)
    forthRow.pack(side=TOP)
    controlButton0 = Button(lastRow, text="Ctrl", height=2, width=8, command=lambda: toggleControl())
    controlButton0.pack(side=LEFT)
    Button(lastRow, text="Esc", height=2, width=3, command=lambda: keyPressed(chr(27))).pack(side=LEFT)
    Button(lastRow, text="Space", height=2, width=25, command=lambda: keyPressed(chr(0x20))).pack(side=LEFT)
    Button(lastRow, text="Del", height=2, width=3, command=lambda: keyPressed(chr(127))).pack(side=LEFT)
    controlButton1 = Button(lastRow, text="Ctrl", height=2, width=8, command=lambda: toggleControl())
    controlButton1.pack(side=LEFT)
    lastRow.pack(side=TOP)
    return kbf
"""


# but you can set up action listeners
def keyPressed(event):
    print(event)
    if not keyboardInputValid:
        return
    if event == keyboard.Key.esc:
        vm.MCR.value[0] = 0
    if type(event) is str:
        kb.dataRegister[0] = ord(event)
        kb.statusRegister[0] |= 0x8000
    if debug:
        print("\tKey Pressed:", event)
    if event == keyboard.Key.esc:
        return False


# for running and debugging in simulator
def run():
    if debug:
        print("\nAttempting to run")
    asmblr.run()
    if debug:
        print("\tRun successful")


def debug(debugAddress: int):
    if debug:
        print("\nAttempting to enter debug mode")
    funcId = root.bind("<Key>", keyPressed)
    asmblr.run(debugAddress)
    root.unbind("<Key>", funcId)
    if debug:
        print("\tHit breakpoint or Halt!")


def stepIn():
    if debug:
        print("\nAttempting to step in")
    asmblr.step()
    if debug:
        print("\tStep in successful")


""" here starts the main code"""
# declare some variables and flags for later use
shiftButton0: Button
shiftButton1: Button
controlButton0: Button
controlButton1: Button
capslockButton: Button
fileNameEntry: Entry

CAPSLOCK_FLAG: bool = False
CONTROL_FLAG: bool = False
SHIFT_FLAG: bool = False  # default is false

currentFileName: str = ""

# dictionary from lower-case to upper-case
upperCases = {
    'a': 'A',
    'b': 'B',
    'c': 'C',
    'd': 'D',
    'e': 'E',
    'f': 'F',
    'g': 'G',
    'h': 'H',
    'i': 'I',
    'j': 'J',
    'k': 'K',
    'l': 'L',
    'm': 'M',
    'n': 'N',
    'o': 'O',
    'p': 'P',
    'q': 'Q',
    'r': 'R',
    's': 'S',
    't': 'T',
    'u': 'U',
    'v': 'V',
    'w': 'W',
    'x': 'X',
    'y': 'Y',
    'z': 'Z',
    '1': '!',
    '2': '@',
    '3': '#',
    '4': '$',
    '5': '%',
    '6': '^',
    '7': '&',
    '8': '*',
    '9': '(',
    '0': ')',
    '`': '~',
    '-': '_',
    '=': '+',
    ',': '<',
    '.': '>',
    '/': '?',
    ';': ':',
    '\'': '\"',
    '[': '{',
    ']': '}',
    '\\': '|'
}

# setup root window
root = Tk()
root.title("LC-3 Simulator")
root.geometry("480x360")

# set menus
mainMenu = Menu(root)
root.config(menu=mainMenu)
fileMenu = Menu(mainMenu)
helpMenu = Menu(mainMenu)
codeMenu = Menu(mainMenu)
consoleMenu = Menu(mainMenu)
debugMenu = Menu(mainMenu)

mainMenu.add_cascade(label="File", menu=fileMenu)
mainMenu.add_cascade(label="Code", menu=codeMenu)
mainMenu.add_cascade(label="Console", menu=consoleMenu)
mainMenu.add_cascade(label="Debug", menu=debugMenu)
mainMenu.add_cascade(label="Help", menu=helpMenu)
mainMenu.add_command(label="Exit", command=exitSim)

fileMenu.add_command(label="New", command=newFile)
fileMenu.add_command(label="Open", command=openFile)
fileMenu.add_command(label="Save", command=saveFile)
fileMenu.add_command(label="Preference", command=setPreference)

codeMenu.add_command(label="Assemble", command=lc3Assemble)
codeMenu.add_command(label="Check", command=lc3Check)

consoleMenu.add_command(label="Copy", command=copyConsole)
consoleMenu.add_command(label="Clear", command=clearConsole)

debugMenu.add_command(label="Run", command=run)
debugMenu.add_command(label="Step In", command=stepIn)

helpMenu.add_command(label="About", command=aboutSim)

# set components (widgets)
tabControl = ttk.Notebook(root)

codingFrame = ttk.Frame(tabControl)
consoleFrame = ttk.Frame(tabControl)
codingFrame.bind("<KeyPressed>")

tabControl.add(codingFrame, text="Code")
tabControl.add(consoleFrame, text="I/O")

fileNameFrame = Frame(codingFrame, height=1)

codeInput = Text(codingFrame, bg="ivory2")
console = Text(consoleFrame, bg="dark slate gray", fg="LightCyan2")
csl.setTextField(console)
fileNameLabel = Label(fileNameFrame, text="File Name: ")
fileNameEntry = Entry(fileNameFrame)
giveName()
# kbd = Frame(consoleFrame, height=300)
# kbd = addKeyboard(kbd)

fileNameLabel.pack(side=LEFT)
fileNameEntry.pack(fill=X, expand=True, side=LEFT)
fileNameFrame.pack(fill=X, side=TOP)
codeInput.pack(fill=BOTH, expand=True)
# kbd.pack(fill=X, expand=True, side=BOTTOM)
console.pack(fill=BOTH, expand=True)

tabControl.pack(expand=True, fill=BOTH)

# ready to go
root.bind("<Key>", keyPressed)
root.mainloop()
