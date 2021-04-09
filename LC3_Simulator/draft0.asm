.orig x3000
ldi r1, KBSR
BRzp #-2
ldi r0, KBDR
ldi r1, ESC
add r0, r0, r1
brnp #-6
halt
KBSR .fill xfe00
KBDR .fill xfe02
ESC .fill #-48
.end






