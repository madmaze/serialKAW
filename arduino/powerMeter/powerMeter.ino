void setup()
{
  Serial.begin(115200);
  // use external voltage ref
  //analogReference(EXTERNAL);
}

void readVals()
{
  //unsigned long start, finished, elapsed;
  int readings = 80;
  int a0[readings];
  int a1[readings];
  int a2[readings];
  int a3[readings];
  
  //start=millis();
  // 4x 80 readings takes ~ 36ms
  // could only read a0 and a1 and double read rate
  for(int i = 0; i<readings; i++)
  {
    a0[i]=analogRead(0);// current 1 (hi res amp)
    a1[i]=analogRead(1);// voltage 1
    a2[i]=analogRead(2);// current 2 needed? (low res amp?)
    a3[i]=analogRead(3);// current 3 needed?
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
     Serial.print(",");
     Serial.print(a2[i]);
     Serial.print(",");
     Serial.print(a3[i]);
     Serial.print(";");
  }
  Serial.println("");
}

void loop()
{
  delay(500);
  readVals();
}
