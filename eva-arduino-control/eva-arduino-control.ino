/*
 * Software de controle para os servomotores do robô EVA (nova versão 2024)
 * Autor: Marcelo Marques da Rocha (Universidade Federal Fluminense)
 * Agradecimentos ao Google Research e à CAPES
 */


#include "Arduino.h"
#include "AX12A.h"
#include <Servo.h>

#define ID_EVA_PAN    1 // horizontal
#define ID_EVA_TILT   2 // vertical

#define WEBCAM_SERVO_TILT 8 // Porta Digital 8 PWM (Vertical)
#define WEBCAM_SERVO_PAN 9 // Porta Digital 9 PWM (Horizontal)

#define DirectionPin 	10u
#define BaudRate  		1000000ul

Servo webcam_servo_tilt; // Variável Servo
Servo webcam_servo_pan; // Variável Servo

int eva_pan   = 512; // centro
int eva_tilt  = 512; // centro
int eva_velocity = 35; // velocidade de movimentacao da cabeça do EVA

void setup()
{
	ax12a.begin(BaudRate, DirectionPin, &Serial);
  webcam_servo_tilt.attach(WEBCAM_SERVO_TILT); // vertical
  webcam_servo_pan.attach(WEBCAM_SERVO_PAN); // horizontal
  webcam_servo_tilt.write(90); // vertical 40 (up) < 90 > 120 (down) esses são os limites.
  webcam_servo_pan.write(90); // horizontal 55 (direita da cam) < 90 > 125 (parece ser o suficiente, mas pode ir mais para os dois lados)
}

void loop()
{
  if (Serial.available() > 0){
    char command = Serial.read();
    delay(20);

    // COmandos para controlar os movimentos da webcam
    if (command == 't') { // tilt da webcam
      delay(10);
      char angulo = Serial.read();
      delay(10);
      webcam_servo_tilt.write(angulo); // vertical
    }
    else if (command == 'p') { // pan da webcam
      delay(10);
      char angulo = Serial.read();
      delay(10);
      webcam_servo_pan.write(angulo); // horizontal
    }
    // Comandos para o servomotor da cabea do robô ///////////////////////////
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
  }
}


void eva_center (){ // centraliza a cabeça
  eva_pan = 512;
  eva_tilt = 512;
  ax12a.moveSpeed(ID_EVA_TILT, eva_tilt, eva_velocity);
  delay(10);
  ax12a.moveSpeed(ID_EVA_PAN, eva_pan, eva_velocity);
}


void eva_down (int amplitude){ // baixa a cabeça
  int tilt_range = 25;
  eva_tilt = eva_tilt - (tilt_range * amplitude);
  ax12a.moveSpeed(ID_EVA_TILT, eva_tilt, eva_velocity); 
}


void eva_up (int amplitude){ // ergue a cabeça
  int tilt_range = 25;
  eva_tilt = eva_tilt + (tilt_range * amplitude);
  ax12a.moveSpeed(ID_EVA_TILT, eva_tilt, eva_velocity);
}


void eva_right (int amplitude){ // vira a cabeça para a direita
  int pan_range = 40;
  eva_pan = eva_pan - (pan_range * amplitude);
  ax12a.moveSpeed(ID_EVA_PAN, eva_pan, eva_velocity); 
}


void eva_left (int amplitude){ // vira a cabeça para a direita
  int pan_range = 40;
  eva_pan = eva_pan + (pan_range * amplitude);
  ax12a.moveSpeed(ID_EVA_PAN, eva_pan, eva_velocity); 
}


void eva_nod(int repeticoes){ // Acena com a cabeça, como se estivesse concordando
    int inc_velocity = -20;
    int pause = 900;
    while (repeticoes > 0){
      ax12a.moveSpeed(ID_EVA_TILT, eva_tilt + 40, eva_velocity + inc_velocity); // para cima
      delay(pause); // tempo para a cabeça chegar na posição desejada
      ax12a.moveSpeed(ID_EVA_TILT, eva_tilt, eva_velocity + inc_velocity); // para a posicao inicial
      delay(pause); // tempo para a cabeça chegar na posição desejada
      repeticoes --;
  }
}


void eva_shake(int repeticoes){ // sacode a cabeça, como se estivesse dizendo um não
  int inc_velocity = 1;
  int pause = 500;
  while (repeticoes > 0){
    ax12a.moveSpeed(ID_EVA_PAN, eva_pan + 40, eva_velocity + inc_velocity); // para esquerda
    delay(pause); // tempo para a cabeça chegar na posição desejada
    ax12a.moveSpeed(ID_EVA_PAN, eva_pan, eva_velocity + inc_velocity); // para a posicao inicial
    delay(pause); // tempo para a cabeça chegar na posição desejada
    ax12a.moveSpeed(ID_EVA_PAN, eva_pan - 40, eva_velocity + inc_velocity); // para direita
    delay(pause); // tempo para a cabeça chegar na posição desejada
    ax12a.moveSpeed(ID_EVA_PAN, eva_pan, eva_velocity + inc_velocity); // para a posicao inicial
    delay(pause); // tempo para a cabeça chegar na posição desejada
    repeticoes --;
  }
}
