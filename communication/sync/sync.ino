const uint8_t ledPin = 13;
const uint8_t ledPin1 = 10; 
const uint8_t ledPin2 = 7;
void sync(){
    digitalWrite(ledPin, toggled); 
    digitalWrite(ledPin1, toggled); 
    digitalWrite(ledPin2, toggled);
}

void async_clear(){
    digitalWrite(ledPin, false); 
    digitalWrite(ledPin1, false);
    digitalWrite(ledPin2, false); 
}

void async_set(){
    digitalWrite(ledPin, true); 
    digitalWrite(ledPin1, true); 
    digitalWrite(ledPin2, false); 
}
