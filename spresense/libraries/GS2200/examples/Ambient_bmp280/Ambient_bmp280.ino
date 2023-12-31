/*
 *  Ambient_bmp280.ino - Sample Program for Ambient with BMP280
 *  Copyright 2020 Spresense Users
 *
 *  This work is free software; you can redistribute it and/or modify it under the terms 
 *  of the GNU Lesser General Public License as published by the Free Software Foundation; 
 *  either version 2.1 of the License, or (at your option) any later version.
 *
 *  This work is distributed in the hope that it will be useful, but without any warranty; 
 *  without even the implied warranty of merchantability or fitness for a particular 
 *  purpose. See the GNU Lesser General Public License for more details.
 *
 *  You should have received a copy of the GNU Lesser General Public License along with 
 *  this work; if not, write to the Free Software Foundation, 
 *  Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
 */


#include <GS2200Hal.h>
#include <GS2200AtCmd.h>
#include <AmbientGs2200.h>
#include <TelitWiFi.h>

#include "config.h"

#include <Adafruit_BMP280.h>

TelitWiFi gs2200;
TWIFI_Params gsparams = {ATCMD_MODE_STATION, ATCMD_PSAVE_DEFAULT};

AmbientGs2200 theAmbientGs2200(&gs2200);

Adafruit_BMP280 bmp; // I2C

void setup()
{

  Serial.begin(115200);

  pinMode(LED0, OUTPUT);
  pinMode(LED1, OUTPUT);
  pinMode(LED2, OUTPUT);
  pinMode(LED3, OUTPUT);
  digitalWrite( LED0, HIGH );

  /* WiFi Module Initialize */
  Init_GS2200_SPI_type(iS110B_TypeC);

  if( gs2200.begin( gsparams ) ){
    Serial.println( "GS2200 Initilization Fails" );
    while(1);
  }

  /* GS2200 Association to AP */
  if( gs2200.activate_station( AP_SSID, PASSPHRASE ) ){
    Serial.println( "Association Fails" );
    while(1);
  }

  digitalWrite( LED0, LOW );
  digitalWrite( LED1, HIGH );

  Serial.println(F("GS2200 Initialized"));

  theAmbientGs2200.begin(channelId, writeKey);

  Serial.println(F("Ambient Initialized"));

  if (!bmp.begin()) {  
    Serial.println(F("Could not find a valid BMP280 sensor, check wiring!"));
    exit(1);
  }

  Serial.println(F("BMP280 Initialized"));

}

void loop()
{
  Serial.print(F("Temperature = "));
  Serial.print(bmp.readTemperature());
  Serial.println(" *C");

  Serial.print(F("Pressure = "));
  Serial.print(bmp.readPressure());
  Serial.println(" Pa");

  Serial.print(F("Approx altitude = "));
  Serial.print(bmp.readAltitude(1013.25)); // this should be adjusted to your local forcase
  Serial.println(" m");

  Serial.println();

  // Send to Ambient
  theAmbientGs2200.set(1, (String(bmp.readTemperature())).c_str());
  theAmbientGs2200.set(2, (String(bmp.readPressure())).c_str());

  int ret = theAmbientGs2200.send();

  if (ret == 0) {
    Serial.println("*** ERROR! RESET Wifi! ***\n");
    exit(1);
  }else{
    Serial.println("*** Send comleted! ***\n");
    usleep(300000);
  }

  sleep(10); // Once every 10 seconds.

}
