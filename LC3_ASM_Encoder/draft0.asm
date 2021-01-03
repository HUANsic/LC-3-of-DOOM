; OPERATING SYSTEM CODE ----------------------------------------------
        .ORIG x500
        LD R0, VEC
        LD R1, ISR
        ; (1) Initialize interrupt vector table with the starting address of ISR.
        STR R1, R0, #0
        ; (2) Set bit 14 of KBSR. [To Enable Interrupt] A | B = (A' & B')'
        LDI R3, KBSR
        NOT R3, R3
        LD R2, MASK
        AND R3, R3, R2
        NOT R3, R3
	    STI R3, KBSR
        ; (3) Set up system stack to enter user space. So that PC can return to the main user program at x3000.
	        ; R6 is the Stack Pointer. Remember to Push PC and PSR in the right order. Hint: Refer State Graph
        LD R0, PSR
        STR R0, R6, #0
        ADD R6, R6, #-1
        LD R0, PC
        STR R0, R6, #0
        ; (4) Enter user Program.
        RTI
        
VEC     .FILL x0180         ;INTERRUPT VECTOR
ISR     .FILL x1700         ;INTERRUPT SERVICE ROUTINE (START ADDRESS)
KBSR    .FILL xFE00         ;1111 1110 0000 0000
MASK    .FILL xBFFF         ;!(1 << IE)
PSR     .FILL x8002         ;1000 0000 0000 0010
PC      .FILL x3000
PSRLOC  .FILL xFFFC
        .END
; END OF OS --------------------------------------------------------------

; INTERRUPT SERVICE ROUTINE ----------------------------------------------
        .ORIG x1700
        ST R0, SAVER0
        ST R1, SAVER1
        ST R2, SAVER2
        ST R7, SAVER7

        ; CHECK THE KIND OF CHARACTER TYPED AND PRINT THE APPROPRIATE PROMPT
        LDI R2, KBDR
        LD R1, ASCII_NUM
        ;IF THE RESULT IS NEGATIVE, IT GOES TO "OTHERS"
        ADD R2, R2, R1
        BRZP #3
        LEA R0, STRING4
        JSR PUTS_
        HALT
        ;IF THE RESULT IS NEGATIVE, IT GOES TO "NUMBERS"
        ADD R2, R2, #-10
        BRZP #3
        LEA R0, STRING3
        JSR PUTS_
        BR ENDI
        ;IF THE RESULT IS NEGATIVE, IT GOES TO "OTHERS"
        ADD R2, R2, #-7
        BRZP #3
        LEA R0, STRING4
        JSR PUTS_
        HALT
        ;IF THE RESULT IS NEGATIVE, IT GOES TO "UPPER"
        ADD R2, R2, #-16
        ADD R2, R2, #-10
        BRZP #3
        LEA R0, STRING1
        JSR PUTS_
        BR ENDI
        ;IF THE RESULT IS NEGATIVE, IT GOES TO "OTHERS"
        ADD R2, R2, #-6
        BRZP #3
        LEA R0, STRING4
        JSR PUTS_
        HALT
        ;IF THE RESULT IS NEGATIVE, IT GOES TO "LOWER"
        ADD R2, R2, #-16
        ADD R2, R2, #-10
        BRZP #3
        LEA R0, STRING2
        JSR PUTS_
        BR ENDI
        ;OTHERWISE, "OTHERS"
        ADD R2, R2, #-6
        BRZP #3
        LEA R0, STRING4
        JSR PUTS_
        HALT

ENDI    LD R0, SAVER0
        LD R1, SAVER1
        LD R2, SAVER2
        LD R7, SAVER7
        RTI
; END OF INTERRUPT MAIN

;MY OWN PUTS TRAP (SUBR0)
PUTS_   ST R1, SVR1
        ST R2, SVR2
        
        LDR R1, R0, #0          ;TEST IF THE STRING IS EMPTY
        BRZ END0
        
JMP0    LDI R2, DSR             ;THE POLLING
        BRZP #-2
        STI R1, DDR
        
        ADD R0, R0, #1          ;INCREMENT TO NEXT ADDRESS, LOAD NEXT CHAR, AND TEST IF NULL
        LDR R1, R0, #0
        BRNP JMP0
        
END0    LD R1, SVR1
        LD R2, SVR2
        RET
SVR1    .BLKW   X1
SVR2    .BLKW   X1
; END OF SUBR0

ASCII_NUM .FILL x-30
;ASCII_LC  .FILL x-61
;ASCII_UC  .FILL x-41
KBDR    .FILL   xFE02
DSR     .FILL   XFE04
DDR     .FILL   XFE06
STRING1 .STRINGZ    "\nPractice Social Distancing\n"
STRING2 .STRINGZ    "\nWash your Hands frequently\n"
STRING3 .STRINGZ    "\nStay Home, Stay Safe\n"
STRING4 .STRINGZ    "\n ---------- END OF EE306 LABS -------------\n"
SAVER0  .BLKW   x1
SAVER1  .BLKW   x1
SAVER2  .BLKW   x1
SAVER7  .BLKW   x1
        .END
; END OF ENTIRE INTERRUPT ------------------------------

; USER PROGRAM: PRINT THE MESSAGE "WHAT STARTS HERE CHANGES THE WORLD" WITH A DELAY LOGIC
        .ORIG x3000
AGAIN   LEA R0, MESSAGE
        LD R1, CNT
        ADD R1, R1, #-1
        BRNP #-2
        
        PUTS
        BR AGAIN

CNT     .FILL xFFFF
MESSAGE .STRINGZ  "WHAT STARTS HERE CHANGES THE WORLD\n"
        .END
        