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
      DDRA = 0xFF;
      DDRC = 0xFF;
      DDRL = 0xFF;
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
        delayMicroseconds(10);
        setWriteEnable(0);
        delayMicroseconds(10);
      }

      delay(MAX_WRITE_CYCLE_TIME);
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
uint16_t zeros[128], count;

void setup() {
  Serial.begin(57600);
  while(!Serial);
  Serial.println("Serial good");
  myCat.init();
  for(int i = 0; i < 128; i++){
    zeros[i] = 0;
  }
  myCat.write(0, zeros, 128);
  for(uint16_t i = 128; i > 127; i += 128){
    myCat.write(i, zeros, 128);
  }

  Serial.println("Done!");
  Serial.end();
}

void loop() {
}
