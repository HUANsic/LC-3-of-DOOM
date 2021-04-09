; this is just a demo file to show how code will be like once the linker is completed
; in this file, I will manually convert a simple C code into assembly
; for the first demonstration, I will show the steps to compile the most basic line of code: "int main(){return 1;}"


; First, the lexer tokenizes the string into several parts: "int", "main", "(", ")", "{", "return", "1", ";", "}"
; so, it will be converted into 9 byte-of-16-bit-s (byte for short).


; Second, the parser forms a parse tree by stacking: (scanning from left to right)
;
; at the beginning, it scans a declaration, so set declaration flag. It initializes variable/method initialization process: 
;    adding its name pointer, pushing it into the identifier stack, and reserve one slot for its type of declarence(variable or method)
; ----------------- step 1 -----------------
; operation stack:  
; output stack:     
;
; then, it scans "main", which is an identitier, store the identifier in the identifier stack and store the pointer to its identifier in the declaration block
; if the name repeats, raise error. (panic)
;       IF IT IS NAMED "main", STORE THE LOCATION OF IT, SINCE IT IS THE ENTRANCE TO THIS ENTIRE PROGRAM!!!!
; ----------------- step 2 -----------------
; operation stack:  
; output stack:     
;
; next, it scans "(", which, with combination of the declaration flag, indicates that the current declaration is a method declaration, prepare for parameter init
; ----------------- step 3 -----------------
; operation stack:  
; output stack:     
;
; then, it scans ")", which ends the parameter input
; ----------------- step 4 -----------------
; operation stack:  
; output stack:     
;
; next, it scans "{", which starts the body of function, switches the scope to current method (so that extra declaration falls under this method) by stacking
; ----------------- step 5 -----------------
; operation stack:  
; output stack:     
;
; then, it scans "return", which is a operational keyword; since operation stack is empty, push it in
; ----------------- step 6 -----------------
; operation stack:  return
; output stack:     
;
; next, it scans "1", a literal, is pushed into the method's literal stack, and here, also pushed to the output
; ----------------- step 7 -----------------
; operation stack:  return
; output stack:     1
;
; then, it scans ";", pop everything in operation stack in order and push to output
; ----------------- step 8 -----------------
; operation stack:  
; output stack:     1       return
;
; next, it scans "}", which indicates to exit current scope to the last scope; pop current scope off the stack.
;       if current scope is a function, you might want to move on to next step of converting those tokens into machine code
; ----------------- step 9 -----------------
; operation stack:  
; output stack:     1       return
;
; input empty (EOF), check for remaining operations and panic if there's operations left
; ----------------- step 10 -----------------
; operation stack:
; output stack:     1       return

; note: METHOD FRAME: local variable(s), global_temp2, global_temp1, global_temp0, last frame pointer, return address, return value, top to bottom, stack grows from larger to lower
;
; Third, assemble (and link) the program together
;   when first entered the program, it calls the "main" method, which pushes its method frame into the executing method stack: (R6 stack pointer) (R5 frome ptr)
;       STR R5, R6, #-2         ; STORE CALLER FRAME POINTER
;       STR R7, R6, #-1         ; STORE RETURN ADDRESS
;       ADD R5, R6, #0          ; COPY THE CURRENT FRAME POINTER
;       ADD R6, R6, #-5         ; MOVE THE POINTER (SHOULD BE -6 HERE, BUT SINCE ~R4 is neg(R4)-1, aka R6 is subtracting (R4 + 1), it is -5 here)
;       NOT R4, R4
;       ADD R6, R6, R4          ; THESE THREE LINES ADD THE LOCAL VARIABLES (FOR NOW THEY ARE ALL INT TYPES)
;
; "1"-> ADD R0, R5, #-6         ; #-6 means that the memory location of the "1" literal has an offset of -6 with respect to the frame pointer
;
;   RETURN statement:
;       LDR R0, R0, #0
;       STR R0, R5, #0
;
;   when exiting the method, pop its method frame from stack
;       ADD R6, R5, #0          ; THE "NEXT" FRAME POINTER
;       LDR R5, R6, #-2         ; POP CALLER FRAME POINTER
;       ADD R0, R6, #0          ; ALSO COPY THE ADDRESS OF THE RETURNED VALUE
;       LDR R7, R6, #-1         ; POP RETURN ADDRESS IN R7
;       RET                     ; RETURN TO ADDRESS IN R7
;
;   if the last method popped is the last one, it should pop back to the operating system and halt


; Assuming there the "main" method that the compiler has caught in last steps
; Fourth and last, copy the program as a whole and paste it into somewhere safe to execute: 
.orig x3000
; of course, you need to load the pointers first
ld r5, ld_r5
ld r6, ld_r6
ld r7, ld_r7
and r4, r4, #0
add r4, r4, #1


STR R5, R6, #-2         ; STORE CALLER FRAME POINTER
STR R7, R6, #-1         ; STORE RETURN ADDRESS
ADD R5, R6, #0          ; COPY THE CURRENT FRAME POINTER
ADD R6, R6, #-5         ; MOVE THE POINTER (SHOULD BE -6 HERE, BUT SINCE ~R4 is neg(R4)-1, and R6 is subtracting (R4 + 1), it is -5 here)
NOT R4, R4
ADD R6, R6, R4          ; THESE THREE LINES ADD THE LOCAL VARIABLES (FOR NOW THEY ARE ALL INT TYPES)

not r4, r4
str r4, r6, #1          ; luckily, "1" is also the number of locals; load the literal (it should be included within the function definition)

ADD R0, R5, #-6         ; #-6 means that the memory location of the "1" literal has an offset of -6 with respect to the frame pointer

LDR R0, R0, #0          ; return
STR R0, R5, #0

ADD R6, R5, #0          ; THE "NEXT" FRAME POINTER
LDR R5, R6, #-2         ; POP CALLER FRAME POINTER
ADD R0, R6, #0          ; ALSO COPY THE ADDRESS OF THE RETURNED VALUE
LDR R7, R6, #-1         ; POP RETURN ADDRESS IN R7
RET                     ; RETURN TO ADDRESS IN R7

ld_r7 .fill the_halt
ld_r6 .fill init_frame_ptr
ld_r5 .fill init_frame_ptr  ; too far for LEA opcode to reach down there; must have a place to make it in reach
.end

; extra code for the entire program
.orig x4000
.blkw xF9                   ; x4000 + xF9 + #8 = x4100, just to make it look nice
.blkw #1; location is pointed by R6
.fill #1                    ; the "1" literal location
.blkw #3                    ; the three global_temp# locations
.blkw #1                    ; just null; the last frame address: the os has no frame --- it is not a method of user program
.blkw #1                    ; points to the "halt" in the operating system; this field is the return address
init_frame_ptr .fill init_frame_ptr     ; return value is 0 for now, location is pointed by R5

the_halt halt
.end


