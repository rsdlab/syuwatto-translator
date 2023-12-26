/*
 *  WebCamera.ino - Web Camera via GS2200
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

#include <TelitWiFi.h>
#include "config.h"
#include "hiragana_mapping.h"

#include <Camera.h>
#include <SDHCI.h>
#include <time.h>
#include <SPI.h>
#include <Adafruit_ILI9341.h>
#include <Adafruit_GFX.h>
#include <Audio.h>


/****************************************************************************
 * Initial parameters
 ****************************************************************************/
// #define DEBUG
#define BMP

// #define USE_HDR_CAMERA
#define CONSOLE_BAUDRATE          115200
#define TOTAL_PICTURE_COUNT       9999
#ifdef BMP
  #define GET_AUDIO_FILENAME        "input/audio/get_audio.mp3"
  #define RECEIVE_AUDIO_FILENAME    "output/audio/receive_audio.mp3"
#endif
#ifndef BMP
  #define GET_AUDIO_FILENAME        "get_audio.mp3"
  #define RECEIVE_AUDIO_FILENAME    "receive_audio.mp3"
#endif

#define SCREEN_PORTRAIT_NORMAL    0
#define SCREEN_LANDSCAPE_NOMAL    1
#define SCREEN_PORTRAIT_REVERSE   2
#define SCREEN_LANDSCAPE_REVERSE  3
#define SCREEN_ROTATION           SCREEN_LANDSCAPE_REVERSE
#define TFT_DC                    9
#define TFT_CS                    10
#define TFT_RESET                 8
#define SD_CARD_CS                3
#define BMP_FILE_TYPE             0x0000
#define BMP_FILE_SIZE             0x0002
#define BMP_RESERVE1              0x0006
#define BMP_RESERVE2              0x0008
#define BMP_OFFSET                0x000A
#define BMP_HEADDER_SIZE          0x000E
#define BMP_WIDTH                 0x0012
#define BMP_HEIGHT                0x0016
#define BMP_PLANES                0x001A
#define BMP_BIT_COUNT             0x001C
#define BMP_COMPRESSION           0x001E
#define BMP_SIZE_IMAGE            0x0022
#define BMP_X_PIX_PER_M           0x0026
#define BMP_Y_PIX_PER_M           0x002A
#define BMP_N_OF_PALETTE          0X002E
#define BMP_CIR_IMPORTANT         0x0032


TelitWiFi     gs2200;
TWIFI_Params  gsparams;
SDClass       img_theSD;
SDClass       audio_theSD;
AudioClass    *theAudio;
File          img_myFile;
File          audio_myFile;


int g_width                 = CAM_IMGSIZE_VGA_H;
int g_height                = CAM_IMGSIZE_VGA_V;
int g_divisor               = 7;
int lcd_buttonState4        = 1;
int lcd_buttonState5        = 1;
int lcd_buttonState6        = 1;
int lcd_buttonState7        = 1;
int img_initialized_flag    = 0;
int audio_initialized_flag  = 0;
int time_interval_img       = 1500;


CAM_IMAGE_PIX_FMT    g_img_fmt   = CAM_IMAGE_PIX_FMT_JPG;
CAM_WHITE_BALANCE    g_wb        = CAM_WHITE_BALANCE_AUTO;
CAM_HDR_MODE         g_hdr       = CAM_HDR_MODE_ON;
Adafruit_ILI9341     tft         = Adafruit_ILI9341(&SPI, TFT_DC, TFT_CS, TFT_RESET); //ILI9341液晶ディスプレイのクラス定義
String               SwitchValue = "None";


const uint16_t       PACKET_SIZE                       = 1024;
const uint16_t       CHUNK_SIZE                        = 256;
const int            lcd_buttonPin4                    = 4;
const int            lcd_buttonPin5                    = 5;
const int            lcd_buttonPin6                    = 6;
const int            lcd_buttonPin7                    = 7;
const int            LED_Pin                           = 14;
const int            MAX_HIRAGANA                      = 100;
const int            BMP_MODE_SELECT_1                 = 0;
const int            BMP_MODE_SELECT_2                 = 2;
const int            BMP_CHANGE_INTERVAL_1             = 3;
const int            BMP_CHANGE_INTERVAL_2             = 4;
const int            BMP_CHANGE_INTERVAL_3             = 5;
const int            BMP_GET_IMG                       = 6;
const int            BMP_GET_AUDIO                     = 7;
const int            BMP_FINISH_IMG                    = 8;
const int            BMP_FINISH_AUDIO                  = 9;
const int            BMP_FINISH_TRANSLATE              = 10;
const int            BMP_SHOW_PROBLEM                  = 11;
const int            BMP_take_picture                  = 12;
const int            BMP_FINISH_PICTURE                = 13;
const int            BMP_FINISH_ALL                    = 14;
const int            BMP_GET_ERROR                     = 15;
const int            BMP_INIT_DISPLAY                  = 16;
uint8_t              CHECK_RESPONSE_OK[]               = "OK";
uint8_t              CHECK_RESPONSE_NG[]               = "NG";
uint8_t              Send_Data[PACKET_SIZE]            = {0};
uint8_t              output_text[300]                  = "";
uint8_t              problem_text[300]                 = "";
static const int32_t max_recoding_time                 = 10; /* Recording time[second] */
static const int32_t recoding_bitrate                  = 96000; /* Recording bit rate. Set in bps. Note: 96kbps fixed */
static const int32_t recoding_byte_per_second          = (recoding_bitrate / 8); /* Bytes per second */
static const int32_t recoding_size                     = recoding_byte_per_second * max_recoding_time; /* Total recording size */

bool                 ErrEnd                            = false;


void display_bmp(const char *filename, int flag);
void display_rgb565(const char *filename);
void display(int input_num);

bool areArraysEqual(uint8_t arr1[], uint8_t arr2[], size_t size);

int get_img();
int take_picture();
void get_audio();
void send_mode(char *mode_data, char *server_cid);
void send_text(char *send_data, char *server_cid);
void receive_text(char *Request_text, char *server_cid, size_t max_size);
void receive_problem(char *Request_text, char *server_cid, size_t max_size);
void send_img(int count, char *server_cid);
void send_audio(char *filename, char *server_cid);
void receive_audio(char *server_cid);
void output_img(uint8_t *input);
void output_audio();
void init_button();
void set_init();


/****************************************************************************
 * Print error message
 ****************************************************************************/
void printError(enum CamErr err) {
  Serial.print("Error: ");
  switch (err) {
  case CAM_ERR_NO_DEVICE:             Serial.println("No Device");                     break;
  case CAM_ERR_ILLEGAL_DEVERR:        Serial.println("Illegal device error");          break;
  case CAM_ERR_ALREADY_INITIALIZED:   Serial.println("Already initialized");           break;
  case CAM_ERR_NOT_INITIALIZED:       Serial.println("Not initialized");               break;
  case CAM_ERR_NOT_STILL_INITIALIZED: Serial.println("Still picture not initialized"); break;
  case CAM_ERR_CANT_CREATE_THREAD:    Serial.println("Failed to create thread");       break;
  case CAM_ERR_INVALID_PARAM:         Serial.println("Invalid parameter");             break;
  case CAM_ERR_NO_MEMORY:             Serial.println("No memory");                     break;
  case CAM_ERR_USR_INUSED:            Serial.println("Buffer already in use");         break;
  case CAM_ERR_NOT_PERMITTED:         Serial.println("Operation not permitted");       break;
  default:
    break;
  }

  #ifdef BMP
    display(BMP_GET_ERROR);
  #endif
  exit(1);

}

/****************************************************************************
 * Function definition
 ****************************************************************************/
void display_bmp(const char *filename , int flag){
  File ReadFile;
  ReadFile = img_theSD.open(filename, FILE_READ);
  if(!ReadFile){
    Serial.println("File cannot open!!!");
    #ifdef BMP
      display(BMP_GET_ERROR);
    #endif
    while(true);
  }

  //uint32_t file_size = ReadFile.size();
  uint8_t headder[54];
  for(uint8_t i=0; i<54; i++){
    headder[i]= ReadFile.read();
  }

  uint32_t data_offset      = *((uint32_t *)(headder+BMP_OFFSET));
  uint32_t data_width       = *((uint32_t *)(headder+BMP_WIDTH));
  uint32_t data_height      = *((uint32_t *)(headder+BMP_HEIGHT));
  uint16_t data_bit_count   = *((uint32_t *)(headder+BMP_BIT_COUNT));
  uint32_t data_compression = *((uint32_t *)(headder+BMP_COMPRESSION));
  if((data_offset != 54) || (data_bit_count != 24) || (data_compression != 0)){
    Serial.println("File format is not suppoted.");
    #ifdef BMP
      display(BMP_GET_ERROR);
    #endif
    while(true);
  }
  uint32_t display_width = data_width <320 ? data_width : 320;
  uint32_t display_height = data_height<240 ? data_height : 240;

  int num_line = 2;
  for (int32_t y = display_height - 1; y >= 0; y -= num_line) {
    ReadFile.seek(54 + data_width * 3 * y);
    uint16_t line_data[320 * num_line];
    for (int32_t i = 0; i < num_line; i++) {
      for (int32_t x = 0; x < display_width; x++) {
        uint8_t blue = ReadFile.read();
        uint8_t green = ReadFile.read();
        uint8_t red = ReadFile.read();
        // Adjust the index to store data for each line
        line_data[i * display_width + x] = tft.color565(red, green, blue);
      }
    }

    // Adjust the coordinates for drawing multiple lines
    tft.drawRGBBitmap(0, display_height - (y + num_line - 1) - 1, line_data, display_width, num_line);
  }

  ReadFile.close();

  sleep(0.3);

  if (flag == 1) {
    num_line = 10;
    for (int32_t y = display_height - 1; y >= 0; y -= num_line) {
      uint16_t line_data[320 * num_line];
      for (int32_t i = 0; i < num_line; i++) {
        for (int32_t x = 0; x < display_width; x++) {
          uint8_t blue = 255;
          uint8_t green = 255;
          uint8_t red = 255;
          // Adjust the index to store data for each line
          line_data[i * display_width + x] = tft.color565(red, green, blue);
        }
      }

      // Adjust the coordinates for drawing multiple lines
      tft.drawRGBBitmap(0, display_height - (y + num_line - 1) - 1, line_data, display_width, num_line);
    }
  }
}


/**
 * @brief Audio attention callback
 *
 * When audio internal error occurs, this function will be called back.
 */
static void audio_attention_cb(const ErrorAttentionParam *atprm) {
  puts("Attention!");

  if (atprm->error_code >= AS_ATTENTION_CODE_WARNING) {
    ErrEnd = true;
  }
}


bool areArraysEqual(uint8_t arr1[], uint8_t arr2[], size_t size) {
  for (size_t i = 0; i < size; ++i) {
    if (arr1[i] != arr2[i]) {
      return false;
    }
  }
  return true;
}


int get_img() {
  int take_picture_count = 0;
  int take_picture_count_old = 0;
  int cam_flag = 0;
  unsigned long cam_before, cam_after, required_time, sleep_time;
  // カメラのセットアップが終了していなければセットアップを行う
  if (img_initialized_flag == 0) {
    Serial.println("Setup Camera...");
    CamErr err = theCamera.begin();
    if (err != CAM_ERR_SUCCESS) {
      printError(err);
      #ifdef BMP
        display(BMP_GET_ERROR);
      #endif
      return -1;
    }

    // HDRカメラを使用するときの設定
    #ifdef USE_HDR_CAMERA
      err = theCamera.setHDR(g_hdr);
      if (err != CAM_ERR_SUCCESS) {
        printError(err);
        #ifdef BMP
          display(BMP_GET_ERROR);
        #endif
        return -1;
      }
    #endif

    err = theCamera.setAutoWhiteBalanceMode(g_wb);
    if (err != CAM_ERR_SUCCESS) {
      printError(err);
      #ifdef BMP
        display(BMP_GET_ERROR);
      #endif
      return -1;
    }
    err = theCamera.setStillPictureImageFormat(g_width, g_height, g_img_fmt, g_divisor);if (err != CAM_ERR_SUCCESS) {
      printError(err);
      #ifdef BMP
        display(BMP_GET_ERROR);
      #endif
      return -1;
    }
    
    char filename[16] = {0};
    #ifdef BMP
      sprintf(filename, "input/img/IMG_%04d.jpg", take_picture_count_old);
    #endif
    #ifndef BMP
      sprintf(filename, "IMG_%04d.jpg", take_picture_count_old);
    #endif

    while (img_theSD.exists(filename)) {
      Serial.print("A old picture (");
      Serial.print(filename);
      Serial.println(") was removed.");
      img_theSD.remove(filename);
      take_picture_count_old++;
      #ifdef BMP
        sprintf(filename, "input/img/IMG_%04d.jpg", take_picture_count_old);
      #endif
      #ifndef BMP
        sprintf(filename, "IMG_%04d.jpg", take_picture_count_old);
      #endif
    }

    Serial.println("Setup Camera done.");
    img_initialized_flag = 1;
  }

  while (cam_flag == 0) {
    cam_before = millis(); // 撮影時間の計測開始

    #ifdef DEBUG
      digitalWrite(LED3, HIGH); // LEDを点灯させて画像をとることを知らせる
      CamImage img = theCamera.takePicture(); // 画像撮影
      digitalWrite(LED3, LOW); // 撮影が終了したらLEDを消灯させる
    #endif

    #ifndef DEBUG
      digitalWrite(LED_Pin, HIGH); // LEDを点灯させて画像をとることを知らせる
      CamImage img = theCamera.takePicture(); // 画像撮影
      digitalWrite(LED_Pin, LOW); // 撮影が終了したらLEDを消灯させる
    #endif

    // 画像の保存処理
    if (img.isAvailable()) {
      /* Create file name */
      char filename[16] = {0};
      #ifdef BMP
        sprintf(filename, "input/img/IMG_%04d.jpg", take_picture_count);
      #endif
      #ifndef BMP
        sprintf(filename, "IMG_%04d.jpg", take_picture_count);
      #endif

      // 同じ名前の画像があれば削除
      if (img_theSD.exists(filename)) {
        Serial.print("A old picture (");
        Serial.print(filename);
        Serial.println(") was removed.");
        img_theSD.remove(filename);
      }

      // 取得した画像を保存
      Serial.print("Save taken picture as ");
      Serial.println(filename);
      File img_myFile = img_theSD.open(filename, FILE_WRITE);
      if (img_myFile) {
        img_myFile.write(img.getImgBuff(), img.getImgSize());
        img_myFile.close();
        take_picture_count++;
      }
      else {
        Serial.println("Failed to open file for writing");
      }

      cam_after = millis(); // 撮影時間の計測終了
      required_time = cam_after - cam_before;
      ConsolePrintf( "Take Cam:%dms\n", required_time ); // 撮影時間の表示

      /* 撮影間隔の調整 */
      if (required_time < time_interval_img) {
        sleep_time = time_interval_img - required_time;
        delay(sleep_time);
      }
    }

    // 画像の撮影に失敗した時の処理
    else {
      Serial.println("Failed to take picture");
    }

    // 撮影を終了するかの判断
    lcd_buttonState7 = digitalRead(lcd_buttonPin7);

    // 7番ボタンが押されている場合
    if(lcd_buttonState7 == 0) {
      cam_flag = 1;
      theCamera.end();
      img_initialized_flag = 0;
    }
  }

  return take_picture_count;
}


int take_picture() {
  int take_picture_count = 0;
  int take_picture_count_old = 0;
  int cam_flag = 0;
  // カメラのセットアップが終了していなければセットアップを行う
  if (img_initialized_flag == 0) {
    Serial.println("Setup Camera...");
    CamErr err = theCamera.begin();
    if (err != CAM_ERR_SUCCESS) {
      printError(err);
      #ifdef BMP
        display(BMP_GET_ERROR);
      #endif
      return -1;
    }

    // HDRカメラを使用するときの設定
    #ifdef USE_HDR_CAMERA
      err = theCamera.setHDR(g_hdr);
      if (err != CAM_ERR_SUCCESS) {
        printError(err);
        #ifdef BMP
          display(BMP_GET_ERROR);
        #endif
        return -1;
      }
    #endif

    err = theCamera.setAutoWhiteBalanceMode(g_wb);
    if (err != CAM_ERR_SUCCESS) {
      printError(err);
      #ifdef BMP
        display(BMP_GET_ERROR);
      #endif
      return -1;
    }
    err = theCamera.setStillPictureImageFormat(g_width, g_height, g_img_fmt, g_divisor);if (err != CAM_ERR_SUCCESS) {
      printError(err);
      #ifdef BMP
        display(BMP_GET_ERROR);
      #endif
      return -1;
    }
    
    char filename[16] = {0};
    #ifdef BMP
      sprintf(filename, "input/img/IMG_%04d.jpg", take_picture_count_old);
    #endif
    #ifndef BMP
      sprintf(filename, "IMG_%04d.jpg", take_picture_count_old);
    #endif

    while (img_theSD.exists(filename)) {
      Serial.print("A old picture (");
      Serial.print(filename);
      Serial.println(") was removed.");
      img_theSD.remove(filename);
      take_picture_count_old++;
      #ifdef BMP
        sprintf(filename, "input/img/IMG_%04d.jpg", take_picture_count_old);
      #endif
      #ifndef BMP
        sprintf(filename, "IMG_%04d.jpg", take_picture_count_old);
      #endif
    }

    Serial.println("Setup Camera done.");
    img_initialized_flag = 1;
  }

  while (cam_flag == 0) {

    // 撮影タイミングの判断
    while (lcd_buttonState4 == 1) {
      lcd_buttonState4 = digitalRead(lcd_buttonPin4);
    }

    if (lcd_buttonState4 == 0) {
      lcd_buttonState4 = 0;
      #ifdef DEBUG
        digitalWrite(LED3, HIGH); // LEDを点灯させて画像をとることを知らせる
        CamImage img = theCamera.takePicture(); // 画像撮影
        digitalWrite(LED3, LOW); // 撮影が終了したらLEDを消灯させる
      #endif

      #ifndef DEBUG
        digitalWrite(LED_Pin, HIGH); // LEDを点灯させて画像をとることを知らせる
        CamImage img = theCamera.takePicture(); // 画像撮影
        digitalWrite(LED_Pin, LOW); // 撮影が終了したらLEDを消灯させる
      #endif

      // 画像の保存処理
      if (img.isAvailable()) {
        /* Create file name */
        char filename[16] = {0};
        #ifdef BMP
          sprintf(filename, "input/img/IMG_%04d.jpg", take_picture_count);
        #endif
        #ifndef BMP
          sprintf(filename, "IMG_%04d.jpg", take_picture_count);
        #endif

        // 同じ名前の画像があれば削除
        if (img_theSD.exists(filename)) {
          Serial.print("A old picture (");
          Serial.print(filename);
          Serial.println(") was removed.");
          img_theSD.remove(filename);
        }

        // 取得した画像を保存
        Serial.print("Save taken picture as ");
        Serial.println(filename);
        File img_myFile = img_theSD.open(filename, FILE_WRITE);
        if (img_myFile) {
          img_myFile.write(img.getImgBuff(), img.getImgSize());
          img_myFile.close();
          take_picture_count++;
        }
        else {
          Serial.println("Failed to open file for writing");
        }
      }

      // 画像の撮影に失敗した時の処理
      else {
        Serial.println("Failed to take picture");
      }
    }

    // 撮影を終了するかの判断
    lcd_buttonState7 = digitalRead(lcd_buttonPin7);

    // 7番ボタンが押されている場合
    if(lcd_buttonState7 == 0) {
      cam_flag = 1;
      theCamera.end();
      img_initialized_flag = 0;
    }
  }

  return take_picture_count;
}


void get_audio() {
  int loop_flag = 0;
  int button_flag = 0;
  // マイクのセットアップが終了していなければセットアップを行う
  if (audio_initialized_flag == 0) {
    theAudio = AudioClass::getInstance();

    theAudio->begin(audio_attention_cb);

    puts("initialization Audio Library");

    /* Select input device as microphone */
    theAudio->setRecorderMode(AS_SETRECDR_STS_INPUTDEVICE_MIC);

    /*
    * Initialize filetype to stereo mp3 with 48 Kb/s sampling rate
    * Search for MP3 codec in "/mnt/sd0/BIN" directory
    */
    theAudio->initRecorder(AS_CODECTYPE_MP3, "/mnt/sd0/BIN", AS_SAMPLINGRATE_48000, AS_CHANNEL_STEREO);
    puts("Init Recorder!");

    /* Open file for data write on SD card */

    if (audio_theSD.exists(GET_AUDIO_FILENAME)) {
      printf("Remove existing file %s.\n", GET_AUDIO_FILENAME);
      audio_theSD.remove(GET_AUDIO_FILENAME);
    }

    audio_myFile = audio_theSD.open(GET_AUDIO_FILENAME, FILE_WRITE);
    /* Verify file open */
    if (!audio_myFile) {
      printf("File open error\n");
      #ifdef BMP
        display(BMP_GET_ERROR);
      #endif
      exit(1);
    }

    printf("Open! %s\n", GET_AUDIO_FILENAME);

    theAudio->startRecorder();
    #ifdef DEBUG
      digitalWrite(LED3, HIGH); // LEDを点灯させて録音することを知らせる
    #endif

    #ifndef DEBUG
      digitalWrite(LED_Pin, HIGH); // LEDを点灯させて録音することを知らせる
    #endif
    
    puts("Recording Start!");
    audio_initialized_flag = 1;
  }

  // loop_flagが立つまで実行
  while (loop_flag == 0) {
    err_t err;

    // 撮影を終了するかの判断
    lcd_buttonState7 = digitalRead(lcd_buttonPin7);

    // 7番ボタンが押されている場合
    if(lcd_buttonState7 == 0) {
      button_flag = 1;
    }

    if (theAudio->getRecordingSize() > recoding_size || button_flag == 1) {
      theAudio->stopRecorder();
      
      #ifdef DEBUG
        digitalWrite(LED3, LOW); // 録音が終了したらLEDを消灯させる
      #endif

      #ifndef DEBUG
        digitalWrite(LED_Pin, LOW); // 録音が終了したらLEDを消灯させる
      #endif

      sleep(1);
      err = theAudio->readFrames(audio_myFile);

      goto exitRecording;
    }

    /* Read frames to record in file */
    err = theAudio->readFrames(audio_myFile);

    if (err != AUDIOLIB_ECODE_OK) {
      printf("File End! =%d\n", err);
      theAudio->stopRecorder();
      
      #ifdef DEBUG
        digitalWrite(LED3, LOW); // 録音が終了したらLEDを消灯させる
      #endif

      #ifndef DEBUG
        digitalWrite(LED_Pin, LOW); // 録音が終了したらLEDを消灯させる
      #endif

      goto exitRecording;
    }

    if (ErrEnd) {
      printf("Error End\n");
      theAudio->stopRecorder();
      
      #ifdef DEBUG
        digitalWrite(LED3, LOW); // 録音が終了したらLEDを消灯させる
      #endif

      #ifndef DEBUG
        digitalWrite(LED_Pin, LOW); // 録音が終了したらLEDを消灯させる
      #endif

      goto exitRecording;
    }

    /* This sleep is adjusted by the time to write the audio stream file.
    * Please adjust in according with the processing contents
    * being processed at the same time by Application.
    *
    * The usleep() function suspends execution of the calling thread for usec
    * microseconds. But the timer resolution depends on the OS system tick time
    * which is 10 milliseconds (10,000 microseconds) by default. Therefore,
    * it will sleep for a longer time than the time requested here.
    */

    // usleep(10000);

    continue;

    exitRecording:

      theAudio->closeOutputFile(audio_myFile);
      audio_myFile.close();

      theAudio->setReadyMode();
      theAudio->end();

      puts("End Recording");
      loop_flag = 1;
      audio_initialized_flag = 0;
      button_flag = 0;
  }
}


void send_mode(char *mode_data, char *server_cid) {
	int receive_size = 0;
  int flag = 0;
  uint8_t TCP_Receive_mode_state[PACKET_SIZE] = "";
  
	while (flag == 0) {
    ConsoleLog("Send mode data");
    // Prepare for the next chunck of incoming data
    WiFi_InitESCBuffer();

    // Start the infinite loop to send the data
    while (flag == 0) {
      while (!gs2200.write(server_cid, mode_data, strlen((const char*)mode_data))) {
        // Data is not sent, we need to re-send the data
        delay(100);
      }

      delay(100);

      if (gs2200.available()) {
        receive_size = gs2200.read(server_cid, TCP_Receive_mode_state, PACKET_SIZE);
        if (0 < receive_size) {
          // ConsolePrintf("Receive %d byte:%s \r\n", receive_size, TCP_Receive_mode_state);
          if (areArraysEqual(TCP_Receive_mode_state, CHECK_RESPONSE_OK, sizeof(CHECK_RESPONSE_OK) - 1)) {
            Serial.println("モードをサーバに送信しました。");
            memset(TCP_Receive_mode_state, 0, PACKET_SIZE);
            flag = 1;
            WiFi_InitESCBuffer();
            delay(100);
          }
          else {
            Serial.println("サーバにモードを送信できませんでした。");
            memset(TCP_Receive_mode_state, 0, PACKET_SIZE);
            flag = 0;
            WiFi_InitESCBuffer();
          }
        }
      }
    }
  }
}


void send_text(char *send_data, char *server_cid) {
	int receive_size = 0;
  int flag = 0;
  uint8_t TCP_Receive_text_state[PACKET_SIZE] = "";
  
	while (flag == 0) {
    ConsoleLog("Send text data");
    // Prepare for the next chunck of incoming data
    WiFi_InitESCBuffer();

    // Start the infinite loop to send the data
    while (flag == 0) {
      if (!gs2200.write(server_cid, send_data, strlen((const char*)send_data))) {
        // Data is not sent, we need to re-send the data
        delay(100);
      }
    
      if (gs2200.available()) {
        receive_size = gs2200.read(server_cid, TCP_Receive_text_state, PACKET_SIZE);
        if (0 < receive_size) {
          // ConsolePrintf("Receive %d byte:%s \r\n", receive_size, TCP_Receive_text_state);
          if (areArraysEqual(TCP_Receive_text_state, CHECK_RESPONSE_OK, sizeof(CHECK_RESPONSE_OK) - 1)) {
            Serial.println("サーバがテキストを受信したことを確認しました。");
            flag = 1;
            memset(TCP_Receive_text_state, 0, PACKET_SIZE);
            WiFi_InitESCBuffer();
            delay(100);
          }
          else {
            Serial.println("サーバがテキストを受信できませんでした。");
            memset(TCP_Receive_text_state, 0, PACKET_SIZE);
            WiFi_InitESCBuffer();
          }
        }
      }
    }
  }
}


void receive_text(char *Request_text, char *server_cid, size_t max_size) {
	int receive_size = 0;
  int send_flag = 0;
  int flag = 0;
  
  while (flag == 0) {
    ConsoleLog("Receive text data");
    WiFi_InitESCBuffer();

    while (send_flag == 0) {
      if (!gs2200.write(server_cid, Request_text, strlen((const char*)Request_text))) {
        // Data is not sent, we need to re-send the data
        delay(100);
      }
      else {
        send_flag = 1;
      }
    }

    delay(100);

    while (flag == 0) {
      if (gs2200.available()) {
        receive_size = gs2200.read(server_cid, output_text, PACKET_SIZE);
        if (0 < receive_size) {
          if (!areArraysEqual(output_text, CHECK_RESPONSE_OK, sizeof(CHECK_RESPONSE_OK) - 1) && !areArraysEqual(output_text, CHECK_RESPONSE_NG, sizeof(CHECK_RESPONSE_NG) - 1)) {
            Serial.println("テキストを送信してくることを確認しました。");
            // ConsolePrintf("Receive %d byte:%s \r\n", receive_size, output_text);
            // memset(output_text, 0, PACKET_SIZE);
            flag = 1;
            WiFi_InitESCBuffer();
            delay(100);
          }
          else {
            Serial.println("OKまたはNGのフラグを受信しました。再度データを受信します。");
            memset(output_text, 0, PACKET_SIZE);
            send_flag = 0;
            WiFi_InitESCBuffer();
            break;
          }
        }
      }
    }
  }
}


void receive_problem(char *Request_text, char *server_cid, size_t max_size) {
  int receive_size = 0;
  int send_flag = 0;
  int flag = 0;
  int retry_count = 0;
  const int MAX_RETRY_COUNT = 5;
  
  while (flag == 0 && retry_count < MAX_RETRY_COUNT) {
    ConsoleLog("Receive problem data");
    WiFi_InitESCBuffer();

    // 送信が完了するまでループ
    while (send_flag == 0 && retry_count < MAX_RETRY_COUNT) {
      if (!gs2200.write(server_cid, Request_text, strlen((const char*)Request_text))) {
        // Data is not sent, re-send the data
        delay(100);
        retry_count++;
      }
      else {
        send_flag = 1;
      }
    }

    if (retry_count >= MAX_RETRY_COUNT) {
      ConsoleLog("Failed to send request text!");
      break;
    }

    delay(100);
    retry_count = 0;  // リトライ回数のリセット

    while (flag == 0 && retry_count < MAX_RETRY_COUNT) {
      if (gs2200.available()) {
        receive_size = gs2200.read(server_cid, problem_text, max_size - 1);

        if (receive_size > 0) {
          // Null終端文字を追加
          problem_text[receive_size] = '\0';

          if (!areArraysEqual(problem_text, CHECK_RESPONSE_OK, sizeof(CHECK_RESPONSE_OK) - 1) &&
              !areArraysEqual(problem_text, CHECK_RESPONSE_NG, sizeof(CHECK_RESPONSE_NG) - 1)) {
            Serial.println("練習機能で使用する問題であることを確認しました。");
            // ConsolePrintf("Receive %d byte: %s \r\n", receive_size, problem_text);
            flag = 1;
            WiFi_InitESCBuffer();
            delay(100);
          } else {
            Serial.println("OKまたはNGのフラグを受信しました。再度データを受信します。");
            send_flag = 0;
            retry_count++;
            delay(100);
            break;
          }
        }
      }
    }
  }

  // リトライ回数制限を超えた場合のエラーメッセージ
  if (retry_count >= MAX_RETRY_COUNT) {
    ConsoleLog("Failed to receive response text!");
  }
}


void send_img(int count, char *server_cid) {
  int index = 0;

  uint8_t state_data[] = "5";
  send_mode(state_data, server_cid);

  delay(300);

  while (count > index) {
    WiFi_InitESCBuffer();

    // 画像データを送信
    ConsoleLog("Send image data");
    char filename[16] = {0};
    #ifdef BMP
      sprintf(filename, "input/img/IMG_%04d.jpg", index);
    #endif
    #ifndef BMP
      sprintf(filename, "IMG_%04d.jpg", index);
    #endif
    img_myFile = img_theSD.open(filename, FILE_READ);
    if (!img_myFile || img_myFile.size() == 0) {
      ConsoleLog("Failed to open or empty image file!");
      // エラーハンドリングとしてプログラムを終了
      break; // あるいは適切なエラーハンドリング
    }

    int retry_count = 0;
    const int MAX_RETRY_COUNT = 5;
    size_t bytesRead;

    while (img_myFile.available()) {
      WiFi_InitESCBuffer();
      bytesRead = img_myFile.read(Send_Data, sizeof(Send_Data));

      while (bytesRead > 0 && retry_count < MAX_RETRY_COUNT) {
        if (gs2200.write(server_cid, Send_Data, bytesRead)) {
          break;  // 書き込み成功
        }

        ConsolePrintf("Send Bulk Error, retry...\n");
        delay(100);
        retry_count++;
      }

      if (retry_count >= MAX_RETRY_COUNT) {
        // エラーハンドリングとしてプログラムを終了
        ConsoleLog("Failed to send image data!");
        break;
      }

      retry_count = 0;

      // 画像データの一部が送信されるごとに少し待機する
      delay(100);
    }

    // 画像データ送信完了を示すデリミタを送信
    gs2200.write(server_cid, "\r\n\r\n", 4);

    img_myFile.close();
    Serial.print("No.");
    Serial.print(index);
    Serial.println(" is sent.");
    delay(100);
    index++;
  }

  // 送信完了を示すデリミタを送信
  gs2200.write(server_cid, "\r\n\r\n\r\n", 6);
  WiFi_InitESCBuffer();
  delay(100);
}



void send_audio(char *filename, char *server_cid) {
  int receive_size = 0;
  uint8_t mp3Buffer[CHUNK_SIZE];
  uint8_t Receive_Data[PACKET_SIZE] = {0};
  int retry_count = 0;
  const int MAX_RETRY_COUNT = 3;
  size_t bytesRead;

  uint8_t state_data[] = "5";
  send_mode(state_data, server_cid);

  ConsoleLog("MP3データの送信を開始します");

  // MP3ファイルを読み込むためにファイルを開く
  File audio_myFile = audio_theSD.open(filename);
  if (!audio_myFile) {
    ConsoleLog("MP3ファイルのオープンに失敗しました");
    #ifdef BMP
      display(BMP_GET_ERROR);
    #endif
    while (1);
  }

  while (audio_myFile.available()) {
    bytesRead = audio_myFile.read(mp3Buffer, sizeof(mp3Buffer));

    if (bytesRead > 0) {
      while (!gs2200.write(server_cid, mp3Buffer, bytesRead) && (retry_count < MAX_RETRY_COUNT)) {
        // Data is not sent, we need to re-send the data
        Serial.println("Retry...");
        // memset(mp3Buffer, 0, sizeof(mp3Buffer));
        delay(10);
        retry_count++;
      }
      if (retry_count == MAX_RETRY_COUNT) {
        Serial.println("Max retries reached!");
      }
      memset(mp3Buffer, 0, sizeof(mp3Buffer));
      retry_count = 0;

      // if (!gs2200.write(server_cid, mp3Buffer, bytesRead)) {
      //   // データが送信されなかった場合、エラー処理または再試行を行います
      //   delay(10);
      // }

      // while (gs2200.available()) {
      //   receive_size = gs2200.read(server_cid, Receive_Data, PACKET_SIZE);
      //   if (receive_size > 0) {
      //     ConsolePrintf("Receive %d byte:%s \r\n", receive_size, Receive_Data);
      //     memset(Receive_Data, 0, PACKET_SIZE);
      //   }
      // }
      
      delay(100);
    }
  }

  // MP3ファイルを閉じる
  audio_myFile.close();
  gs2200.write(server_cid, "\r\n\r\n\r\n", 6);
  WiFi_InitESCBuffer();
  delay(100);
  Serial.println("Sent audio!");
}


void receive_audio(char *server_cid) {
  int receive_size = 0;
  int flag = 0;
  uint8_t TCP_Receive_audio[PACKET_SIZE] = "";
  uint8_t Request_mp3[] = "request_mp3";
  
  uint8_t state_data[] = "5";
  send_mode(state_data, server_cid);

  // ファイルがすでに存在していたら削除
  if (audio_theSD.exists(RECEIVE_AUDIO_FILENAME)) {
    audio_theSD.remove(RECEIVE_AUDIO_FILENAME);
    printf("Existing file %s was removed", RECEIVE_AUDIO_FILENAME);
  }
  
  audio_myFile = audio_theSD.open(RECEIVE_AUDIO_FILENAME, FILE_WRITE);
  if (!audio_myFile) {
    ConsoleLog("Error opening MP3 file");
    #ifdef BMP
      display(BMP_GET_ERROR);
    #endif
    while (1);
  }

  while (flag == 0) {
    ConsoleLog("Receive audio data");
    // Prepare for the next chunck of incoming data
    WiFi_InitESCBuffer();

    // Start the infinite loop to send the data
    if (!gs2200.write(server_cid, Request_mp3, strlen((const char*)Request_mp3))) {
      // Data is not sent, we need to re-send the data
      delay(100);
    }

    delay(100);

    while (flag == 0) {
      WiFi_InitESCBuffer();
      receive_size = gs2200.read(server_cid, TCP_Receive_audio, PACKET_SIZE);
      if (receive_size > 0) {

        // MP3データをSDカードに書き込む
        audio_myFile.write(TCP_Receive_audio, receive_size);
        // memset(TCP_Receive_audio, 0, PACKET_SIZE);
      }
      else {
        flag = 1;
      }
    }
  }
  audio_myFile.close();  // Close the MP3 file
  Serial.println("mp3_recieved.");
  // gs2200.write(server_cid, "\r\n\r\n\r\n", 6);
  WiFi_InitESCBuffer();
  delay(100);
}


void display(int input_num) {
  tft.fillScreen(ILI9341_BLACK);
  clock_t start_time = clock();
  char bmp_filename[16] = {0};
  #ifdef BMP
    sprintf(bmp_filename, "bmp/%03d.bmp", input_num);
  #endif

  #ifndef BMP
    sprintf(bmp_filename, "%03d.bmp", input_num);
  #endif
  display_bmp(bmp_filename, 0);
  
  clock_t end_time = clock();
  
  String resultValue = String("Display completed");
}


void output_img(uint8_t *input) {
  char numbers[MAX_HIRAGANA][3];
  int length = strlen(input);
  int count = 0;

  for (int i = 0; i < length; i += 3) {
    char hiragana[4];
    strncpy(hiragana, &input[i], 3);
    hiragana[3] = '\0';
    int number = getHiraganaNumber(hiragana);
    if (number != NOT_FOUND) {
      snprintf(numbers[count], 3, "%02d", number);
      ++count;
    }
  }

  tft.fillScreen(ILI9341_BLACK);
  clock_t start_time = clock();
  for (int i = 0; i < count; ++i) {
    char bmp_filename[16] = {0};
    #ifdef BMP
      sprintf(bmp_filename, "bmp/%s.bmp", numbers[i]);
    #endif
    #ifndef BMP
      sprintf(bmp_filename, "%s.bmp", numbers[i]);
    #endif
    display_bmp(bmp_filename, 1);
  }
  clock_t end_time = clock();
  
  String resultValue = String("Display completed");
}


void output_audio() {
  int result_loop_flag = 0;

  theAudio = AudioClass::getInstance();

  theAudio->begin(audio_attention_cb);

  puts("initialization Audio Library");

  /* Set clock mode to normal */
  theAudio->setRenderingClockMode(AS_CLKMODE_NORMAL);

  /* Set output device to speaker with first argument.
   * If you want to change the output device to I2S,
   * specify "AS_SETPLAYER_OUTPUTDEVICE_I2SOUTPUT" as an argument.
   * Set speaker driver mode to LineOut with second argument.
   * If you want to change the speaker driver mode to other,
   * specify "AS_SP_DRV_MODE_1DRIVER" or "AS_SP_DRV_MODE_2DRIVER" or "AS_SP_DRV_MODE_4DRIVER"
   * as an argument.
   */
  theAudio->setPlayerMode(AS_SETPLAYER_OUTPUTDEVICE_SPHP, AS_SP_DRV_MODE_LINEOUT);

  /*
   * Set main player to decode stereo mp3. Stream sample rate is set to "auto detect"
   * Search for MP3 decoder in "/mnt/sd0/BIN" directory
   */
  err_t err = theAudio->initPlayer(AudioClass::Player0, AS_CODECTYPE_MP3, "/mnt/sd0/BIN", AS_SAMPLINGRATE_AUTO, AS_CHANNEL_STEREO);

  /* Verify player initialize */
  if (err != AUDIOLIB_ECODE_OK) {
    printf("Player0 initialize error\n");
    #ifdef BMP
      display(BMP_GET_ERROR);
    #endif
    exit(1);
  }

  audio_myFile = audio_theSD.open(RECEIVE_AUDIO_FILENAME);

  /* Verify file open */
  if (!audio_myFile) {
    printf("File open error\n");
    #ifdef BMP
      display(BMP_GET_ERROR);
    #endif
    exit(1);
  }
  printf("Open! 0x%08lx\n", (uint32_t)audio_myFile);

  /* Send first frames to be decoded */
  err = theAudio->writeFrames(AudioClass::Player0, audio_myFile);

  if ((err != AUDIOLIB_ECODE_OK) && (err != AUDIOLIB_ECODE_FILEEND)) {
    printf("File Read Error! = %d\n", err);
    audio_myFile.close();
    #ifdef BMP
      display(BMP_GET_ERROR);
    #endif
    exit(1);
  }

  puts("Play!");

  /* Main volume set to -16.0 dB */
  theAudio->setVolume(-160);
  theAudio->startPlayer(AudioClass::Player0);

  while (result_loop_flag == 0) {
    puts("loop!!");

    /* Send new frames to decode in a loop until file ends */
    int err = theAudio->writeFrames(AudioClass::Player0, audio_myFile);

    /*  Tell when player file ends */
    if (err == AUDIOLIB_ECODE_FILEEND) {
      printf("Main player File End!\n");
    }

    /* Show error code from player and stop */
    if (err || ErrEnd) {
      printf("Main player error code: %d\n", err);
      result_loop_flag = 1;
      break;
    }

    /* This sleep is adjusted by the time to read the audio stream file.
     * Please adjust in according with the processing contents
     * being processed at the same time by Application.
     *
     * The usleep() function suspends execution of the calling thread for usec
     * microseconds. But the timer resolution depends on the OS system tick time
     * which is 10 milliseconds (10,000 microseconds) by default. Therefore,
     * it will sleep for a longer time than the time requested here.
     */
    usleep(40000);
  }

  // 共通処理
  stop_player:
    theAudio->stopPlayer(AudioClass::Player0);
    audio_myFile.close();
    theAudio->setReadyMode();
    theAudio->end();
}


void init_button() {
  lcd_buttonState4 = 1;
  lcd_buttonState5 = 1;
  lcd_buttonState6 = 1;
  lcd_buttonState7 = 1;
}


void read_button() {
  lcd_buttonState4 = digitalRead(lcd_buttonPin4);
  lcd_buttonState5 = digitalRead(lcd_buttonPin5);
  lcd_buttonState6 = digitalRead(lcd_buttonPin6);
  lcd_buttonState7 = digitalRead(lcd_buttonPin7);
}

void set_init() {
  SwitchValue = "None";
  init_button();
  Serial.println("fin");
  #ifdef BMP
    display(BMP_FINISH_ALL);
  #endif
}

/****************************************************************************
 * setup
 ****************************************************************************/
void setup() {
  int take_picture_count_old = 0;
  /* initialize digital pin of LEDs as an output. */
  pinMode(LED0, OUTPUT);
  pinMode(LED1, OUTPUT);
  pinMode(LED2, OUTPUT);
  pinMode(LED3, OUTPUT);
  
  pinMode(lcd_buttonPin4, INPUT);
  pinMode(lcd_buttonPin5, INPUT);
  pinMode(lcd_buttonPin6, INPUT);
  pinMode(lcd_buttonPin7, INPUT);

  pinMode(LED_Pin, OUTPUT);

  pinMode(TFT_RESET, OUTPUT);
  digitalWrite(TFT_RESET, HIGH);
  
  ledOn(LED0);
  Serial.begin( CONSOLE_BAUDRATE );
  while (!Serial)
    {
      ; /* wait for serial port to connect. Needed for native USB port only */
    }

  //液晶ディスプレイの設定
  tft.begin();
  tft.setRotation(SCREEN_ROTATION);
  
  /* Initialize SD */
  while (!audio_theSD.begin()) {
    /* wait until SD card is mounted. */
    Serial.println("Insert SD card.");
  }

  /* Initialize SD */
  while (!img_theSD.begin()) 
    {
      /* wait until SD card is mounted. */
      Serial.println("Insert SD card.");
    }
  
  char filename[16] = {0};
  #ifdef BMP
    sprintf(filename, "input/img/IMG_%04d.jpg", take_picture_count_old);
  #endif
  #ifndef BMP
    sprintf(filename, "IMG_%04d.jpg", take_picture_count_old);
  #endif

  /* Remove the old file with the same file name as new created file,
  * and create new file.
  */
  while (img_theSD.exists(filename)) {
    Serial.print("A old picture (");
    Serial.print(filename);
    Serial.println(") was removed.");
    img_theSD.remove(filename);
    take_picture_count_old++;
    #ifdef BMP
      sprintf(filename, "input/img/IMG_%04d.jpg", take_picture_count_old);
    #endif
    #ifndef BMP
      sprintf(filename, "IMG_%04d.jpg", take_picture_count_old);
    #endif
  }

  /* Initialize SPI access of GS2200 */
  Init_GS2200_SPI_type(iS110B_TypeC);

  // Initialize AT Command Library Buffer
  gsparams.mode = ATCMD_MODE_STATION; //ステーションモード
  gsparams.psave = ATCMD_PSAVE_DEFAULT;
  if( gs2200.begin( gsparams ) ){
    ConsoleLog( "GS2200 Initilization Fails" );
    #ifdef BMP
      display(BMP_GET_ERROR);
    #endif
    while(1);
  }

  // GS2200 runs as ST（ステーションモード）
  if( gs2200.activate_station( AP_SSID, PASSPHRASE ) ){
    ConsoleLog( "Association Fails" );
    #ifdef BMP
      display(BMP_GET_ERROR);
    #endif
    while(1);
  }

  ledOn(LED0);
  #ifdef BMP
    display(BMP_INIT_DISPLAY);
  #endif
}

/****************************************************************************
 * main loop
 ****************************************************************************/
void loop() {
  int img_num = 0;
  char server_cid = 0;
  bool served = false;
  
  unsigned long time1,  time2,  time3,  time4,  time5,  time6,  time7,  time8;

  while (1) {
    // TCPクライアントとしてサーバに接続？
    if (!served) {
        // ConsoleLog("Start TCP Client");
        server_cid = gs2200.connect(TCPSRVR_IP, TCPSRVR_PORT);
        ConsolePrintf("server_cid: %d \r\n", server_cid);
        while (server_cid == ATCMD_INVALID_CID) {
          Serial.println("Retry TCP Client");
          server_cid = gs2200.connect(TCPSRVR_IP, TCPSRVR_PORT);
          ConsolePrintf("server_cid: %d \r\n", server_cid);
          // ConsolePrintf("ATCMD_INVALID_CID: %d \r\n", ATCMD_INVALID_CID);
        }
        served = true;
    }
    while (served){
      // モード選択（条件は要確認）
      while (SwitchValue == "None") {
        // 7番（終了判定）ボタンの状態を取得
        lcd_buttonState7 = digitalRead(lcd_buttonPin7);

        // 7番ボタンが押されていない場合
        if(lcd_buttonState7 == 1) {
          #ifdef BMP
            display(BMP_MODE_SELECT_1);
          #endif
          // どれかが押されるまで4~7番のボタンの状態を取得し続ける
          while(lcd_buttonState4 == 1 && lcd_buttonState5 == 1 && lcd_buttonState6 == 1) {
            read_button();
          }
          // 4番（指文字翻訳機能）ボタンが押された場合
          if (lcd_buttonState4 == 0) {
            SwitchValue = "img_translate";
          }
          // 5番（音声翻訳機能）ボタンが押された場合
          else if (lcd_buttonState5 == 0) {
            SwitchValue = "audio_translate";
          }
          // 6番（次へ）ボタンが押された場合
          else if (lcd_buttonState6 == 0) {
            // ボタンの状態をリセット
            init_button();
            #ifdef BMP
              display(BMP_MODE_SELECT_2);
            #endif
            // どれかが押されるまで4~7番のボタンの状態を取得し続ける
            while(lcd_buttonState4 == 1 && lcd_buttonState5 == 1 && lcd_buttonState6 == 1) {
              read_button();
            }
            // 4番（練習機能）ボタンが押された場合
            if (lcd_buttonState4 == 0) {
              // ボタンの状態をリセット
              init_button();
              SwitchValue = "practice";
            }
            // 5番（撮影間隔変更）ボタンが押された場合
            else if (lcd_buttonState5 == 0) {
              // ボタンの状態をリセット
              init_button();
              SwitchValue = "change_interval";
            }
            // 6番（戻る）ボタンが押された場合
            else if (lcd_buttonState6 == 0) {
              // ボタンの状態をリセット
              init_button();
              SwitchValue = "None";
              break;
            }
          }
        }

        // 7番ボタンが押されている場合
        else {
          SwitchValue = "None";

          // すべてのボタンの状態を押されていない状態に戻す
          init_button();
        }
      }

      // 指文字翻訳機能
      if (SwitchValue == "img_translate") {
        /*************************************************************************************************
        * この機能で実装すること
        * ・画像の取得→カメラのセットアップ/LEDの点滅/SDへの保存/スイッチ割り込みによる終了
        * ・画像を送信
        * ・翻訳結果を受信
        * ・表示→ディスプレイ出力/音声出力
        *************************************************************************************************/
        uint8_t mode_data[] = "1";
        send_mode(mode_data, server_cid);

        time1 = millis();

        #ifdef BMP
          display(BMP_GET_IMG);
        #endif
        img_num = get_img();
        #ifdef BMP
          display(BMP_FINISH_IMG);
        #endif

        time2 = millis();
        Serial.print("撮影時間 : ");
        Serial.print(time2 - time1);
        Serial.println("[ms]");
        time3 = millis();

        send_img(img_num, server_cid);

        time4 = millis();
        Serial.print("転送時間 : ");
        Serial.print(time4 - time3);
        Serial.println("[ms]");
        time5 = millis();

        uint8_t Request_text[] = "request_text";
        receive_text(Request_text, server_cid, PACKET_SIZE);
        
        #ifdef DEBUG
          ConsolePrintf("Receive : %s \r\n", output_text);
        # endif
        
        receive_audio(server_cid);
        #ifdef BMP
          display(BMP_FINISH_TRANSLATE);
        #endif

        time6 = millis();
        Serial.print("受信時間 : ");
        Serial.print(time6 - time5);
        Serial.println("[ms]");
        time7 = millis();

        output_img(output_text);
        output_audio();

        time8 = millis();
        Serial.print("出力時間 : ");
        Serial.print(time8 - time7);
        Serial.println("[ms]");
        Serial.print("合計 : ");
        Serial.print(time8 - time1);
        Serial.println("[ms]");
        set_init();
      }

      // 音声翻訳機能
      else if (SwitchValue == "audio_translate") {
        /*************************************************************************************************
        * この機能で実装すること
        * ・音声の取得→マイクのセットアップ/SDへの保存/スイッチ割り込みによる終了
        * ・音声ファイルを送信
        * ・翻訳結果を受信
        * ・表示→ディスプレイ出力
        *************************************************************************************************/
        uint8_t mode_data[] = "2";
        send_mode(mode_data, server_cid);

        time1 = millis();
        
        #ifdef BMP
          display(BMP_GET_AUDIO);
        #endif
        get_audio();
        #ifdef BMP
          display(BMP_FINISH_AUDIO);
        #endif

        time2 = millis();
        Serial.print("撮影時間 : ");
        Serial.print(time2 - time1);
        Serial.println("[ms]");
        time3 = millis();

        send_audio(GET_AUDIO_FILENAME, server_cid);

        time4 = millis();
        Serial.print("転送時間 : ");
        Serial.print(time4 - time3);
        Serial.println("[ms]");
        time5 = millis();

        // delay(2000);
        uint8_t Request_text[] = "request_text";
        receive_text(Request_text, server_cid, PACKET_SIZE);
        
        #ifdef DEBUG
          ConsolePrintf("Receive : %s \r\n", output_text);
        # endif

        #ifdef BMP
          display(BMP_FINISH_TRANSLATE);
        #endif

        time6 = millis();
        Serial.print("受信時間 : ");
        Serial.print(time6 - time5);
        Serial.println("[ms]");
        time7 = millis();

        output_img(output_text);

        time8 = millis();
        Serial.print("出力時間 : ");
        Serial.print(time8 - time7);
        Serial.println("[ms]");
        Serial.print("合計 : ");
        Serial.print(time8 - time1);
        Serial.println("[ms]");

        // #ifdef DEBUG
        //   output_audio();
        // # endif

        set_init();
      }

      // 指文字練習機能
      else if (SwitchValue == "practice") {
        /*************************************************************************************************
        * この機能で実装すること
        * ・問題の表示
        * ・画像の取得→カメラのセットアップ/LEDの点滅/SDへの保存/スイッチ割り込みによる終了
        * ・画像を送信
        * ・翻訳結果を受信
        * ・表示→ディスプレイ出力/音声出力？
        *************************************************************************************************/
        uint8_t mode_data[] = "3";
        send_mode(mode_data, server_cid);

        uint8_t Request_text[] = "request_text";
  
        uint8_t state_data[] = "5";
        send_mode(state_data, server_cid);

        receive_problem(Request_text, server_cid, PACKET_SIZE);
        
        #ifdef DEBUG
          ConsolePrintf("Receive : %s \r\n", problem_text);
        # endif
        
        #ifdef BMP
          display(BMP_SHOW_PROBLEM);
        #endif
        output_img(problem_text);
        #ifdef BMP
          display(BMP_GET_IMG);
        #endif
        img_num = get_img();
        #ifdef BMP
          display(BMP_FINISH_IMG);
        #endif
        send_img(img_num, server_cid);
        receive_text(Request_text, server_cid, PACKET_SIZE);
        
        #ifdef DEBUG
          ConsolePrintf("Receive : %s \r\n", problem_text);
        # endif

        receive_audio(server_cid);
        #ifdef BMP
          display(BMP_FINISH_TRANSLATE);
        #endif
        output_img(output_text);
        output_audio();
        set_init();
      }

      // 写真撮影機能
      else if (SwitchValue == "teke_picture") {
        /*************************************************************************************************
        * この機能で実装すること
        * ・画像の取得
        * ・画像を送信
        *************************************************************************************************/
        uint8_t mode_data[] = "4";
        send_mode(mode_data, server_cid);
        #ifdef BMP
          display(BMP_GET_IMG);
        #endif
        img_num = take_picture();
        #ifdef BMP
          display(BMP_FINISH_IMG);
        #endif
        send_img(img_num, server_cid);
        set_init();
      }

      // 撮影間隔変更
      else if (SwitchValue == "change_interval") {
        /*************************************************************************************************
        * この機能で実装すること
        * ・撮影間隔(time_interval_img)の変更
        *************************************************************************************************/
        int flag1 = 0;
        int flag2 = 0;
        int delta_time_interval = 0;
        int pre_time_interval = 0;
        unsigned long time_before, time_after, required_time, sleep_time;

        #ifdef BMP
          display(BMP_CHANGE_INTERVAL_1);
        #endif

        while (flag1 == 0) {
          time_before = millis();
          #ifdef DEBUG
            digitalWrite(LED3, HIGH); // LEDを点灯
            delay(10);
            digitalWrite(LED3, LOW); // LEDを消灯
          #endif

          #ifndef DEBUG
            digitalWrite(LED_Pin, HIGH); // LEDを点灯
            delay(10);
            digitalWrite(LED_Pin, LOW); // LEDを消灯
          #endif

          time_after = millis();
          required_time = time_after - time_before;
          sleep_time = time_interval_img - required_time;
          while (sleep_time > 100) {
            read_button();

            if (lcd_buttonState4 == 0) {
              if (time_interval_img + delta_time_interval > 600) {
                delta_time_interval -= 100;
              }

              // ボタンの状態をリセット
              init_button();
            }

            else if (lcd_buttonState5 == 0) {
              delta_time_interval += 100; 

              // ボタンの状態をリセット
              init_button();
            }

            else if (lcd_buttonState6 == 0) {
              flag1 = 1;

              // ボタンの状態をリセット
              init_button();
            }

            else if (lcd_buttonState7 == 0) {
              flag1 = 1;
              flag2 = 1;
              
              set_init();
              break;
            }

            time_after = millis();
            required_time = time_after - time_before;
            sleep_time = time_interval_img - required_time;
          }
          if (flag2 == 0) {
            delay(sleep_time);
          }
        }

        if (flag2 == 0) {
          pre_time_interval = time_interval_img + delta_time_interval;

          #ifdef BMP
            display(BMP_CHANGE_INTERVAL_2);
          #endif
          
          while(lcd_buttonState4 == 1 && lcd_buttonState5 == 1) {
            time_before = millis();
            #ifdef DEBUG
              digitalWrite(LED3, HIGH); // LEDを点灯
              delay(10);
              digitalWrite(LED3, LOW); // LEDを消灯
            #endif

            #ifndef DEBUG
              digitalWrite(LED_Pin, HIGH); // LEDを点灯
              delay(10);
              digitalWrite(LED_Pin, LOW); // LEDを消灯
            #endif
            
            time_after = millis();
            required_time = time_after - time_before;
            sleep_time = pre_time_interval - required_time;
            while (sleep_time > 100) {
              read_button();

              if (lcd_buttonState4 == 0) {
                time_interval_img = pre_time_interval;
                flag2 = 1;
                break;
              }

              else if (lcd_buttonState5 == 0) {
                flag1 = 0;
                flag2 = 0;
                break;
              }

              time_after = millis();
              required_time = time_after - time_before;
              sleep_time = pre_time_interval - required_time;
            }

            if (lcd_buttonState4 == 1 && lcd_buttonState5 == 1) {
              delay(sleep_time);
            }
          }
          
          if (flag2 == 1) {
            // ボタンの状態をリセット
            SwitchValue = "None";
            init_button();
            Serial.println("fin");
            #ifdef BMP
              display(BMP_CHANGE_INTERVAL_2);
            #endif
          }
        }
      }
    }
  }
}