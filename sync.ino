const uint8_t ledPin = 13;
const uint8_t ledPin1 = 12; 
const uint8_t ledPin2 = 11;


void async_clear(){
    digitalWrite(ledPin,  LOW); 
    digitalWrite(ledPin1, LOW);
    digitalWrite(ledPin2, LOW); 
}

void async_set(){
    digitalWrite(ledPin, HIGH); 
    digitalWrite(ledPin1, HIGH); 
    digitalWrite(ledPin2, HIGH); 
}

void initialize_pins(){
  pinMode(ledPin, OUTPUT);
  pinMode(ledPin1, OUTPUT); 
  pinMode(ledPin2, OUTPUT); 
}
