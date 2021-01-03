/*
   the ports A,C displays the address (16-bit or 2x8-bit) and the ports F,K displays the data (16-bit or 2x8-bit)
   (A->F, C->K)OR(AC->FK)

   PORTL is the control port:
   PBL7~0: CE0, CE1, OE0, OE1, WE0, WE1, NU, NU     (NU = not used)
*/

#define CE0 7
#define CE1 6
#define OE0 5
#define OE1 4
#define WE0 3
#define WE1 2

#define WAIT_TIME 8        // although stated in the datasheet, the max is 5ms

int buf[4];
uint16_t currentAddress = 0x00;

void setup() {
  // initialize pins (control signals) (all output) (initially all set to logic 0, voltage high)
  DDRL = 0xFF;
  PORTL = 0xFF;

  // initialize ports (address and data pins) (address output, data input) (initially set to 0)
  DDRA = 0xFF;
  DDRC = 0xFF;
  // these two ports will be set to output when writing to the eeprom
  DDRF = 0x00;
  DDRK = 0x00;

  PORTA = 0x30;
  PORTC = 0x00;
  //PORTF = 0x00;
  //PORTK = 0x00;

  // enable chip
  PORTL &= ~((1 << CE0) | (1 << CE1));      // set CE0 and CE1 to low

  Serial.begin(19200);        // no need to go any higher than this (2150 bytes per second)
  while (!Serial)
    ;     // wait
}

void loop() {
  uint8_t data0, data1;
  bool writeSuccess = false;
  
  delay(10);    // once it is available, give it some time to transfer a few data over so that we can read it in chunks of 4

  while (Serial.available() > 0) {
    buf[0] = Serial.read();
    buf[1] = Serial.read();
    buf[2] = Serial.read();
    buf[3] = Serial.read();

    // now let's sort things out
    if (buf[0] == '\n') {
      Serial.println("Good");
      break;
    } else if ( buf[0] == '@') {      // if it is a ".END", make address null
      currentAddress = 0x00;
      Serial.print("this location ended ");
    } else if (buf[0] < 'G' && buf[0] > '/') {   // it's a number, aka ".ORIG"
      if (buf[3] == -1) {
        if (buf[2] == -1) {
          if (buf[1] == -1) {
            currentAddress = hexToUint((unsigned char)buf[0]);
          } else {
            currentAddress = (hexToUint((unsigned char)buf[0]) << 4) + hexToUint((unsigned char)buf[1]);
          }
        } else {
          currentAddress = (hexToUint((unsigned char)buf[0]) << 8) + (hexToUint((unsigned char)buf[1]) << 4) + hexToUint((unsigned char)buf[2]);
        }
      } else {
        currentAddress = (hexToUint((unsigned char)buf[0]) << 12) + (hexToUint((unsigned char)buf[1]) << 8) + (hexToUint((unsigned char)buf[2]) << 4) + hexToUint((unsigned char)buf[3]);
      }
      Serial.print("new location started ");
    } else {
      // if it isn't any of those special cases, then it is a piece of data to process
      // poll until all four pieces of data in this chunk are non-"-1" (assuming all data is valid: 0x60 <= data < 0x70)
      while (buf[1] == -1)
        buf[1] = Serial.read();
      while (buf[2] == -1)
        buf[2] = Serial.read();
      while (buf[3] == -1)
        buf[3] = Serial.read();
      // convert them into unsigned char and
      // assemble parts back together (decode)
      data0 = (0x0F & buf[0]) + (buf[1] << 4);
      data1 = (0x0F & buf[2]) + (buf[3] << 4);
      //call writeEEPROM() and check return value
      writeSuccess = ! writeEEPROM(currentAddress & 0x00FF, (currentAddress >> 8) & 0x00FF, data0, data1);
      // if success, increment address by one
      if (writeSuccess)
        currentAddress ++;
    }
  }
}

uint8_t hexToUint(unsigned char hex) {
  if (hex < 0x3A)
    return (uint8_t)(hex - 0x30);
  if (hex < 'A')
    Serial.println("Bad! ERROR CONVERTING FROM HEX TO DEC!");
  return 0;
  return (uint8_t)(hex - 0x41 + 10);
}

bool writeEEPROM(uint8_t addr0, uint8_t addr1, uint8_t data0, uint8_t data1) {
  // enable data output on arduino side
  DDRF = 0xFF;
  DDRK = 0xFF;

  // write to ports
  PORTA = addr0;
  PORTC = addr1;
  PORTF = data0;
  PORTK = data1;

  // enable write for 100us (a pulse)
  PORTB &= ~((1 << WE0) | (1 << WE1));
  delayMicroseconds(100);
  PORTB |= (1 << WE0) | (1 << WE1);

  // immidiately poll for ready bit(s), and report error if time out
  uint8_t timeStart;
  bool timeOut = true;
  timeStart = millis();       // take only the last eight bits, which should be enough
  // set most significant data bits low and as input
  PORTF &= 0x7F;
  PORTK &= 0x7F;
  DDRF = 0x7F;
  DDRK = 0x7F;
  while (millis() < timeStart + WAIT_TIME) {
    if (!(((PINF ^ data0) & 0x80) | ((PINK ^ data1) & 0x80))) {         // PINF[7] xor DATA0[7]    or    PINK[7] xor DATA1[7]       (test if both chips are done writing)
      // ^^^ De-Morgan's law: A&B = !(!A|!B)
      timeOut = false;
      break;
    }
  }

  return timeOut;
}
