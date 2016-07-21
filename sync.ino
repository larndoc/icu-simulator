const int ledPin = 13;
const uint8_t ledPin1 = 12; 
const uint8_t ledPin2 = 11;
const uint8_t ledPin3 = 4; 

void display_recieved_output(){
 for (int i = 0; i < response_packet_counter[1]; i++){
  Serial.println(fee_packet1_ptr[i]); 
 }
}
void sync(){
  
    digitalWrite(12, toggled); 
    digitalWrite(10, toggled); 
    //digitalWrite(ledPin2, toggled);
}

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
