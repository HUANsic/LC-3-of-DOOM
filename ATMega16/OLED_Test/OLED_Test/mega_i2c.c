#ifndef F_CPU
#define F_CPU 16000000UL
#endif

#define MAX_TRIES 50
#define I2C_START 0
#define I2C_DATA  1
#define I2C_STOP  2

uint8_t twi_status = 0;
uint8_t slave_address = 0x3C;					// default slave address

// methods below for i2c are copied from http://www.ermicro.com/blog/?p=744 by rwb, and modified
uint8_t i2c_transmit(uint8_t type) {
	switch(type) {
		case I2C_START:    // Send Start Condition
		TWCR = (1 << TWINT) | (1 << TWSTA) | (1 << TWEN);
		break;
		case I2C_DATA:     // Send Data
		TWCR = (1 << TWINT) | (1 << TWEN);
		break;
		case I2C_STOP:     // Send Stop Condition
		TWCR = (1 << TWINT) | (1 << TWEN) | (1 << TWSTO);
		return 0;
	}
	// Wait for TWINT flag set in TWCR Register
	while (!(TWCR & (1 << TWINT)));
	// Return TWI Status Register, mask the prescaler bits (TWPS1,TWPS0)
	return (TWSR & 0xF8);
}

uint8_t i2c_start(){
	uint8_t n = 0;
	i2c_start_retry:
	if (n++ >= MAX_TRIES) return 23;
	
	// Transmit Start Condition
	twi_status = i2c_transmit(I2C_START);

	// Check the TWI Status
	if (twi_status == TW_MT_ARB_LOST) goto i2c_start_retry;
	if ((twi_status != TW_START) && (twi_status != TW_REP_START)) return 10;
	
	return 0;
}

uint8_t i2c_send(uint8_t input){
	uint8_t n = 0;
	i2c_send_retry:
	if (n++ >= MAX_TRIES) return 23;
	// Set data
	TWDR = input;
	// Transmit I2C Data
	twi_status=i2c_transmit(I2C_DATA);
	// Check the TWSR status
	if ((twi_status == TW_MT_SLA_NACK) || (twi_status == TW_MT_ARB_LOST)) goto i2c_send_retry;
	if (twi_status != TW_MT_SLA_ACK) return 10;
	return 0;
}

uint8_t i2c_stop(){
	uint8_t n = 0;
	i2c_stop_retry:
	if (n++ >= MAX_TRIES) return 23;
	
	// Transmit Start Condition
	twi_status = i2c_transmit(I2C_STOP);

	// Check the TWI Status
	if (twi_status == TW_MT_ARB_LOST) goto i2c_stop_retry;
	if ((twi_status != TW_START) && (twi_status != TW_REP_START)) return 10;
	
	return 0;
}

uint32_t i2c_init(uint8_t slaveAddress){
	// set the SCL frequency to 250kHz (Max 400kHz for SSD1306)
	return i2c_init(slaveAddress, 250000);
}

uint32_t i2c_init(uint8_t slaveAddress, uint32_t freq){
	slave_address = slaveAddress;
	// setting the SCL frequency to the closest possible value to freq
	uint16_t twbr = F_CPU / freq < 16 ? 0 : F_CPU / freq - 16;
	uint8_t twps = 0;
	twbr /= 2;
	// some protection
	while(twbr > 255){
		twbr /= 4;
		twps ++;
	}
	if(twps > 3){
		twps = 3;
		twbr = 255;
	}
	// write value to registers
	TWBR = twbr;
	TWSR |= twps;
	
	// return the actual SCL frequency
	return F_CPU / (16 + 2 * twbr * pow(4, twps));
}


// below are methods for SSD1306
// command without data
uint8_t ssd_sendCommand(uint8_t cmd){
	uint8_t feedback = 0;
	feedback += i2c_start();								// start i2c communication
	feedback += i2c_send((slave_address << 1) & 0xFE);		// set to write mode
	feedback += i2c_send(SSD1306_COMMAND_MODE);				// set to command mode
	feedback += i2c_send(cmd);								// send command
	feedback += i2c_stop();									// end communication
	return feedback;
}

// command with data
uint8_t ssd_sendCommand(uint8_t cmd, uint8_t* data, uint8_t count){
	if(count < 1)				// just in case someone thought it's funny to joke around
	return ssd_sendCommand(cmd);
	uint8_t feedback = 0;
	feedback += i2c_start();								// start i2c communication
	feedback += i2c_send((slave_address << 1) & 0xFE);		// set to write mode
	feedback += i2c_send(SSD1306_COMMAND_MODE);				// set to command mode
	feedback += i2c_send(cmd);								// send command
	int i;													// iterate through the array
	for(i = 0; i < count; i++){
		feedback += i2c_send(data[i]);
	}
	feedback += i2c_stop();									// end communication
	return feedback;
}

uint8_t ssd_sendCommand(uint8_t cmd, uint8_t data){
	return ssd_sendCommand(cmd, &data, 1);
}

// writes data to its GDDRAM (Graphic Display Data RAM)
uint8_t ssd_sendData(uint8_t* data, uint8_t count){
	uint8_t feedback = 0;
	feedback += i2c_start();								// start i2c communication
	feedback += i2c_send((slave_address << 1) & 0xFE);		// set to write mode
	feedback += i2c_send(SSD1306_DATA_MODE);				// set to data mode
	int i;
	for(i = 0; i < count; i++){
		feedback += i2c_send(data[i]);
	}
	feedback += i2c_stop();
	return feedback;
}

// not planning on using this, but just in case
uint8_t ssd_sendData(uint8_t data){
	return ssd_sendData(&data, 1);
}


// below are methods for console
// page addressing mode
uint8_t console_init(uint8_t slaveAddress){
	i2c_init(slaveAddress);						// call slave
	
	ssd_sendCommand(SSD1306_MEMORYMODE, 0x02);	// set page addressing mode
	ssd_sendCommand(SSD1306_SETDISPLAYOFFSET, 0x08);	// display offset = 8 (1st page at bottom)
	
}

// shift to next line on console
uint8_t console_NL(){
	ssd_sendCommand()
}