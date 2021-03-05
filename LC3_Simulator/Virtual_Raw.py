from tkinter import *


class InvalidRegisterError(Exception):
    def __init__(self, strIn):
        self.input = strIn
        super().__init__()

    def __str__(self):
        return f'\"{self.input}\" can\'t be found in register file.'


class IllegalCode(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__()

    def __str__(self):
        return f'Illegal Opcode \"{self.code}\".'


class IllegalKey(Exception):
    def __init__(self, key: str):
        self.key = key
        super().__init__()

    def __str__(self):
        return f'Illegal key \"{self.key}\".'


class externalRegister:
    name: str
    writable: bool
    readable: bool
    value: list

    def update(self):
        ...


class MachineControlRegister(externalRegister):
    name = "MCR"
    writable = True
    readable = True
    value = [0]


class ProgramStatusRegister(externalRegister):
    name = "PSR"
    writable = True
    readable = True
    value = [0]


class Device:
    type: str

    statusRegister: list = [0]
    SRWritable: bool
    SRReadable: bool

    dataRegister: list = [0]
    DRWritable: bool
    DRReadable: bool

    def update(self): ...


class Memory(Device):
    pagesBit: int
    colsBit: int
    pageAddressBuffer: int = 0
    columnAddressBuffer: int = 0

    SRWritable = True
    SRReadable = True
    DRWritable = True
    DRReadable = True
    # status register format:   0b  X   X   X   X   X   X   X   X   X   X   X   X   X   X   X   X
    #                             ready                                          setR setC  R   W
    # so you have two bytes in the data register, when one of row/col bit is set, the data is stored in
    # the corresponding address register. When the read bit is set, the memory reads and put the data in
    # data register and set the ready bit when it is ready (this program doesn't include the clearing and
    # setting of the ready bit)
    memory: list

    def __init__(self, pagesBit, colsBit):
        self.pagesBit = pagesBit
        self.colsBit = colsBit
        self.memory = [] * (2 ** (pagesBit + colsBit))

    def update(self):
        if self.statusRegister[0] & 0x0008 != 0:
            self.pageAddressBuffer = self.dataRegister[0]
        elif self.statusRegister[0] & 0x0004 != 0:
            self.columnAddressBuffer = self.dataRegister[0]
        elif self.statusRegister[0] & 0x0002 != 0:
            self.dataRegister[0] = self.memory[
                self.pageAddressBuffer * (2 ** self.colsBit) + self.columnAddressBuffer]
        elif self.statusRegister[0] & 0x0001 != 0:
            self.memory[self.pageAddressBuffer * (2 ** self.colsBit) + self.columnAddressBuffer] = self.dataRegister[0]
        self.statusRegister[0] = 0x8000  # well, just set it


class InputDevice(Device):
    priorityLevel: int
    ...


class Keyboard(InputDevice):
    """ a virtual keyboard class, holds its priority level, the KBSR and KBDR"""
    type = "keyboard"

    SRWritable = True
    DRWritable = False
    SRReadable = True
    DRReadable = True

    def __init__(self, priority: int):
        self.priorityLevel = priority


class Console(Device):
    """ a virtual console class, holds the DDR and DSR"""
    type = "display"
    consoleTextField: Text
    statusRegister = [0x8000]

    SRWritable = True
    DRWritable = True
    SRReadable = True
    DRReadable = False

    def setTextField(self, textField: Text):
        self.consoleTextField = textField

    def update(self):
        if self.statusRegister[0] & 0x8000 != 0:
            self.consoleTextField.insert(END, chr(self.dataRegister[0]))
            self.statusRegister[0] |= 0x8000
        # else, do nothing


class RAM(Memory):
    type = "RAM"


"""
note that I have combined the address/PC adder with the ALU
                 greatly simplified the control block
"""


class virtual_lc3:
    # some constants
    READ = True
    WRITE = False
    not_command = "NOT"
    and_command = "AND"
    add_command = "ADD"
    passa_command = "PASSA"

    # memory and registers
    myMemory: list
    RegFile = [0, 0, 0, 0, 0, 0, 0, 0]
    devices = {}  # e.g. {"keyboard": kb}
    deviceReg = {}  # e.g. {0xFE00: [kb.statusRegister]}
    regDeviceMap = {}  # e.g. {0xFE00: kb}
    deviceRegReadable = {}  # e.g. {0xFE00: readable}
    deviceRegWritable = {}  # e.g. {0xFE00: writable}

    MCR: MachineControlRegister
    PSR: ProgramStatusRegister

    PC = 0

    Priority: int = 0
    INTV: int = 0
    VECTOR: int = 0
    Saved_USP: int = 0
    Saved_SSP: int = 0

    # for simulator
    debugMode: bool = False
    debugAddress: int = -1

    # for debugging
    debug: bool

    def __init__(self, debug: bool, dbgAddress=-1):
        self.debugAddress = dbgAddress
        self.debug = debug

        newMCR = MachineControlRegister()
        self.MCR = newMCR
        self.devices["MCR"] = newMCR
        self.regDeviceMap[0xFFFE] = newMCR
        self.deviceReg[0xFFFE] = newMCR.value
        self.deviceRegWritable[0xFFFE] = True
        self.deviceRegReadable[0xFFFE] = True

        newPSR = ProgramStatusRegister()
        self.PSR = newPSR
        self.devices["PSR"] = newPSR
        self.regDeviceMap[0xFFFC] = newPSR
        self.deviceReg[0xFFFC] = newPSR.value
        self.deviceRegWritable[0xFFFC] = True
        self.deviceRegReadable[0xFFFC] = True

    # could add more registers (*regs) to the end
    def addDevice(self, device: Device, statusRegAdd: int, dataRegAdd: int) -> bool:
        if device.type not in self.devices and (statusRegAdd in self.deviceRegWritable or statusRegAdd in
                                                self.deviceRegReadable or dataRegAdd in self.deviceRegWritable or
                                                dataRegAdd in self.deviceRegReadable):
            return False
        self.devices[device.type] = device
        self.deviceReg[statusRegAdd] = device.statusRegister
        self.deviceReg[dataRegAdd] = device.dataRegister
        self.regDeviceMap[statusRegAdd] = device
        self.regDeviceMap[dataRegAdd] = device
        self.deviceRegReadable[statusRegAdd] = device.SRReadable
        self.deviceRegReadable[dataRegAdd] = device.DRReadable
        self.deviceRegWritable[statusRegAdd] = device.SRWritable
        self.deviceRegWritable[dataRegAdd] = device.DRWritable
        return True

    def setMemory(self, memory):
        self.myMemory = memory

    def mem(self, address, RW: bool, value: int = None):
        address &= 0x0FFFF
        if address == 0xFFFE or address == 0xFFFC:
            if self.PSR.value[0] & 0x8000 != 0:
                self.VECTOR = 0
                self.ex_int_enterSupervisorMode()
                return False
        if 0xFE00 <= address:
            if RW:
                if address in self.deviceRegReadable:
                    if self.deviceRegReadable[address]:
                        return self.deviceReg[address][0]
                return False
            else:
                if address in self.deviceRegWritable:
                    if self.deviceRegWritable[address]:
                        self.deviceReg[address][0] = value
                        self.regDeviceMap[address].update()
                        return True
                return False
        else:
            if RW:
                return self.myMemory[address]
            else:
                self.myMemory[address] = value
                return True

    def alu(self, valA, operation: str, valB: int = 0):
        retVal = 0
        if operation == self.not_command:
            retVal = ~valA
        elif operation == self.and_command:
            retVal = valA & valB
        elif operation == self.add_command:
            retVal = valA + valB
        elif operation == self.passa_command:  # shouldn't be used in this virtual machine
            retVal = valA

        retVal &= 0x0FFFF  # trap it in 16 bits
        return retVal

    def registerFile(self, register: int, RW: bool, value: int = 0):
        value = value & 0x0FFFF

        if RW:
            return self.RegFile[register]
        else:
            self.RegFile[register] = value
            conditionCode = 1 << (2 if (value & (1 << 15)) != 0 else (1 if value == 0 else 0))
            self.PSR.value[0] = self.PSR.value[0] & 0xFFF8 | conditionCode

    def control(self):
        # fetch
        address = self.PC
        self.PC += 1
        self.PC &= 0x0FFFF

        # test for interrupts (could add more here)
        if (self.devices["keyboard"].statusRegister[0] & (0b11 << 14)) == (0b11 << 14):
            self.INT_request(0x80, self.devices["keyboard"].priorityLevel)

        # test if do interrupt
        if self.Priority > ((self.PSR.value[0] & (0b111 << 8)) >> 8):
            if self.debug:
                print("\tInterrupt Triggered! Following vector", hex(self.VECTOR))
            self.VECTOR = self.INTV
            self.ex_int_enterSupervisorMode(self.Priority)
            return
        else:
            pass  # failed to initialize interrupt, just move on

        # real fetch
        if self.debug:
            print("\t\t\tFetching address", address)
        instruction = self.myMemory[address]

        # decode and execute
        opcode = (instruction & 0xF000) >> 12
        if self.debug:
            print("\t\t\t\tGot instruction", bin(instruction))
            print("\t\t\t\tAnd Operation Code", bin(opcode))

        if opcode == 0b0000:  # branch
            BEN = (self.PSR.value[0] & (1 << 2)) * (instruction & (1 << 11)) + (self.PSR.value[0] & (1 << 1)) * (
                    instruction & (1 << 10)) + (self.PSR.value[0] & (1 << 0)) * (instruction & (1 << 9)) \
                  + (1 if (instruction & (0b111 << 9)) == 0 else 0)  # branch enable
            if BEN != 0:
                SR = (instruction & 0x00FF) if (instruction & (1 << 8)) == 0 else (instruction | 0xFF00)
                self.PC = self.alu(self.PC, self.add_command, SR)

        elif opcode == 0b0001:  # ADD
            SR1 = self.registerFile(((0b111 << 6) & instruction) >> 6, self.READ)

            if (instruction & (1 << 5)) == 0:  # DR = SR1 + SR2
                SR2 = self.registerFile(0b111 & instruction, self.READ)
            else:  # DR = SR1 + SEXT[imm5]
                SR2 = (instruction & 0x000F) if (instruction & (1 << 4)) == 0 else (instruction | 0xFFF0)

            self.registerFile(((0b111 << 9) & instruction) >> 9, self.WRITE, self.alu(SR1, self.add_command, SR2))

        elif opcode == 0b0010:  # LD
            offset = (instruction & 0x00FF) if (instruction & (1 << 8)) == 0 else (instruction | 0xFF00)
            data = self.mem(self.alu(self.PC, self.add_command, offset), self.READ)
            if data is False:
                return
            self.registerFile((instruction & (0b111 << 9)) >> 9, self.WRITE, data)

        elif opcode == 0b0011:  # ST
            offset = (instruction & 0x00FF) if (instruction & (1 << 8)) == 0 else (instruction | 0xFF00)
            data = self.registerFile((instruction & (0b111 << 9)) >> 9, self.READ)
            self.mem(self.alu(self.PC, self.add_command, offset), self.WRITE, data)

        elif opcode == 0b0100:  # JSR
            self.registerFile(7, self.WRITE, self.PC)
            offset = (instruction & 0x00FF) if (instruction & (1 << 8)) == 0 else (instruction | 0xFF00)
            self.PC += offset

        elif opcode == 0b0101:  # AND
            SR1 = self.registerFile(((0b111 << 6) & instruction) >> 6, self.READ)

            if (instruction & (1 << 5)) == 0:  # DR = SR1 + SR2
                SR2 = self.registerFile(0b111 & instruction, self.READ)
            else:  # DR = SR1 + SEXT[imm5]
                SR2 = (instruction & 0x000F) if (instruction & (1 << 4)) == 0 else (instruction | 0xFFF0)

            self.registerFile(((0b111 << 9) & instruction) >> 9, self.WRITE, self.alu(SR1, self.and_command, SR2))

        elif opcode == 0b0110:  # LDR
            offset = (instruction & 0x001F) if (instruction & (1 << 5)) == 0 else (instruction | 0xFFE0)
            base = self.registerFile((instruction & (0b111 << 6)) >> 6, self.READ)
            address = self.alu(base, self.add_command, offset)
            data = self.mem(address, self.READ)
            if data is False:
                return
            self.registerFile((instruction & (0b111 << 9)) >> 9, self.WRITE, data)

        elif opcode == 0b0111:  # STR
            offset = (instruction & 0x001F) if (instruction & (1 << 5)) == 0 else (instruction | 0xFFE0)
            base = self.registerFile((instruction & (0b111 << 6)) >> 6, self.READ)
            data = self.registerFile((instruction & (0b111 << 9)) >> 9, self.READ)
            self.mem(self.alu(base, self.add_command, offset), self.WRITE, data)

        elif opcode == 0b1000:  # RTI
            if self.PSR.value[0] & 0x8000 != 0:
                self.VECTOR = 0x00
                self.ex_int_enterSupervisorMode()
            else:
                address = self.mem(self.registerFile(6, self.READ), self.READ)
                if address is False:
                    return
                self.PC = address
                self.registerFile(6, self.WRITE, self.registerFile(6, self.READ) + 1)
                value = self.mem(self.registerFile(6, self.READ), self.READ)
                if value is False:
                    return
                self.PSR.value[0] = value
                self.registerFile(6, self.WRITE, self.registerFile(6, self.READ) + 1)
                if self.PSR.value[0] & 0x8000 != 0:
                    self.Saved_SSP = self.registerFile(6, self.READ)
                    self.registerFile(6, self.WRITE, self.Saved_USP)

        elif opcode == 0b1001:  # NOT
            SR = self.registerFile(((0b111 << 6) & instruction) >> 6, self.READ)
            self.registerFile(((0b111 << 9) & instruction) >> 9, self.WRITE, self.alu(SR, self.not_command))

        elif opcode == 0b1010:  # LDI
            offset = (instruction & 0x00FF) if (instruction & (1 << 8)) == 0 else (instruction | 0xFF00)
            address = self.mem(self.alu(self.PC, self.add_command, offset), self.READ)
            if address is False:
                return
            data = self.mem(address, self.READ)
            if data is False:
                return
            self.registerFile((instruction & (0b111 << 9)) >> 9, self.WRITE, data)

        elif opcode == 0b1011:  # STI
            offset = (instruction & 0x00FF) if (instruction & (1 << 8)) == 0 else (instruction | 0xFF00)
            address = self.mem(self.alu(self.PC, self.add_command, offset), self.READ)
            if address is False:
                return
            data = self.registerFile((instruction & (0b111 << 9)) >> 9, self.READ)
            self.mem(address, self.WRITE, data)

        elif opcode == 0b1100:  # RET/JMP
            self.PC = self.registerFile((instruction & (0b111 << 6)) >> 6, self.READ)

        elif opcode == 0b1101:  # reserved
            self.VECTOR = 0x01
            self.ex_int_enterSupervisorMode()

        elif opcode == 0b1110:  # LEA
            offset = (instruction & 0x00FF) if (instruction & (1 << 8)) == 0 else (instruction | 0xFF00)
            self.registerFile(((0b111 << 9) & instruction) >> 9, self.WRITE,
                              self.alu(self.PC, self.add_command, offset))

        elif opcode == 0b1111:  # TRAP
            if (self.PSR.value[0] & (0b111 << 8)) != 0:  # initiate exception handling if current priority is > 0
                self.VECTOR = 0x02
                self.ex_int_enterSupervisorMode()
                return
            self.trap_enterSupervisorMode()
            self.PC = instruction & 0x00FF
            address = self.mem(self.PC, self.READ)
            if address is False:
                return
            self.PC = address

        else:  # should not happen
            self.VECTOR = 0x01
            self.ex_int_enterSupervisorMode()

    def INT_request(self, vector: int, priority: int):
        if priority > self.Priority:
            self.INTV = vector
            self.Priority = priority

    def ex_int_enterSupervisorMode(self, priority=0):
        self.enterSupervisorMode()
        self.mem(self.registerFile(6, self.READ), self.WRITE, self.PC - 1)
        self.PSR.value[0] = (self.PSR.value[0] & (~(0b111 << 8))) | (priority << 8)  # update priority
        self.PC = self.mem(0x0100 + self.VECTOR, self.READ)

    def trap_enterSupervisorMode(self):
        self.enterSupervisorMode()
        self.mem(self.registerFile(6, self.READ), self.WRITE, self.PC)
        self.PSR.value[0] = self.PSR.value[0] & (~(0b111 << 8))  # update priority to 0, which does nothing

    def enterSupervisorMode(self):
        self.registerFile(6, self.WRITE, self.registerFile(6, self.READ) - 1)
        self.mem(self.registerFile(6, self.READ), self.WRITE, self.PSR.value[0])
        if self.PSR.value[0] & 0x8000 != 0:
            self.Saved_SSP = self.registerFile(6, self.READ)
            self.registerFile(6, self.WRITE, self.Saved_USP)
        self.PSR.value[0] &= 0x7FFF
        self.registerFile(6, self.WRITE, self.registerFile(6, self.READ) - 1)
