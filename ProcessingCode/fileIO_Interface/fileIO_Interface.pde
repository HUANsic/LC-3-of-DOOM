import processing.serial.*;

BufferedReader reader;
Serial arduino;

void setup() {
  arduino = new Serial(this, "COM3", 19200);
  reader = createReader("draft0-encoded.txt");
  try {
    String line = reader.readLine();
    while (line != null) {
      for (char ch : line.toCharArray()) {
        arduino.write(ch);
        println(ch);
      }
      arduino.clear();
      arduino.write('\n');
      int i = 0;
      char ch;
      while(arduino.available() < 1){
        print("=");
      }
      println("-");
      while (i < 3) {
        if(arduino.available() == 0)
          continue;
          
        ch = arduino.readChar();
        if (ch != 'O' || ch != 'K' || ch != '\n')
        print(ch);
        i++;
      }
      line = reader.readLine();
    }
  }
  catch(Exception e) {
  };
}

void draw() {
}
