void setup()
{
  Serial.begin(115200);
  // use external voltage ref
  //analogReference(EXTERNAL);
}

void readVals()
{
  //unsigned long start, finished, elapsed;
  int readings = 160; // a bit over 2 cycles @ 74 samples each
  int a0[readings];
  int a1[readings];
  
  //start=millis();
  // 2x 160 readings takes ~ 36ms or 0.225ms/reading
  // 1sec/60hz =~ 16.6666ms/cycle
  // 16.6666ms/0.225ms =~ 74.074 readings/cycle
  // could only read a0 and a1 and double read rate
  for(int i = 0; i<readings; i++)
  {
  
    a0[i]=analogRead(0);// current 1 (hi res amp)
    a1[i]=analogRead(1);// voltage 1

  }        
  //finished=millis();
  //elapsed=finished-start;
  //Serial.print(elapsed);
  //Serial.println(" milliseconds elapsed");
  
  for(int i = 0; i<readings; i++)
  {
     Serial.print(a0[i]);
     Serial.print(",");
     Serial.print(a1[i]);
     Serial.print(";");
  }
  Serial.println("");
}

void loop()
{
  delay(250);
  readVals();
}
