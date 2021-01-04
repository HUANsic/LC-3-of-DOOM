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

#define MAX_WRITE_CYCLE_TIME 5

class CAT {
  public:
    void init() {
      DDRL = 0xFF;
      DDRA = 0xFF;
      DDRC = 0xFF;
      DDRF = 0x00;
      DDRK = 0x00;
      PORTF = 0x00;
      PORTK = 0x00;
      setChipEnable(0);
      setOutputEnable(0);
      setWriteEnable(0);
    }

    void write(uint16_t address, uint16_t data) {
      setAddress(address);
      setData(data);
      setWriteEnable(1);
      setOutputEnable(0);
      setChipEnable(1);
      delayMicroseconds(5);
      setWriteEnable(0);

      delay(MAX_WRITE_CYCLE_TIME);
      setChipEnable(0);
    }

    void write(uint16_t address, uint16_t* arr, uint8_t num) {
      setOutputEnable(0);
      setWriteEnable(0);
      setChipEnable(1);
      delayMicroseconds(10);

      for (int i = 0; i < num; i++) {
        setAddress(address + i);
        setData(arr[i]);
        setWriteEnable(1);
        delayMicroseconds(20);
        setWriteEnable(0);
        delayMicroseconds(20);
      }

      delay(MAX_WRITE_CYCLE_TIME);
      setChipEnable(0);
    }

    uint16_t read(uint16_t address) {
      uint16_t retInt;
      setAddress(address);
      setWriteEnable(0);
      setChipEnable(1);
      setOutputEnable(1);
      delayMicroseconds(10);
      retInt = PINF + (PINK << 8);
      setOutputEnable(0);
      setChipEnable(0);
      return retInt;
    }

  private:
    void setAddress(uint16_t address) {
      PORTA = (uint8_t)address;
      PORTC = (uint8_t)(address >> 8);
    }

    void setData(uint16_t data) {
      PORTF = (uint8_t)data;
      PORTK = (uint8_t)(data >> 8);
    }

    void setChipEnable(uint8_t CE) {
      if (CE) {
        PORTL &= ~((1 << CE0) | (1 << CE1));
      } else {
        PORTL |= (1 << CE0) | (1 << CE1);
      }
    }

    void setOutputEnable(uint8_t OE) {
      if (OE) {
        PORTL &= ~((1 << OE0) | (1 << OE1));
        DDRF = 0x00;
        DDRK = 0x00;
        PORTF = 0x00;
        PORTK = 0x00;
      } else {
        PORTL |= (1 << OE0) | (1 << OE1);
      }
    }

    void setWriteEnable(uint8_t WE) {
      if (WE) {
        PORTL &= ~((1 << WE0) | (1 << WE1));
        DDRF = 0xFF;
        DDRK = 0xFF;
      } else {
        PORTL |= (1 << WE0) | (1 << WE1);
        DDRF = 0x00;
        DDRK = 0x00;
      }
    }
};

CAT myCat;

uint16_t arr[128];

void setup() {
  Serial.begin(19200);
  while (!Serial);
  myCat.init();
  while (Serial.read() != -1);  // empty the buffer
}

void loop() {
  uint16_t address = 0x500, data[128], holder = 0, lastAddress;
  uint8_t ch, dta[4], count128 = 0, count4 = 0;
  
  myCat.write(0, 0);
  delay(100);
  Serial.print("OK\n");

  while (1) {
    ch = Serial.read();

    if (ch == -1)
      continue;
    if (((ch < 0x3A) && (ch > 0x2F))) {   // a hex number
      address = address << 4;
      address += ch - 0x30;     // update address (0 <= countDigit <= 3)
      lastAddress = address;
      continue;
    } else if ((ch > 0x40) && (ch < 0x47)) {   // a hex number
      address = address << 4;
      address += ch - 55;     // update address (0 <= countDigit <= 3)
      lastAddress = address;
      continue;
    }
    if (ch == '\n') {   // a new line character
      if (count4 != 0)
        Serial.println(count4);
      Serial.print("OK@");
      Serial.print(address, HEX);
      Serial.print('\n');
      count4 = 0;
      continue;
    }
    if (ch == '@') {    // .END character
      myCat.write(address, data, count128);
      count128 = 0;
      address = 0;
      lastAddress = 0;
      continue;
    }

    if ( (ch > 0x59) && (ch < 0x70)) {
      // a piece of encoded data
      dta[count4] = ch;
      count4++;
      if (count4 == 4) {
        count4 = 0;
        holder = (dta[3] & 0x0F);
        holder |= (dta[2] & 0x0F) << 4;
        holder |= (dta[1] & 0x0F) << 8;
        holder |= (dta[0] & 0x0F) << 12;
        data[count128] = holder;
        count128++;
        address++;
        Serial.print(count128);
        Serial.print(":");
        Serial.print(address, HEX);
        Serial.print("->");
        Serial.print(holder, BIN);
        Serial.print(" ");
      }
      if (address % 128 == 0 && count128 != 0) {
        myCat.write(lastAddress, data, count128);
        count128 = 0;
        lastAddress = address;
      }
    }
  }
}
