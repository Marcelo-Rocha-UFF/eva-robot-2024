/*
 * Software de controle para os servomotores do robô EVA (nova versão 2024)
 * Autor: Marcelo Marques da Rocha (Universidade Federal Fluminense)
 * Google Research / MidiaCom LAB
 */

#include "Arduino.h"
#include "AX12A.h"
#include <VarSpeedServo.h>


#define EVA_PAN_SERVO_ID    1 // horizontal
#define EVA_TILT_SERVO_ID   2 // vertical

#define WEBCAM_SERVO_TILT_PIN 8 // Porta Digital 8 PWM (Vertical)
#define WEBCAM_SERVO_PAN_PIN 9 // Porta Digital 9 PWM (Horizontal)

#define DirectionPin 	10u
#define BaudRate  		1000000ul

VarSpeedServo webcam_servo_tilt; // Webcam Tilt Servo
VarSpeedServo webcam_servo_pan; // Webcam Pan Servo

int eva_pan_value   = 512; // centro
int eva_tilt_value  = 512; // centro
int eva_velocity = 35; // velocidade de movimentacao da cabeça do EVA
int tilt_range = 25; // amplitude (1x) de um tilt (movimento da cabeça na vertical)
int pan_range = 40; // amplitude (1x) de um pan (movimento da cabeça na horizontal)

void setup()
{
	ax12a.begin(BaudRate, DirectionPin, &Serial);
  webcam_servo_tilt.attach(WEBCAM_SERVO_TILT_PIN); // vertical
  webcam_servo_pan.attach(WEBCAM_SERVO_PAN_PIN); // horizontal
  webcam_servo_tilt.write(90); // vertical 40 (up) < 90 > 120 (down) esses são os limites.
  webcam_servo_pan.write(90); // horizontal 55 (direita da cam) < 90 > 125 (parece ser o suficiente, mas pode ir mais para os dois lados)
}

void loop()
{
  if (Serial.available() > 0){
    char command = Serial.read();
    delay(20);

    // Comandos para controlar os movimentos da webcam (O protocolo usa dois caracteres: comando e posição)
    // Comandos t ou p. Posição variando de 60 à 120 (limitação imposta pela tabela ASCII)
    if (command == 't') { // tilt da webcam
      char angulo = Serial.read();
      delay(20);
      if (angulo >= 60 && angulo <= 120 )
        webcam_servo_tilt.write(angulo); // vertical
    }
    else if (command == 'p') { // pan da webcam
      char angulo = Serial.read();
      delay(20);
      if (angulo >= 60 && angulo <= 120 )
        webcam_servo_pan.write(angulo); // horizontal
    }

    // Comandos para o servomotor da cabeça do robô EVA
    // Compatível com o protocolo dos Mexicanos, utilizando apenas um caractere
    else if (command == 'c') { // centraliza a cabeça do robô
      eva_center();
    }
    else if (command == 'd') { // baixa a cabeça
      eva_down(1); // movimento com amplitude 1
    }
    else if (command == 'D') { // baixa a cabeça
      eva_down(2); // movimento com amplitude 2
    }
    else if (command == 'u') { // baixa a cabeça
      eva_up(1); // movimento com amplitude 1
    }
    else if (command == 'U') { // baixa a cabeça
      eva_up(2); // movimento com amplitude 2
    }
    else if (command == 'r') { // vira a cabeça a direita
      eva_right(1); // movimento com amplitude 1
    }
    else if (command == 'R') { // vira a cabeça a direita
      eva_right(2); // movimento com amplitude 2
    }
    else if (command == 'l') { // vira a cabeça a esquerda
      eva_left(1); // movimento com amplitude 1
    }
    else if (command == 'L') { // vira a cabeça a esqyerda
      eva_left(2); // movimento com amplitude 2
    }
    else if (command == 'e') { // vira a cabeça para cima e para a direita
      eva_up(1); // movimento com amplitude 1
      eva_right(1); // movimento com amplitude 1
    }
    else if (command == 'E') { // vira a cabeça para cima e para a direita
      eva_up(2); // movimento com amplitude 2
      eva_right(2); // movimento com amplitude 2
    }
    else if (command == 'q') { // vira a cabeça para cima e para a esquerda
      eva_up(1); // movimento com amplitude 1
      eva_left(1); // movimento com amplitude 1
    }
    else if (command == 'Q') { // vira a cabeça para cima e para a esquerda
      eva_up(2); // movimento com amplitude 2
      eva_left(2); // movimento com amplitude 2
    }
    else if (command == 'x') { // vira a cabeça para baixo e para a direita
      eva_down(1); // movimento com amplitude 1
      eva_right(1); // movimento com amplitude 1
    }
    else if (command == 'X') { // vira a cabeça para baixo e para a direita
      eva_down(2); // movimento com amplitude 2
      eva_right(2); // movimento com amplitude 2
    }
    else if (command == 'z') { // vira a cabeça para baixo e para a esquerda
      eva_down(1); // movimento com amplitude 1
      eva_left(1); // movimento com amplitude 1
    }
    else if (command == 'Z') { // vira a cabeça para baixo e para a esquerda
      eva_down(2); // movimento com amplitude 2
      eva_left(2); // movimento com amplitude 2
    }
    else if (command == 'n') { // acena com a cabeça (nod)
      eva_nod(2); // movimento com 2 repeticoes
    }
    else if (command == 'N') { // acena com a cabeça (nod)
      eva_nod(4); // movimento com 4 repeticoes
    }
    else if (command == 's') { // sacode a cabeça (shake) como se estivesse dizendo um não
      eva_shake(2); // movimento com 2 repeticoes
    }
    else if (command == 'S') { // acena com a cabeça (nod)
      eva_shake(4); // movimento com 4 repeticoes
    }

    // Protocolo com 3 caracteres utilizado para movimentar a cabeça utilizando um parametro de posição.
    // O caractere # sinaliza o protocolo de 3 chars. Em seguida vem o char que indica a função (up_down ou left_right) 
    // Então vem o char que indica a posição de destino do servomotor
    else if (command == '#') { // protocolo com 3 chars
      char tipo = Serial.read();
      delay(20);
      char posicao = Serial.read();
      if (tipo == 't'){
        eva_tilt(posicao); // Posição vertical
      }
      else if (tipo == 'p'){
        eva_pan(posicao); // Posição horizontal
      }
    }
  }
}


void eva_center (){ // centraliza a cabeça
  eva_pan_value = 512;
  eva_tilt_value = 512;
  ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity);
  delay(10);
  ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
}


void eva_down (int amplitude){ // baixa a cabeça
  eva_tilt_value = eva_tilt_value - (tilt_range * amplitude);
  ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity); 
}


void eva_up (int amplitude){ // ergue a cabeça
  eva_tilt_value = eva_tilt_value + (tilt_range * amplitude);
  ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity);
}


void eva_right (int amplitude){ // vira a cabeça para a direita
  eva_pan_value = eva_pan_value - (pan_range * amplitude);
  ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity); 
}


void eva_left (int amplitude){ // vira a cabeça para a direita
  eva_pan_value = eva_pan_value + (pan_range * amplitude);
  ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity); 
}


void eva_nod(int repeticoes){ // Acena com a cabeça, como se estivesse concordando
    int inc_velocity = -20;
    int pause = 900;
    while (repeticoes > 0){
      ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value + 40, eva_velocity + inc_velocity); // para cima
      delay(pause); // tempo para a cabeça chegar na posição desejada
      ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity + inc_velocity); // para a posicao inicial
      delay(pause); // tempo para a cabeça chegar na posição desejada
      repeticoes --;
  }
}


void eva_shake(int repeticoes){ // sacode a cabeça, como se estivesse dizendo um não
  int inc_velocity = 1;
  int pause = 500;
  while (repeticoes > 0){
    ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value + 40, eva_velocity + inc_velocity); // para esquerda
    delay(pause); // tempo para a cabeça chegar na posição desejada
    ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity + inc_velocity); // para a posicao inicial
    delay(pause); // tempo para a cabeça chegar na posição desejada
    ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value - 40, eva_velocity + inc_velocity); // para direita
    delay(pause); // tempo para a cabeça chegar na posição desejada
    ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity + inc_velocity); // para a posicao inicial
    delay(pause); // tempo para a cabeça chegar na posição desejada
    repeticoes --;
  }
}


// Funcões de movimento da cabeça com o parâmetro posição (Tilt [vertical] e Pan [horizontal])
void eva_tilt(int posicao_vertical){
  int eva_tilt_value = (90 + (90 - posicao_vertical)) * 5.75;
  ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity + 15);
}


void eva_pan(int posicao_horizontal){
  int eva_pan_value = posicao_horizontal * 5.68;
  ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity + 15);
}
