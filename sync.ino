
void async_clear(){
    digitalWrite(*port[0],  LOW); 
    digitalWrite(*port[1], LOW);
    digitalWrite(*port[2], LOW); 
}

void async_set(){
    digitalWrite(*port[0], HIGH); 
    digitalWrite(*port[1], HIGH); 
    digitalWrite(*port[2], HIGH); 
}
