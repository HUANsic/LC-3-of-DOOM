import getch
from time import sleep
while True:
    char = getch.getch()
    if char == 111:
        print("test")
        break
    sleep(1)
