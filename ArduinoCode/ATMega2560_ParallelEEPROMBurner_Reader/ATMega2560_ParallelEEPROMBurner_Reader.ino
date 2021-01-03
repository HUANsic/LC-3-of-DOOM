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
      setChipEnable(0);

      delay(MAX_WRITE_CYCLE_TIME);
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

uint16_t arr[128], count = 0;

void setup() {
  Serial.begin(19200);
  while (!Serial);
  myCat.init();
  PORTL &= ~((1 << CE0) | (1 << CE1) | (1 << OE0) | (1 << OE1));
}

void loop() {
  PORTA = (uint8_t)count;
  PORTC = (uint8_t)(count >> 8);
  delay(1);
  Serial.print(count, HEX);
  Serial.print("\t->\t");
  Serial.println(PINF + (PINK << 8), HEX);

  count++;
  if(!count){
    while(1);
  }
}
