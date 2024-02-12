/*
 * Software de controle para os servomotores do robô EVA (nova versão 2024)
 * Autor: Marcelo Marques da Rocha (Universidade Federal Fluminense)
 * Google Research / MidiaCom LAB
 */

#include "Arduino.h"
#include "AX12A.h"
#include <VarSpeedServo.h>


#define EVA_PAN_SERVO_ID    1 // horizontal.
#define EVA_TILT_SERVO_ID   2 // vertical.

#define ARM_LEFT_PIN 8 // Porta Digital 8 PWM (Left Arm).
#define ARM_RIGHT_PIN 9 // Porta Digital 9 PWM (Right Arm).

#define DirectionPin 	10u
#define BaudRate  		1000000ul

VarSpeedServo arm_left_servo;
VarSpeedServo arm_right_servo;

int eva_pan_value   = 512; // centro.
int eva_tilt_value  = 512; // centro.
int eva_pan_target = 512; // em repouso na posição y inicial.
int eva_tilt_target = 512; // em repouso na posição x inicial.
int eva_velocity = 50; // velocidade de movimentacao da cabeça do EVA.
int tilt_range = 30; // amplitude (1x) de um tilt (movimento da cabeça na vertical).
int pan_range = 40; // amplitude (1x) de um pan (movimento da cabeça na horizontal).
int eva_tilt_up_limit = eva_tilt_value + (2 * tilt_range); // Angulo máximo da cabeça no movimento UP.
int eva_tilt_down_limit = eva_tilt_value - (2 * (tilt_range - 10)); // Angulo mínimo da cabeça no movimento DOWN.
int eva_pan_right_limit = eva_pan_value - (3 * pan_range); // Limite máximo do movimento para a direita.
int eva_pan_left_limit = eva_pan_value + (3 * pan_range); // Limite máximo do movimento para a esquerda.
int fator_de_amplitude = 2; // Amplitude dobrada para os movimentos do tipo 2x.
// timers para simular a independência dos movimentos.
char head_move_interval = 1; // Os comandos são enviados para o AX12 à cada X milisegundos.
unsigned long head_timer; // timer para a movimentação da cabeça do robô.
// the head states can be all chars that represents the head motion commands: U, u, c, l, r etc
char head_state = 'i'; // idle (Initial state)


// Variaveis relacionadas com os braços do robô. O braço pode estar em 4 posições (p0, p1, p2 e p3).
// A regulagem das posições dos braços pode ser feita através destas variáveis.
int arm_left_p0 = 150; // posiçao mínima do braço esquerdo.
int arm_left_p1 = 110;
int arm_left_p2 = 80;
int arm_left_p3 = 50; // altura máxima do braço esquerdo com a cabeça centralizada.

int arm_right_p0 = 50; // posiçao mínima do braço direito.
int arm_right_p1 = 80;
int arm_right_p2 = 110;
int arm_right_p3 = 140; // altura máxima do braço direito com a cabeça centralizada.

char arm_left_state = '_'; // Estados possíveis 0, 1, 2, 3 e s
char arm_right_state = '_'; // Estados possíveis 0, 1, 2, 3 e s
int arm_velocity = 60;

void setup()
{
	ax12a.begin(BaudRate, DirectionPin, &Serial);
  arm_left_servo.attach(ARM_LEFT_PIN);
  arm_right_servo.attach(ARM_RIGHT_PIN);
}

void loop()
{
  // Incializa as posições iniciais da cabeça e dos braços do EVA.
  Serial.println("");
  Serial.println("Motion control software is working.");
  // Centraliza a cabeça.
  Serial.println("Centering the head...");
  head_center();

  // Coloca os braços na posição (p0) e estado inicial (0).
  Serial.println("");
  Serial.println("Setting the Arms to their initial position (0)");
  arm_left_servo.write(arm_left_p0, 30);
  arm_left_state = '0'; // Posição inicial.
  arm_right_servo.write(arm_right_p0, 30);
  arm_right_state = '0'; // Posição inicial.

  while(1){
    // trata os estados do robô referentes aos seus movimentos: cabeça, braço esquerdo e direito.
    if (head_state == 'i'){
      head_timer = millis();
    }
    else {
      if ((millis() - head_timer) >= head_move_interval)
      {
        head_motion();
      }
    }

    // desliga os servos quando estão sem movimento.
    if (!arm_left_servo.isMoving())
      arm_left_servo.detach();
    if (!arm_right_servo.isMoving())
      arm_right_servo.detach();

    // recebe os comandos da serial port e muda os estados do robô.
    read_serial_buffer();
  }
}



// Head motion
void head_motion(){
  // tilt movements
  if ((head_state == 'd' || head_state == 'D')) 
    head_down();
  else if ((head_state == 'u') || (head_state == 'U')) 
    head_up();
  // pan movements
  else if ((head_state == 'l') || (head_state == 'L'))
    head_left();
  else if ((head_state == 'r') || (head_state == 'R'))
    head_right();
  // composed movements
  else if ((head_state == 'z') || (head_state == 'Z')){
    head_down();
    head_left();
  }
  else if ((head_state == 'x') || (head_state == 'X')){
    head_down();
    head_right();
  }
  else if ((head_state == 'q') || (head_state == 'Q')){
    head_up();
    head_left();
  }
  else if ((head_state == 'e') || (head_state == 'E')){
    head_up();
    head_right();
  }
}


// Função que lê o buffer da porta serial recebendo os comandos
void read_serial_buffer(){
  if (Serial.available() > 0){
    char command = Serial.read();
    delay(20);

    // Protocolo de controle dos braços do EVA:
    // 1) deve ser enviado um char 'a', de Arm;
    // 2) em seguida, deve ser enviado um char indicando o braço 'l' (esquerdo) ou 'r' (direito);
    // 3) deve ser enviado um char '0', '1', '2' ou '3' (indicando a posição de destino do braço) ou 's' para "sacudir" o braço, a partir da posição corrente.
    if (command == 'a') { // Comando para os braços.
      char arm = Serial.read();
      delay(20);
      if (arm == 'l'){ // Braço esquerdo.
        arm_left_servo.attach(ARM_LEFT_PIN);
        char pos = Serial.read();
        delay(20);
        if (pos == '0'){
          arm_left_servo.write(arm_left_p0, arm_velocity);
          arm_left_state = '0';
        } else if (pos == '1'){
          arm_left_servo.write(arm_left_p1, arm_velocity);
          arm_left_state = '1';
        } else if (pos == '2'){
          arm_left_servo.write(arm_left_p2, arm_velocity);
          arm_left_state = '2';
        } else if (pos == '3'){
          arm_left_servo.write(arm_left_p3, arm_velocity);
          arm_left_state = '3';
        }
        Serial.println("");
        Serial.print("Left_Arm (state): ");
        Serial.print(arm_left_state);
      }
      if (arm == 'r'){ // Braço direito.
        arm_right_servo.attach(ARM_RIGHT_PIN);
        char pos = Serial.read();
        delay(20);
        if (pos == '0'){
          arm_right_servo.write(arm_right_p0, arm_velocity);
          arm_right_state = '0';
        } else if (pos == '1'){
          arm_right_servo.write(arm_right_p1, arm_velocity);
          arm_right_state = '1';
        } else if (pos == '2'){
          arm_right_servo.write(arm_right_p2, arm_velocity);
          arm_right_state = '2';
        } else if (pos == '3'){
          arm_right_servo.write(arm_right_p3, arm_velocity);
          arm_right_state = '3';
        }
        Serial.println("");
        Serial.print("Right_Arm (state): ");
        Serial.print(arm_right_state);
      }
    }
    else if (command == 'p') { // pan da webcam
      char angulo = Serial.read();
      delay(20);
      if (angulo >= 60 && angulo <= 120 )
        ;//webcam_servo_pan.write(angulo); // horizontal
    }

    // Comandos para o servomotor da cabeça do robô EVA
    // Compatível com o protocolo dos Mexicanos, utilizando apenas um caractere
    else if (command == 'c') { // centraliza a cabeça do robô
      head_center();
    }
    else if (command == 'd') { // baixa a cabeça
        head_state = 'd';
        eva_tilt_target = eva_tilt_value - ((tilt_range - 10) * 1); // Os movimentos para baixo usam um tilt_range diminuido de 10 unidades.
    }
    else if (command == 'D') { // baixa a cabeça
        head_state = 'D';
        eva_tilt_target = eva_tilt_value - ((tilt_range - 10) * fator_de_amplitude); // Os movimentos para baixo usam um tilt_range diminuido de 10 unidades.
    }
    else if (command == 'u') { // baixa a cabeça
        head_state = 'u';
        eva_tilt_target = eva_tilt_value + (tilt_range * 1);
    }
    else if (command == 'U') { // baixa a cabeça
        head_state = 'U';
        eva_tilt_target = eva_tilt_value + (tilt_range * fator_de_amplitude);
    }
    else if (command == 'r') { // vira a cabeça a direita
        head_state = 'r';
        eva_pan_target = eva_pan_value - (pan_range * 1);
    }
    else if (command == 'R') { // vira a cabeça a direita
        head_state = 'R';
        eva_pan_target = eva_pan_value - (pan_range * fator_de_amplitude);
    }
    else if (command == 'l') { // vira a cabeça a esquerda
        head_state = 'l';
        eva_pan_target = eva_pan_value + (pan_range * 1);
    }
    else if (command == 'L') { // vira a cabeça a esqyerda
        head_state = 'L';
        eva_pan_target = eva_pan_value + (pan_range * fator_de_amplitude);
    }
    else if (command == 'e') { // vira a cabeça para cima e para a direita
      head_state = 'e';
      eva_tilt_target = eva_tilt_value + (tilt_range * 1);
      eva_pan_target = eva_pan_value - (pan_range * 1);
    }
    else if (command == 'E') { // vira a cabeça para cima e para a direita
      head_state = 'E';
      eva_tilt_target = eva_tilt_value + (tilt_range * fator_de_amplitude);
      eva_pan_target = eva_pan_value - (pan_range * fator_de_amplitude);
    }
    else if (command == 'q') { // vira a cabeça para cima e para a esquerda
      head_state = 'q';
      eva_tilt_target = eva_tilt_value + (tilt_range * 1);
      eva_pan_target = eva_pan_value + (pan_range * 2);
    }
    else if (command == 'Q') { // vira a cabeça para cima e para a esquerda
      head_state = 'Q';
      eva_tilt_target = eva_tilt_value + (tilt_range * fator_de_amplitude);
      eva_pan_target = eva_pan_value + (pan_range * fator_de_amplitude);
    }
    else if (command == 'x') { // vira a cabeça para baixo e para a direita
      head_state = 'x';
      eva_tilt_target = eva_tilt_value - ((tilt_range - 10) * 1);
      eva_pan_target = eva_pan_value - (pan_range * 1);
    }
    else if (command == 'X') { // vira a cabeça para baixo e para a direita
      head_state = 'X';
      eva_tilt_target = eva_tilt_value - ((tilt_range - 10) * fator_de_amplitude);
      eva_pan_target = eva_pan_value - (pan_range * fator_de_amplitude);
    }
    else if (command == 'z') { // vira a cabeça para baixo e para a esquerda
      head_state = 'z';
      eva_tilt_target = eva_tilt_value - ((tilt_range - 10) * 1);
      eva_pan_target = eva_pan_value + (pan_range * 1);
    }
    else if (command == 'Z') { // vira a cabeça para baixo e para a esquerda
      head_state = 'Z';
      eva_tilt_target = eva_tilt_value - ((tilt_range - 10) * fator_de_amplitude);
      eva_pan_target = eva_pan_value + (pan_range * fator_de_amplitude);
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
    else if (command == 'S') { // sacode a cabeça (shake) como se estivesse dizendo um não
      eva_shake(4); // movimento com 4 repeticoes
    }

    // Protocolo com 3 caracteres utilizado para movimentar a cabeça utilizando um parametro de posição.
    // O caractere # sinaliza o protocolo de 3 chars. Em seguida vem o char que indica a função (up_down ou left_right) 
    // Então vem o char que indica a posição de destino do servomotor
    // else if (command == '#') { // protocolo com 3 chars
    //   char tipo = Serial.read();
    //   delay(20);
    //   char posicao = Serial.read();
    //   if (tipo == 't'){
    //     eva_tilt(posicao); // Posição vertical
    //   }
    //   else if (tipo == 'p'){
    //     eva_pan(posicao); // Posição horizontal
    //   }
    // }
  }
}

void head_center (){ // centraliza a cabeça
  eva_pan_value = 512;
  eva_tilt_value = 512;
  ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity);
  delay(10);
  ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
}

//////////////////////////////////////////////////////////////////////////////////
/////////////////////////// NOVAS FUNÇÕES DE MOVIMENTO ///////////////////////////
//////////////////////////////////////////////////////////////////////////////////
/////// Movimentos Simples (unidimensionais) ////////////////////
void head_down (){ // baixa a cabeça do robô.
  if (eva_tilt_value > eva_tilt_down_limit){ // verifica se está dentro do limite mínimo para o movimento DOWN. 
    if (eva_tilt_value <= eva_tilt_target){ // chegou à posição de destino
      head_state = 'i'; 
    } else {
      eva_tilt_value = eva_tilt_value - 1;
      ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity);
      head_timer = millis();
    }
  } else {
    head_state = 'i';
    head_timer = millis();
  }
}


void head_up (){ // Levanta a cabeça do robô.
  if (eva_tilt_value < eva_tilt_up_limit){ // verifica se está dentro do limite máximo para o movimento UP. 
    if (eva_tilt_value >= eva_tilt_target){ // chegou à posição de destino
      head_state = 'i'; 
    } else {
      eva_tilt_value = eva_tilt_value + 1;
      ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity);
      head_timer = millis();
    }
  } else {
    head_state = 'i';
    head_timer = millis();
  }
}


void head_left (){ // vira a cabeça do robô para a esquerda.
  if (eva_pan_value < eva_pan_left_limit){ // verifica se está dentro do limite máximo para o movimento LEFT. 
    if (eva_pan_value >= eva_pan_target){
      head_state = 'i'; 
    } else {
      eva_pan_value = eva_pan_value + 1;
      ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity); 
      head_timer = millis();
    }
  } else {
    head_state = 'i';
    head_timer = millis();
  }
}


void head_right (){ // vira a cabeça do robô para a direta.
  if (eva_pan_value > eva_pan_right_limit){ // verifica se está dentro do limite máximo para o movimento RIGHT.
    if (eva_pan_value <= eva_pan_target){
        head_state = 'i'; 
    } else {
      eva_pan_value = eva_pan_value - 1;
      ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity); 
      head_timer = millis();
    }
  } else {
    head_state = 'i';
    head_timer = millis();
  }
}



// void eva_up (int amplitude){ // ergue a cabeça
//   Serial.println("EvaUP");
//   eva_tilt_value = eva_tilt_value + (tilt_range * amplitude);
//   ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity);
// }


// void eva_right (int amplitude){ // vira a cabeça para a direita
//   eva_pan_value = eva_pan_value - (pan_range * amplitude);
//   ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity); 
// }


// void eva_left (int amplitude){ // vira a cabeça para a direita
//   eva_pan_value = eva_pan_value + (pan_range * amplitude);
//   ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity); 
// }


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
// void eva_tilt(int posicao_vertical){
//   int eva_tilt_value = (90 + (90 - posicao_vertical)) * 5.75;
//   ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity + 15);
// }


// void eva_pan(int posicao_horizontal){
//   int eva_pan_value = posicao_horizontal * 5.68;
//   ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity + 15);
// }
