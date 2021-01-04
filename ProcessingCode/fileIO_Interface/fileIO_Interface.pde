import processing.serial.*;

BufferedReader reader;
Serial arduino;

void setup() {
  arduino = new Serial(this, "COM3", 57600);
  reader = createReader("draft0-encoded.txt");
  
  // this part acts as a long delay until certain character is recieved
  char chr;
  while (true) {
    chr = arduino.readChar();
    if ((chr == 'O') || (chr == 'K') || (chr == '\n')) {
      break;
    }
    print();
  }
  
  try {
    String line = reader.readLine();
    while (line != null) {
      for (char ch : line.toCharArray()) {
        arduino.write(ch);
      }
      println();
      arduino.clear();
      arduino.write('\n');
      int i = 0;
      char ch;
      while (arduino.available() < 1)
        print("");
      while (i < 3) {
        if (arduino.available() == 0)
          continue;

        ch = arduino.readChar();
        if ((ch == 'O') || (ch == 'K') || (ch == '\n')) {
          i++;
        }
        print(ch);
      }
      arduino.clear();
      line = reader.readLine();
    }
  }
  catch(Exception e) {
  };
}

void draw() {
}
