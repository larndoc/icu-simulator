const int ledPin = 13;
const uint8_t ledPin1 = 10; 
const uint8_t ledPin2 = 7;
const uint8_t ledPin3 = 4; 

void display_recieved_output(){
 for (int i = 0; i < response_packet_counter[1]; i++){
  Serial.println(fee_packet1[i]); 
 }
}
void sync(){
  
    digitalWrite(12, toggled); 
    digitalWrite(10, toggled); 
    //digitalWrite(ledPin2, toggled);
}

void async_clear(){
    digitalWrite(12,  LOW); 
    digitalWrite(10, LOW);
   // digitalWrite(ledPin2, false); 
}

void async_set(){
    digitalWrite(12, HIGH); 
    digitalWrite(10, HIGH); 
    //digitalWrite(ledPin2, true); 
}

void initialize_pins(){
  pinMode(12, OUTPUT); 
  pinMode(13, OUTPUT);
  pinMode(ledPin1, OUTPUT); 
  pinMode(ledPin2, OUTPUT); 
}
