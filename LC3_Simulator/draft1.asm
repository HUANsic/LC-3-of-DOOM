.orig x3000
trap x30
.end

.orig x0030
.fill x4000
.end

.orig x4000
ldi r0, location
ld r1, offset
add r0, r0, r1
out
ld r1, userMode
sti r1, location
out
ldi r0, location
ld r1, offset
add r0, r0, r1
out
halt
location .fill xfffc
offset .fill x0030
userMode .fill x8002
.end


