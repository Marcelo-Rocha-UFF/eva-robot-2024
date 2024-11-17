/*
 * Software de controle para os servomotores do robô EVA (nova versão 2024)
 * Adição de movimentação dos braços do robô
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

int eva_pan_center   = 512; // centro.
int eva_tilt_center  = 512; // centro.
int eva_pan_value   = eva_pan_center; // centro.
int eva_tilt_value  = eva_tilt_center; // centro.
int eva_velocity = 50; // velocidade de movimentacao da cabeça do EVA.
int tilt_range = 30; // amplitude (1x) de um tilt (movimento da cabeça na vertical).
int pan_range = 40; // amplitude (1x) de um pan (movimento da cabeça na horizontal).
int eva_tilt_up_limit = eva_tilt_center + (2 * tilt_range); // Angulo máximo da cabeça no movimento UP.
int eva_tilt_down_limit = eva_tilt_center - (2 * (tilt_range - 10)); // Angulo mínimo da cabeça no movimento DOWN.
int eva_pan_right_limit = eva_pan_center - (3 * pan_range); // Limite máximo do movimento para a direita.
int eva_pan_left_limit = eva_pan_center + (3 * pan_range); // Limite máximo do movimento para a esquerda.

//

// timers para simular a independência dos movimentos.
unsigned long head_timer; // timer para a movimentação da cabeça do robô.
// the head states can be all chars that represents the head motion commands: U, u, c, l, r etc.
char head_state = 'i'; // idle (sem movimentação da cabeça).
// shake movement (como um "sim").
char head_shake_state = '0'; // sem movimento;
int head_shake_repetitions = 1; // quantidade de repetições de um shake da cabeça.
// nod movement (como um "não")
char head_nod_state = '0'; // sem movimento;
int nod_repetitions = 1; // quantidade de repetições de um shake da cabeça.

// Coordenadas vertical (tilt) e horizontal (pan) das posições pré-definidas.
int L1 = 552; int L2 = 592; int L3 = 632;
int R1 = 472; int R2 = 432; int R3 = 392;
int U1 = 542; int U2 = 572;
int D1 = 492; int D2 = 472;

// Variaveis relacionadas com os braços do robô. O braço pode estar em 4 posições (p0, p1, p2 e p3).
// A regulagem das posições dos braços pode ser feita através destas variáveis.
int arm_left_p0 = 120; // posiçao mínima do braço esquerdo.
int arm_left_p1 = 85;
int arm_left_p2 = 60;
int arm_left_p3 = 40; // altura máxima do braço esquerdo com a cabeça centralizada.

int arm_right_p0 = 40; // posiçao mínima do braço direito.
int arm_right_p1 = 70;
int arm_right_p2 = 90;
int arm_right_p3 = 110; // altura máxima do braço direito com a cabeça centralizada.

char arm_left_state = '_'; // estados possíveis 0, 1, 2, 3, s ou S.
char arm_right_state = '_'; // estados possíveis 0, 1, 2, 3, s ou S.
char arm_right_shake_state = '0'; // estados do braço direito durante o movimento de shaking.
char arm_left_shake_state = '0'; // estados do braço esquerdo durante o movimento de shaking.
int arm_velocity = 40;

bool arm_left_active = true; // começa ativo pois o SG90 (left) é inicializado.
bool arm_left_timer_active = false;
bool arm_right_active= true; // começa ativo pois o SG90 (right) é inicializado.
bool arm_right_timer_active = false;
// a função arm_left_servo.isMoving() indica que o servo parou de mover, um pouco antes dele ter chegado ao destino de fato.
// por isso utilizamos um timer (para o arm_left e arm_right) com um intervalo de tempo, antes do servo.dettach(), para que os servos, de fato, cheguem aos seus destinos.
unsigned long arm_left_timer; 
unsigned long arm_right_timer;

// estes timers são usados para o movimento de shake dos braços quando estão no estado 's' ou 'S'.
unsigned long arm_left_shake_timer; 
unsigned long arm_right_shake_timer;

// posições referentes aos pontos de oscilação do braço direito e esquerdo.
int arm_right_shake_start;
int arm_right_shake_end;

int arm_left_shake_start;
int arm_left_shake_end;

// variáveis que controlam o nímero de repetições do "shake" dos braços.
int arm_right_shake_repetitions = 1;
int arm_left_shake_repetitions = 1;



void setup()
{
	ax12a.begin(BaudRate, DirectionPin, &Serial);
  arm_left_servo.attach(ARM_LEFT_PIN);
  arm_right_servo.attach(ARM_RIGHT_PIN);
  head_timer = millis();
}

void loop()
{
  // incializa as posições iniciais da cabeça e dos braços do EVA.
  Serial.println("");
  Serial.println("Motion control software is working.");
  // Centraliza a cabeça.
  Serial.println("Centering the head...");
  head_init();

  // coloca os braços na posição (p0) e estado inicial (0).
  Serial.println("");
  Serial.println("Setting the Arms to their initial position (0)");
  arm_left_servo.write(arm_left_p0, 30);
  arm_left_state = '0'; // Posição inicial.
  arm_right_servo.write(arm_right_p0, 30);
  arm_right_state = '0'; // Posição inicial.

  while(1){ // este é o looping principal do software de controle.
    // trata os estados do robô referentes aos seus movimentos: cabeça, braço esquerdo e direito.

    // a cabeça do robô entra neste estado (s ou S) quando está "shaking", como se dissesse um 'não'.
    if ((head_state == 's') || (head_state == 'S')){
      head_shake();
    }
    // a cabeça do robô entra neste estado (n ou N ou NOD) como se dissesse um 'sim'.
    if ((head_state == 'n') || (head_state == 'N')){
        head_nod();
    }
    // o braço direito do robô entra neste estado (s ou S) quando está sacudindo o braçõ (arm_right_shake()).
    if ((arm_right_state == 's') || (arm_right_state == 'S')){
      // o tipo do 's' serve para indicar o número de repetições do movimento.
      arm_right_shake();
    }
    // o braço esquerdo do robô entra neste estado (s ou S) quando está sacudindo o braçõ (arm_right_shake()).
    if ((arm_left_state == 's') || (arm_left_state == 'S')){
      // o tipo do 's' serve para indicar o número de repetições do movimento.
      arm_left_shake();
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    // trata o desligamento dos servomotores dos braços quando eles estão sem movimento, ou seja, fora dos estados 's' e 'S' //
    ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    if ((arm_right_state != 's') && (arm_right_state != 'S') and (arm_left_state != 's') && (arm_left_state != 'S')){
      
      if ((!arm_left_servo.isMoving()) && (arm_left_active)){ // desliga os servos quando estão sem movimento.
        arm_left_active = false;
        arm_left_timer_active = true;
        arm_left_timer = millis();
      }
      if ((!arm_right_servo.isMoving()) && (arm_right_active)){ // desliga os servos quando estão sem movimento.
        arm_right_active = false;
        arm_right_timer_active = true;
        arm_right_timer = millis();
      }
      if (arm_left_timer_active){
        if ((millis() - arm_left_timer) > 200){ // aguarda 300ms para desligar o arm_lerft (SG90).
          Serial.print("left dettach");
          arm_left_servo.detach();
          arm_left_timer_active = false;
        }
      }
      if (arm_right_timer_active){
        if ((millis() - arm_right_timer) > 200){ // aguarda 300ms para desligar o arm_right (SG90).
          arm_right_servo.detach();
          arm_right_timer_active = false;
          Serial.print("right dettach");
        }
      }
    }


    //////////////////////////////////////////////
    // lê a porta serial recebendo  os comandos. //
    //////////////////////////////////////////////
    read_serial_buffer();
  }
}

//////////////////////////////////////////////////////////////////
// Função que lê o buffer da porta serial recebendo os comandos //
//////////////////////////////////////////////////////////////////
void read_serial_buffer(){
  if (Serial.available() > 0){
    char command = Serial.read();
    delay(20);
    // Protocolo de controle dos braços do EVA:
    // 1) deve ser enviado um char 'a', de Arm;
    // 2) em seguida, deve ser enviado um char indicando o braço 'l' (esquerdo) ou 'r' (direito);
    // 3) deve ser enviado um char '0', '1', '2' ou '3' (indicando a posição de destino do braço) ou 's' para "sacudir" o braço, a partir da posição corrente.
  /////////////////////////
    if (command == 'a') { // comando para os braços.
      char arm = Serial.read();
      delay(20);
      if (arm == 'l'){ // controle do braço esquerdo (left).
        arm_left_servo.attach(ARM_LEFT_PIN);
        arm_left_active = true;
        char pos = Serial.read();
        delay(20);
        if (pos == '0'){ // move o braço esquerdo para posição 0.
          arm_left_servo.write(arm_left_p0, arm_velocity);
          arm_left_state = '0';
        }
        else if (pos == '1'){ // move o braço esquerdo para posição 1.
          arm_left_servo.write(arm_left_p1, arm_velocity);
          arm_left_state = '1';
        }
        else if (pos == '2'){ // move o braço esquerdo para posição 2.
          arm_left_servo.write(arm_left_p2, arm_velocity);
          arm_left_state = '2';
        }
        else if (pos == '3'){ // move o braço esquerdo para posição 3.
          arm_left_servo.write(arm_left_p3, arm_velocity);
          arm_left_state = '3';
        }
        else if (pos == 'u'){ // move o braço esquerdo para cima.
          if (arm_left_state == '0'){ // move o braço esquerdo para cima, a aprtir da posição corrente.
            arm_left_servo.write(arm_left_p1, arm_velocity);
            arm_left_state = '1';
          }
          else if (arm_left_state == '1'){ // move o braço esquerdo para cima, a aprtir da posição corrente.
            arm_left_servo.write(arm_left_p2, arm_velocity);
            arm_left_state = '2';
          }
          else if (arm_left_state == '2'){ // move o braço esquerdo para cima, a aprtir da posição corrente.
            arm_left_servo.write(arm_left_p3, arm_velocity);
            arm_left_state = '3';
          }
        }
        else if (pos == 'd'){ // move o braço esquerdo para baixo. 
          if (arm_left_state == '3'){ // move o braço esquerdo para baixo, a partir da posição corrente.
            arm_left_servo.write(arm_left_p2, arm_velocity);
            arm_left_state = '2';
          }
          else if (arm_left_state == '2'){ // move o braço esquerdo para baixo, a partir da posição corrente.
            arm_left_servo.write(arm_left_p1, arm_velocity);
            arm_left_state = '1';
          }
          else if (arm_left_state == '1'){ // move o braço esquerdo para baixo, a partir da posição corrente.
            arm_left_servo.write(arm_left_p0, arm_velocity);
            arm_left_state = '0';
          }
        }
        else if (pos == 's'){
          arm_left_shake_repetitions = 1;
          arm_left_shake();
        }
        else if (pos == 'S'){
          arm_left_shake_repetitions = 2;
          arm_left_shake();
        }
      }
      else if (arm == 'r'){ // controle do braço direito (right).
        arm_right_servo.attach(ARM_RIGHT_PIN);
        arm_right_active = true;
        char pos = Serial.read();
        delay(20);
        if (pos == '0'){ // move o braço direto para posição 0.
          arm_right_servo.write(arm_right_p0, arm_velocity);
          arm_right_state = '0';
        }
        else if (pos == '1'){ // move o braço direto para posição 1.
          arm_right_servo.write(arm_right_p1, arm_velocity);
          arm_right_state = '1';
        }
        else if (pos == '2'){ // move o braço direto para posição 2.
          arm_right_servo.write(arm_right_p2, arm_velocity);
          arm_right_state = '2';
        }
        else if (pos == '3'){ // move o braço direto para posição 3.
          arm_right_servo.write(arm_right_p3, arm_velocity);
          arm_right_state = '3';
        }
        else if (pos == 'u'){ // move o braço direito para cima (up).
          if (arm_right_state == '0'){ // move o braço direito para cima, a partir da posição corrente.
            arm_right_servo.write(arm_right_p1, arm_velocity);
            arm_right_state = '1';
          }
          else if (arm_right_state == '1'){ // move o braço direito para cima, a partir da posição corrente.
            arm_right_servo.write(arm_right_p2, arm_velocity);
            arm_right_state = '2';
          }
          else if (arm_right_state == '2'){ // move o braço direito para cima, a partir da posição corrente.
            arm_right_servo.write(arm_right_p3, arm_velocity);
            arm_right_state = '3';
          }
        }
        else if (pos == 'd'){ // move o braço direito para baixo (down).
          if (arm_right_state == '3'){ // move o braço direito para baixo, a partir da posição corrente.
            arm_right_servo.write(arm_right_p2, arm_velocity);
            arm_right_state = '2';
          }
          else if (arm_right_state == '2'){ // move o braço direito para baixo, a partir da posição corrente.
            arm_right_servo.write(arm_right_p1, arm_velocity);
            arm_right_state = '1';
          }
          else if (arm_right_state == '1'){ // move o braço direito para baixo, a partir da posição corrente.
            arm_right_servo.write(arm_right_p0, arm_velocity);
            arm_right_state = '0';
          }
        }
        else if (pos == 's'){
          arm_right_shake_repetitions = 1;
          arm_right_shake();
        }
        else if (pos == 'S'){
          arm_right_shake_repetitions = 2;
          arm_right_shake();
        }
      }
    }
    ///////////////////////////////////////////////////////////////////////////////////////
    // comandos para o servomotor da cabeça do robô EVA                                  //
    // compatível com o protocolo dos Mexicanos, utilizando apenas um caractere (1 byte) //
    ///////////////////////////////////////////////////////////////////////////////////////
    else if (command == 'c') { // centraliza a cabeça do robô
      eva_tilt_value = eva_tilt_center;
      eva_pan_value = eva_pan_center;
      ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30); // redução da velocidade nos movimentos verticais.
      ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
      delay(20);
    } /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    else if (command == 'd') { // baixa a cabeça.
      if (eva_tilt_value > eva_tilt_center){
        eva_tilt_value -= (tilt_range); // quantidade de deslocamento normal, acima do ponto central do eixo vertical.
        if (head_test_limits(eva_tilt_value, eva_pan_value)){
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30); // redução da velocidade nos movimentos verticais.
          delay(20);
        }
        else {
          eva_tilt_value += (tilt_range);
        }
      }
      else {
        eva_tilt_value -= (tilt_range - 10); // O deslocamento vertical abaixo da posição central é 10 unidades menor.
        if (head_test_limits(eva_tilt_value, eva_pan_value)){
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30); // redução da velocidade nos movimentos verticais.
          delay(20);
        }
        else {
          eva_tilt_value += (tilt_range - 10);
        }
      }
    } /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    else if (command == 'D') { // baixa a cabeça com o dobro da amplitude.
    if (eva_tilt_value > eva_tilt_center){
        eva_tilt_value -= (tilt_range * 2); // quantidade de deslocamento normal, acima do ponto central do eixo vertical.
        if (head_test_limits(eva_tilt_value, eva_pan_value)){
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30); // redução da velocidade nos movimentos verticais.
          delay(20);
        }
        else {
          eva_tilt_value += (tilt_range * 2);
        }
      }
      else {
        eva_tilt_value -= ((tilt_range - 10) * 2); // O deslocamento vertical abaixo da posição central é 10 unidades menor.
        if (head_test_limits(eva_tilt_value, eva_pan_value)){
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30); // redução da velocidade nos movimentos verticais.
          delay(20);
        }
        else {
          eva_tilt_value += ((tilt_range - 10) * 2);
        }
      }
    } /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    else if (command == 'u') { // ergue a cabeça.
      if (eva_tilt_value >= eva_tilt_center){
        eva_tilt_value += tilt_range; // quantidade de deslocamento normal, acima da região central.
        if (head_test_limits(eva_tilt_value, eva_pan_value)){
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30); // redução da velocidade nos movimentos verticais.
          delay(20);
        }
        else {
          eva_tilt_value -= tilt_range;
        }
      }
      else {
        eva_tilt_value += (tilt_range - 10);
        if (head_test_limits(eva_tilt_value, eva_pan_value)){
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30); // redução da velocidade nos movimentos verticais.
          delay(20);
        }
        else {
          eva_tilt_value -= (tilt_range - 10); // O deslocamento vertical abaixo da posição central é 10 unidades menor.
        }
      }
    } /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    else if (command == 'U') { // ergue a cabeça com o dobro da amplitude.
      if (eva_tilt_value >= eva_tilt_center){
        eva_tilt_value += (tilt_range * 2); // quantidade de deslocamento normal, acima da região central.
        if (head_test_limits(eva_tilt_value, eva_pan_value)){
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30); // redução da velocidade nos movimentos verticais.
          delay(20);
        }
        else {
          eva_tilt_value -= (tilt_range * 2);
        }
      }
      else {
        eva_tilt_value += ((tilt_range - 10) * 2);  // O deslocamento vertical abaixo da posição central é 10 unidades menor.
        if (head_test_limits(eva_tilt_value, eva_pan_value)){
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30); // redução da velocidade nos movimentos verticais.
          delay(20);
        }
        else {
          eva_tilt_value -= ((tilt_range - 10) * 2);
        }
      }
        
    } /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    else if (command == 'r') { // vira a cabeça a direita.
      eva_pan_value -= pan_range;
      if (head_test_limits(eva_tilt_value, eva_pan_value)){ // testa os limites.
        ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
        delay(20);
      }
      else {
        eva_pan_value += pan_range; // restaura o valor.
      }
    } /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    else if (command == 'R') { // vira a cabeça a direita com o dobro da amplitude.
      eva_pan_value -= (pan_range * 2);
      if (head_test_limits(eva_tilt_value, eva_pan_value)){ // testa os limites
        ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
        delay(20);
      }
      else {
         eva_pan_value += (pan_range * 2);
      }
    } /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    else if (command == 'l') { // vira a cabeça a esquerda
      eva_pan_value += pan_range;
      if (head_test_limits(eva_tilt_value, eva_pan_value)){ // testa os limites
        ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
        delay(20);
      }
      else {
        eva_pan_value -= pan_range;
      }
    } /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    else if (command == 'L') { // vira a cabeça a esqyerda
      eva_pan_value += (pan_range * 2);
      if (head_test_limits(eva_tilt_value, eva_pan_value)){ // testa os limites
        ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
        delay(20);
      }
      else {
        eva_pan_value -= (pan_range * 2);
      }
    } /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    else if (command == 'e') { // vira a cabeça para cima e para a direita
      eva_pan_value -= pan_range;
      if (eva_tilt_value > eva_tilt_center){
        eva_tilt_value += tilt_range; // quantidade de deslocamento normal, acima da região central.
        if (head_test_limits(eva_tilt_value, eva_pan_value)){ // testa os limites
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else {
          eva_pan_value += pan_range;
          eva_tilt_value += tilt_range;
        }
      }
      else {
        eva_tilt_value += (tilt_range - 10);  // O deslocamento vertical abaixo da posição central é 10 unidades menor.
        if (head_test_limits(eva_tilt_value, eva_pan_value)){ // testa os limites
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else {
          eva_pan_value += pan_range;
          eva_tilt_value -= (tilt_range - 10);
        }
      }
    } /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    else if (command == 'E') { // vira a cabeça para cima e para a direita
      eva_pan_value -= pan_range * 2;
      if (eva_tilt_value > eva_tilt_center){
        eva_tilt_value += (tilt_range * 2); // quantidade de deslocamento normal, acima da região central.
        if (head_test_limits(eva_tilt_value, eva_pan_value)){ // testa os limites
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else {
          eva_pan_value += pan_range * 2;
          eva_tilt_value += (tilt_range * 2);
        }
      }
      else {
        eva_tilt_value += ((tilt_range - 10) * 2);  // O deslocamento vertical abaixo da posição central é 10 unidades menor.
        if (head_test_limits(eva_tilt_value, eva_pan_value)){ // testa os limites
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else {
          eva_pan_value += pan_range;
          eva_tilt_value -= ((tilt_range - 10) * 2); 
        }
      }
    } /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    else if (command == 'q') { // vira a cabeça para cima e para a esquerda
      eva_pan_value += pan_range;
      if (eva_tilt_value > eva_tilt_center){
        eva_tilt_value += tilt_range; // quantidade de deslocamento normal, acima da região central.
        if (head_test_limits(eva_tilt_value, eva_pan_value)){ // testa os limites
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else {
          eva_pan_value -= pan_range;
          eva_tilt_value += tilt_range;
        }
      }
      else {
        eva_tilt_value += (tilt_range - 10);  // O deslocamento vertical abaixo da posição central é 10 unidades menor.
        if (head_test_limits(eva_tilt_value, eva_pan_value)){ // testa os limites
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else {
          eva_pan_value -= pan_range;
          eva_tilt_value -= (tilt_range - 10);
        }
      }
    } /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    else if (command == 'Q') { // vira a cabeça para cima e para a esquerda com dupla amplitude
      eva_pan_value += (pan_range * 2);
      if (eva_tilt_value > eva_tilt_center){
        eva_tilt_value += (tilt_range * 2); // quantidade de deslocamento normal, acima da região central.
        if (head_test_limits(eva_tilt_value, eva_pan_value)){ // testa os limites
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else {
          eva_pan_value -= (pan_range * 2);
          eva_tilt_value += (tilt_range * 2);
        }
      }
      else {
        eva_tilt_value += ((tilt_range - 10) * 2);  // O deslocamento vertical abaixo da posição central é 10 unidades menor.
        if (head_test_limits(eva_tilt_value, eva_pan_value)){ // testa os limites
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else {
          eva_pan_value -= (pan_range * 2);
          eva_tilt_value += ((tilt_range - 10) * 2);
        }
      }
    } /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    else if (command == 'x') { // vira a cabeça para baixo e para a direita.
      eva_pan_value -= pan_range;
      if (eva_tilt_value > eva_tilt_center){
        eva_tilt_value -= tilt_range; // quantidade de deslocamento normal, acima da região central.
        if (head_test_limits(eva_tilt_value, eva_pan_value)){ // testa os limites
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else {
          eva_tilt_value += tilt_range;
          eva_pan_value += pan_range;
        }
      }
      else {
        eva_tilt_value -= (tilt_range - 10);  // O deslocamento vertical abaixo da posição central é 10 unidades menor.
        if (head_test_limits(eva_tilt_value, eva_pan_value)){ // testa os limites
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else {
          eva_pan_value += pan_range;
          eva_tilt_value -= (tilt_range + 10);
        }
      }
    } /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    else if (command == 'X') { // vira a cabeça para baixo e para a direita com o dobro da amplitude.
      eva_pan_value -= (pan_range * 2);
      if (eva_tilt_value > eva_tilt_center){
        eva_tilt_value -= (tilt_range * 2); // quantidade de deslocamento normal, acima da região central.
        if (head_test_limits(eva_tilt_value, eva_pan_value)){ // testa os limites
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else {
          eva_pan_value += (pan_range * 2);
          eva_tilt_value += (tilt_range * 2);
        }
      }
      else {
        eva_tilt_value -= ((tilt_range - 10) * 2);  // O deslocamento vertical abaixo da posição central é 10 unidades menor.
        if (head_test_limits(eva_tilt_value, eva_pan_value)){ // testa os limites
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else {
          eva_pan_value += (pan_range * 2);
          eva_tilt_value += ((tilt_range - 10) * 2);
        }
      }
    } /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    else if (command == 'z') { // vira a cabeça para baixo e para a esquerda.
      eva_pan_value += pan_range;
      if (eva_tilt_value > eva_tilt_center){
        eva_tilt_value -= tilt_range;  // quantidade de deslocamento normal, acima da região central.
        if (head_test_limits(eva_tilt_value, eva_pan_value)){ // testa os limites
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else {
          eva_pan_value -= pan_range;
          eva_tilt_value += tilt_range;
        }
      }
      else {
        eva_tilt_value -= (tilt_range - 10);  // O deslocamento vertical abaixo da posição central é 10 unidades menor.
        if (head_test_limits(eva_tilt_value, eva_pan_value)){ // testa os limites
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else {
          eva_pan_value -= pan_range;
          eva_tilt_value += (tilt_range - 10);
        }
      }
    } /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    else if (command == 'Z') { // vira a cabeça para baixo e para a esquerda com o dobro da amplitude.
      eva_pan_value += (pan_range * 2);
      if (eva_tilt_value > eva_tilt_center){
        eva_tilt_value -= (tilt_range * 2);  // quantidade de deslocamento normal, acima da região central.
        if (head_test_limits(eva_tilt_value, eva_pan_value)){ // testa os limites
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else {
          eva_pan_value -= (pan_range * 2);
          eva_tilt_value += (tilt_range * 2);
        }
      }
      else {
        eva_tilt_value -= ((tilt_range - 10) * 2);  // O deslocamento vertical abaixo da posição central é 10 unidades menor.
        if (head_test_limits(eva_tilt_value, eva_pan_value)){ // testa os limites
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else {
          eva_pan_value -= (pan_range * 2);
          eva_tilt_value += (tilt_range - 10);
        }
      }
    } /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    else if (command == 'n') { // movimento que sacode a cabeça do robô (como um "sim") sem repetição.
      if (eva_tilt_value >= 492){ // só executa um head_nod() se estiver até a altura UP_D1, caso seja menor, ignora o camando.
        nod_repetitions = 1;
        head_timer = millis(); // inicia relógio de execução da função nod().
        head_state = 'n';
      }
      else {
        Serial.println("");
        Serial.println("Movimento fora do limite permitido.");
      }
    } /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    else if (command == 'N') { // movimento que sacode a cabeça do robô (como um "sim") com repetição.
      if (eva_tilt_value >= 492){ // só executa um head_nod() se estiver até a altura UP_D1, caso seja menor, ignora o camando.
        nod_repetitions = 2;
        head_timer = millis(); // inicia relógio de execução da função nod().
        head_state = 'N';
      }
      else {
        Serial.println("");
        Serial.println("Movimento fora do limite permitido.");
      }
    } /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    else if (command == 's') { // sacode a cabeça (shake) como se estivesse dizendo um "não", sem repetição.
      head_shake_repetitions = 1;
      head_timer = millis(); // inicia relógio de execução da função shake().
      head_state = 's';
    } /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    else if (command == 'S') { // sacode a cabeça (shake) como se estivesse dizendo um "não", com repetição.
      head_shake_repetitions = 2;
      head_timer = millis(); // inicia relógio de execução da função shake().
      head_state = 's';
    } /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    
    ///////////////////////////////////////////////////////////////////////////////
    // comandos para a movimentação da cabeça utilizando o protocolo de 3 bytes. //
    ///////////////////////////////////////////////////////////////////////////////
    else if (command == 'h') { // comando para a cabeça (head).
      char parametro1 = Serial.read();
      delay(20);
      if (parametro1 == 'l'){ // movimento para a esquerda (left).
        char parametro2 = Serial.read();
        delay(20);
        if (parametro2 == '1'){ // movimento para posição L1.
          eva_pan_value = L1;
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          delay(20);
        }
        else if (parametro2 == '2'){ // movimento para posição L2.
        eva_pan_value = L2;
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          delay(20);
        }
        else { // movimento para posição L3.
          eva_pan_value = L3;
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          delay(20);
        }
      }
      else if (parametro1 == 'r'){ // movimento para a direita (right).
        char parametro2 = Serial.read();
        delay(20);
        if (parametro2 == '1'){ // movimento para posição R1.
          eva_pan_value = R1;
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          delay(20);
        }
        else if (parametro2 == '2'){ // movimento para posição R2.
          eva_pan_value = R2;
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          delay(20);
        }
        else { // movimento para posição R3.
          eva_pan_value = R3;
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          delay(20);
        }
      }
      else if (parametro1 == 'u'){ // movimento para cima (up).
        char parametro2 = Serial.read();
        delay(20);
        if (parametro2 == '1'){ // movimento para posição u1.
          eva_tilt_value = U1;
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else if (parametro2 == '2'){ // movimento para posição u2.
          eva_tilt_value = U2;
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
      }
      else if (parametro1 == 'd'){ // movimento para baixo (down).
        char parametro2 = Serial.read();
        delay(20);
        if (parametro2 == '1'){ // movimento para posição d1.
          eva_tilt_value = D1;
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else if (parametro2 == '2'){ // movimento para posição d2.
          eva_tilt_value = D2;
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
      }
      else if (parametro1 == '1'){ // movimento para esquerda e para cima (quadrante 1).
        char parametro2 = Serial.read();
        delay(20);
        if (parametro2 == '1'){ // movimento para posição 1 do quadrante 1. (movimento em duas dimensões).
          eva_pan_value = L1;
          eva_tilt_value = U1;
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else if (parametro2 == '2'){ // movimento para posição 2 do quadrante 1.  (movimento em duas dimensões).
          eva_pan_value = L2;
          eva_tilt_value = U1;
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else if (parametro2 == '3'){ // movimento para posição 32 do quadrante 1.  (movimento em duas dimensões).
          eva_pan_value = L3;
          eva_tilt_value = U2;
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
      }
      else if (parametro1 == '4'){ // movimento para esquerda e para baixo (quadrante 4).
        char parametro2 = Serial.read();
        delay(20);
        if (parametro2 == '1'){ // movimento para posição 1 do quadrante 4. (movimento em duas dimensões).
          eva_pan_value = L1;
          eva_tilt_value = D1;
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else if (parametro2 == '2'){ // movimento para posição 2 do quadrante 4.  (movimento em duas dimensões).
          eva_pan_value = L2;
          eva_tilt_value = D1;
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else if (parametro2 == '3'){ // movimento para posição 3 do quadrante 4.  (movimento em duas dimensões).
          eva_pan_value = L3;
          eva_tilt_value = D2;
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
      }
      else if (parametro1 == '2'){ // movimento para direita e para cima (quadrante 2).
        char parametro2 = Serial.read();
        delay(20);
        if (parametro2 == '1'){ // movimento para posição 1 do quadrante 2. (movimento em duas dimensões).
          eva_pan_value = R1;
          eva_tilt_value = U1;
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else if (parametro2 == '2'){ // movimento para posição 2 do quadrante 2.  (movimento em duas dimensões).
          eva_pan_value = R2;
          eva_tilt_value = U1;
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else if (parametro2 == '3'){ // movimento para posição 2 do quadrante 2.  (movimento em duas dimensões).
          eva_pan_value = R3;
          eva_tilt_value = U2;
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
      }
      else if (parametro1 == '3'){ // movimento para direita e para baixo (quadrante 3).
        char parametro2 = Serial.read();
        delay(20);
        if (parametro2 == '1'){ // movimento para posição 1 do quadrante 3. (movimento em duas dimensões).
          eva_pan_value = R1;
          eva_tilt_value = D1;
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else if (parametro2 == '2'){ // movimento para posição 2 do quadrante 3.  (movimento em duas dimensões).
          eva_pan_value = R2;
          eva_tilt_value = D1;
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else if (parametro2 == '3'){ // movimento para posição 2 do quadrante 3.  (movimento em duas dimensões).
          eva_pan_value = R3;
          eva_tilt_value = D2;
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
      }
      else if (parametro1 == 'c'){ // movimento para centralizar a cabeça em apenas um dos eixos.
        char parametro2 = Serial.read();
        delay(20);
        if (parametro2 == 'y'){ // centraliza no eixo y (tilt)
          eva_tilt_value = eva_tilt_center;
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
        else if (parametro2 == 'x'){ // centraliza no eixo x (pan)
          eva_pan_value = eva_pan_center;
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          delay(20);
        }
        else if (parametro2 == 'c'){ // centraliza nos dos eixos (igual ao comando 'c' do protocolo de 1 byte)
          eva_tilt_value = eva_tilt_center;
          eva_pan_value = eva_pan_center;
          ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity);
          ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - 30);
          delay(20);
        }
      }
    }
  }
}


///////////////////////////////////////////
// movimentos de shake dos braço do robô //
///////////////////////////////////////////
// braço direito (shake)  ////////////////////////////////////////////////////////////////////
void arm_right_shake(){
  int arm_shake_velocity = 20;
  int cycle_time = 600;
  // define os extremos para a oscilação do braço
  if (arm_right_state == '0'){ // se o braço está na posição 0 então ele vai oscilar (shake) entre as posições 0 e 1.
    arm_right_shake_start = arm_right_p0;
    arm_right_shake_end = arm_right_p1;
    arm_right_state = 's'; // faz com que a função shake seja chamada pelo loop principal.
    arm_right_servo.write(arm_right_shake_end, arm_shake_velocity);
    arm_right_shake_timer = millis();
  } 
  else if (arm_right_state == '1'){ // se o braço está na posição 1 então ele vai oscilar (shake) entre as posições 1 e 2.
    arm_right_shake_start = arm_right_p1;
    arm_right_shake_end = arm_right_p2;
    arm_right_state = 's'; // faz com que a função shake seja chamada pelo loop principal.
    arm_right_servo.write(arm_right_shake_end, arm_shake_velocity);
    arm_right_shake_timer = millis();
  }
   else if (arm_right_state == '2'){ // se o braço está na posição 2 então ele vai oscilar (shake) entre as posições 2 e 3.
    arm_right_shake_start = arm_right_p2;
    arm_right_shake_end = arm_right_p3;
    arm_right_state = 's'; // faz com que a função shake seja chamada pelo loop principal.
    arm_right_servo.write(arm_right_shake_end, arm_shake_velocity);
    arm_right_shake_timer = millis();
  }
  else if (arm_right_state == '3'){ // se o braço está na posição 3 então ele vai oscilar (shake) entre as posições 3 e 2.
    arm_right_shake_start = arm_right_p3;
    arm_right_shake_end = arm_right_p2;
    arm_right_state = 's'; // faz com que a função shake seja chamada pelo loop principal.
    arm_right_servo.write(arm_right_shake_end, arm_shake_velocity);
    arm_right_shake_timer = millis();
  }
  //////////////////////////////////////////////////////////////////////////////////////////////////////
  if (arm_right_shake_repetitions == 1) {
    /////// inicio da movimentação baseado no timer (repetições = 1, apenas um ciclo) //////////////////
    if (arm_right_shake_state == '0'){
      if ((millis() - arm_right_shake_timer) > cycle_time){
        arm_right_shake_state = '1';
        arm_right_servo.write(arm_right_shake_start, arm_shake_velocity);
        arm_right_shake_timer = millis();
      }
    }
    else if (arm_right_shake_state == '1'){
      if ((millis() - arm_right_shake_timer) > cycle_time){
        arm_right_shake_state = 'f';
        arm_right_servo.write(arm_right_shake_end, arm_shake_velocity);
        arm_right_shake_timer = millis();
      }
    }
    else if (arm_right_shake_state == 'f'){ // estado final do shake
      if ((millis() - arm_right_shake_timer) > cycle_time){
        arm_right_servo.write(arm_right_shake_start, arm_shake_velocity);
        if (arm_right_shake_start == arm_right_p0){ // encerra a chamada à função shake pelo loop principal siando do estado 's' e voltando para o estado incial, antes do shake.
          arm_right_state = '0';
        }
        else if (arm_right_shake_start == arm_right_p1){
          arm_right_state = '1';
        }
        else if (arm_right_shake_start == arm_right_p2){
          arm_right_state = '2';
        }
        else if (arm_right_shake_start == arm_right_p3){
          arm_right_state = '3';
        }
        arm_right_shake_state = '0'; // permite uma nova inicialização da função arm_shake.
      }
    }
  }
  ///////////////////////////////////////////////////////////////////////////////////////////
  else if (arm_right_shake_repetitions == 2) {
    /////// inicio da movimentação baseado no timer (repetições = 2, são executados dois ciclos) //////////////////
    if (arm_right_shake_state == '0'){
      if ((millis() - arm_right_shake_timer) > cycle_time){
        arm_right_shake_state = '1';
        arm_right_servo.write(arm_right_shake_start, arm_shake_velocity);
        arm_right_shake_timer = millis();
      }
    }
    else if (arm_right_shake_state == '1'){
      if ((millis() - arm_right_shake_timer) > cycle_time){
        arm_right_shake_state = '2';
        arm_right_servo.write(arm_right_shake_end, arm_shake_velocity);
        arm_right_shake_timer = millis();
      }
    }
    if (arm_right_shake_state == '2'){
      if ((millis() - arm_right_shake_timer) > cycle_time){
        arm_right_shake_state = '3';
        arm_right_servo.write(arm_right_shake_start, arm_shake_velocity);
        arm_right_shake_timer = millis();
      }
    }
    else if (arm_right_shake_state == '3'){
      if ((millis() - arm_right_shake_timer) > cycle_time){
        arm_right_shake_state = '4';
        arm_right_servo.write(arm_right_shake_end, arm_shake_velocity);
        arm_right_shake_timer = millis();
      }
    }
    if (arm_right_shake_state == '4'){
      if ((millis() - arm_right_shake_timer) > cycle_time){
        arm_right_shake_state = '5';
        arm_right_servo.write(arm_right_shake_start, arm_shake_velocity);
        arm_right_shake_timer = millis();
      }
    }
    else if (arm_right_shake_state == '5'){
      if ((millis() - arm_right_shake_timer) > cycle_time){
        arm_right_shake_state = '6';
        arm_right_servo.write(arm_right_shake_end, arm_shake_velocity);
        arm_right_shake_timer = millis();
      }
    }
    if (arm_right_shake_state == '6'){
      if ((millis() - arm_right_shake_timer) > cycle_time){
        arm_right_shake_state = 'f';
        arm_right_servo.write(arm_right_shake_start, arm_shake_velocity);
        arm_right_shake_timer = millis();
      }
    }
    else if (arm_right_shake_state == 'f'){ // estado final do shake
      if ((millis() - arm_right_shake_timer) > cycle_time){
        arm_right_servo.write(arm_right_shake_start, arm_shake_velocity);
        if (arm_right_shake_start == arm_right_p0){ // encerra a chamada à função shake pelo loop principal siando do estado 's' e voltando para o estado incial, antes do shake.
          arm_right_state = '0';
        }
        else if (arm_right_shake_start == arm_right_p1){
          arm_right_state = '1';
        }
        else if (arm_right_shake_start == arm_right_p2){
          arm_right_state = '2';
        }
        else if (arm_right_shake_start == arm_right_p3){
          arm_right_state = '3';
        }
        arm_right_shake_state = '0'; // permite uma nova inicialização da função arm_shake.
      }
    }
  }
}


// braço direito (shake) ////////////////////////////////////////////////////////////////////
void arm_left_shake(){
  int arm_shake_velocity = 20;
  int cycle_time = 600;
  // define os extremos para a oscilação do braço
  if (arm_left_state == '0'){ // se o braço está na posição 0 então ele vai oscilar (shake) entre as posições 0 e 1.
    arm_left_shake_start = arm_left_p0;
    arm_left_shake_end = arm_left_p1;
    arm_left_state = 's'; // faz com que a função shake seja chamada pelo loop principal.
    arm_left_servo.write(arm_left_shake_end, arm_shake_velocity);
    arm_left_shake_timer = millis();
  } 
  else if (arm_left_state == '1'){ // se o braço está na posição 1 então ele vai oscilar (shake) entre as posições 1 e 2.
    arm_left_shake_start = arm_left_p1;
    arm_left_shake_end = arm_left_p2;
    arm_left_state = 's'; // faz com que a função shake seja chamada pelo loop principal.
    arm_left_servo.write(arm_left_shake_end, arm_shake_velocity);
    arm_left_shake_timer = millis();
  }
   else if (arm_left_state == '2'){ // se o braço está na posição 2 então ele vai oscilar (shake) entre as posições 2 e 3.
    arm_left_shake_start = arm_left_p2;
    arm_left_shake_end = arm_left_p3;
    arm_left_state = 's'; // faz com que a função shake seja chamada pelo loop principal.
    arm_left_servo.write(arm_left_shake_end, arm_shake_velocity);
    arm_left_shake_timer = millis();
  }
  else if (arm_left_state == '3'){ // se o braço está na posição 3 então ele vai oscilar (shake) entre as posições 3 e 2.
    arm_left_shake_start = arm_left_p3;
    arm_left_shake_end = arm_left_p2;
    arm_left_state = 's'; // faz com que a função shake seja chamada pelo loop principal.
    arm_left_servo.write(arm_left_shake_end, arm_shake_velocity);
    arm_left_shake_timer = millis();
  }
  //////////////////////////////////////////////////////////////////////////////////////////////////////
  if (arm_left_shake_repetitions == 1) {
    /////// inicio da movimentação baseado no timer (repetições = 1, apenas um ciclo) //////////////////
    if (arm_left_shake_state == '0'){
      if ((millis() - arm_left_shake_timer) > cycle_time){
        arm_left_shake_state = '1';
        arm_left_servo.write(arm_left_shake_start, arm_shake_velocity);
        arm_left_shake_timer = millis();
      }
    }
    else if (arm_left_shake_state == '1'){
      if ((millis() - arm_left_shake_timer) > cycle_time){
        arm_left_shake_state = 'f';
        arm_left_servo.write(arm_left_shake_end, arm_shake_velocity);
        arm_left_shake_timer = millis();
      }
    }
    else if (arm_left_shake_state == 'f'){ // estado final do shake
      if ((millis() - arm_left_shake_timer) > cycle_time){
        arm_left_servo.write(arm_left_shake_start, arm_shake_velocity);
        if (arm_left_shake_start == arm_left_p0){ // encerra a chamada à função shake pelo loop principal siando do estado 's' e voltando para o estado incial, antes do shake.
          arm_left_state = '0';
        }
        else if (arm_left_shake_start == arm_left_p1){
          arm_left_state = '1';
        }
        else if (arm_left_shake_start == arm_left_p2){
          arm_left_state = '2';
        }
        else if (arm_left_shake_start == arm_left_p3){
          arm_left_state = '3';
        }
        arm_left_shake_state = '0'; // permite uma nova inicialização da função arm_shake.
      }
    }
  }
  ///////////////////////////////////////////////////////////////////////////////////////////
  else if (arm_left_shake_repetitions == 2) {
    /////// inicio da movimentação baseado no timer (repetições = 2, são executados dois ciclos) //////////////////
    if (arm_left_shake_state == '0'){
      if ((millis() - arm_left_shake_timer) > cycle_time){
        arm_left_shake_state = '1';
        arm_left_servo.write(arm_left_shake_start, arm_shake_velocity);
        arm_left_shake_timer = millis();
      }
    }
    else if (arm_left_shake_state == '1'){
      if ((millis() - arm_left_shake_timer) > cycle_time){
        arm_left_shake_state = '2';
        arm_left_servo.write(arm_left_shake_end, arm_shake_velocity);
        arm_left_shake_timer = millis();
      }
    }
    if (arm_left_shake_state == '2'){
      if ((millis() - arm_left_shake_timer) > cycle_time){
        arm_left_shake_state = '3';
        arm_left_servo.write(arm_left_shake_start, arm_shake_velocity);
        arm_left_shake_timer = millis();
      }
    }
    else if (arm_left_shake_state == '3'){
      if ((millis() - arm_left_shake_timer) > cycle_time){
        arm_left_shake_state = '4';
        arm_left_servo.write(arm_left_shake_end, arm_shake_velocity);
        arm_left_shake_timer = millis();
      }
    }
    if (arm_left_shake_state == '4'){
      if ((millis() - arm_left_shake_timer) > cycle_time){
        arm_left_shake_state = '5';
        arm_left_servo.write(arm_left_shake_start, arm_shake_velocity);
        arm_left_shake_timer = millis();
      }
    }
    else if (arm_left_shake_state == '5'){
      if ((millis() - arm_left_shake_timer) > cycle_time){
        arm_left_shake_state = '6';
        arm_left_servo.write(arm_left_shake_end, arm_shake_velocity);
        arm_left_shake_timer = millis();
      }
    }
    if (arm_left_shake_state == '6'){
      if ((millis() - arm_left_shake_timer) > cycle_time){
        arm_left_shake_state = 'f';
        arm_left_servo.write(arm_left_shake_start, arm_shake_velocity);
        arm_left_shake_timer = millis();
      }
    }
    else if (arm_left_shake_state == 'f'){ // estado final do shake
      if ((millis() - arm_left_shake_timer) > cycle_time){
        arm_left_servo.write(arm_left_shake_start, arm_shake_velocity);
        if (arm_left_shake_start == arm_left_p0){ // encerra a chamada à função shake pelo loop principal siando do estado 's' e voltando para o estado incial, antes do shake.
          arm_left_state = '0';
        }
        else if (arm_left_shake_start == arm_left_p1){
          arm_left_state = '1';
        }
        else if (arm_left_shake_start == arm_left_p2){
          arm_left_state = '2';
        }
        else if (arm_left_shake_start == arm_left_p3){
          arm_left_state = '3';
        }
        arm_left_shake_state = '0'; // permite uma nova inicialização da função arm_shake.
      }
    }
  }
}

////////////////////////////////////////////////////////////////////////////////////////////
//             Funções de controle para a movimentação da cabeça do robô EVA              //
////////////////////////////////////////////////////////////////////////////////////////////
//////////////// função utilizada para centralizar a cabeça durante a inicialização. ///////
void head_init (){ // centraliza a cabeça
  ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_center, eva_velocity - 15);
  ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_center, eva_velocity - 25);
  delay(20);
}

///////////////// função que testa os limites de movimentação da cabeça do robô.
bool head_test_limits(int _eva_tilt_value, int _eva_pan_value){
  if ((_eva_tilt_value <= eva_tilt_up_limit) && (_eva_tilt_value >= eva_tilt_down_limit) && (_eva_pan_value <= eva_pan_left_limit) && (_eva_pan_value >= eva_pan_right_limit)){
    return true;
  }
  else {
    Serial.println("");
    Serial.println("Movimento fora do limite permitido.");
    return false;
  }
}
//////////////////////////////////////////////////////////////////////////////////


//////////////////////////////////////////////////////////////////
// movimentos NO (Shake) e YES (NOD) implementados usando timer //
//////////////////////////////////////////////////////////////////
////////////////////////// SHAKE //////////////////////////////////////////////////////////////
void head_shake(){ // sacode a cabeça como se dissese um "não".
  int shake_amplitude = 30; // se aumentar a amplitude será necessário aumentar o intervalo de tempo cycle_time;
  int cycle_time = 800;
  int velocity_adjust = 10;
  if (head_shake_repetitions == 1){
    if (head_shake_state == '0'){ // estado 0, inicializa o relógio de execução da função shake().
      head_shake_state = '1';
      eva_pan_value -= shake_amplitude; // movimento para a direita.
      ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity - velocity_adjust);
      delay(20);
    }
    else if (head_shake_state == '1'){ // estado 1, movimento para a direita.
      if ((millis() - head_timer) > (cycle_time / 2)){
        head_shake_state = '2';
        head_timer = millis();
        eva_pan_value += (shake_amplitude * 2); // movimento para a esquerda.
        ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity - velocity_adjust); 
        delay(20);
      }
    }
    else if (head_shake_state == '2'){ // estado 2, movimento para a esquerda.
      if ((millis() - head_timer) > cycle_time){
        head_shake_state = '3';
        head_timer = millis();
        eva_pan_value -= (shake_amplitude * 2); // movimento para a direita.
        ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity - velocity_adjust); 
        delay(20);
      }
    }
    else if (head_shake_state == '3'){ // estado 2, movimento para a esquerda.
      if ((millis() - head_timer) > cycle_time){
        head_shake_state = 'f';
        head_timer = millis();
        eva_pan_value += shake_amplitude; // movimento para a direita.
        ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity - velocity_adjust); 
        delay(20);
      }
    }
    else if (head_shake_state == 'f'){ // estado 2, movimento para a esquerda.
      if ((millis() - head_timer) > (cycle_time / 2)){
        head_shake_state = '0';
        head_state = 'i'; // muda para o estado idle 'i' para o shake.
      }
    }
  }
  else { // duas repetições do shake()
    if (head_shake_state == '0'){ // estado 0, inicializa o relógio de execução da função shake().
      head_shake_state = '1';
      eva_pan_value -= shake_amplitude; // movimento para a direita.
      ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity - velocity_adjust);
      delay(20);
    }
    else if (head_shake_state == '1'){ // estado 1, movimento para a direita.
      if ((millis() - head_timer) > (cycle_time / 2)){
        head_shake_state = '2';
        head_timer = millis();
        eva_pan_value += (shake_amplitude * 2); // movimento para a esquerda.
        ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity - velocity_adjust); 
        delay(20);
      }
    }
    else if (head_shake_state == '2'){ // estado 2, movimento para a esquerda.
      if ((millis() - head_timer) > cycle_time){
        head_shake_state = '3';
        head_timer = millis();
        eva_pan_value -= (shake_amplitude * 2); // movimento para a direita.
        ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity - velocity_adjust); 
        delay(20);
      }
    }
    else if (head_shake_state == '3'){ // estado 3, movimento para a direita.
      if ((millis() - head_timer) > cycle_time){
        head_shake_state = '4';
        head_timer = millis();
        eva_pan_value += (shake_amplitude * 2); // movimento para a esquerda.
        ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity - velocity_adjust); 
        delay(20);
      }
    }
    else if (head_shake_state == '4'){ // estado 4, movimento para a esquerda.
      if ((millis() - head_timer) > cycle_time){
        head_shake_state = '5';
        head_timer = millis();
        eva_pan_value -= (shake_amplitude * 2); // movimento para a direita.
        ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity - velocity_adjust); 
        delay(20);
      }
    }
    else if (head_shake_state == '5'){ // estado 5, movimento para a direita.
      if ((millis() - head_timer) > cycle_time){
        head_shake_state = '6';
        head_timer = millis();
        eva_pan_value += (shake_amplitude * 2); // movimento para a esquerda.
        ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity - velocity_adjust); 
        delay(20);
      }
    }
    else if (head_shake_state == '6'){ // estado 6, movimento para a esquerda.
      if ((millis() - head_timer) > cycle_time){
        head_shake_state = '7';
        head_timer = millis();
        eva_pan_value -= (shake_amplitude * 2); // movimento para a direita.
        ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity - velocity_adjust); 
        delay(20);
      }
    }
    else if (head_shake_state == '7'){ // estado 7, movimento para a direita.
      if ((millis() - head_timer) > cycle_time){
        head_shake_state = 'f';
        head_timer = millis();
        eva_pan_value += shake_amplitude; // movimento para a esquerda.
        ax12a.moveSpeed(EVA_PAN_SERVO_ID, eva_pan_value, eva_velocity - velocity_adjust); 
        delay(20);
      }
    }
    ////// fim
    else if (head_shake_state == 'f'){ // estado 10, movimento para a esquerda e finaliza.
      if ((millis() - head_timer) > (cycle_time / 2)){
        head_shake_state = '0';
        head_state = 'i'; // muda para o estado idle 'i' para o shake.
      }
    }
  }
}  


//////////////////////// NOD ///////////////////////////////////////////////////////////
void head_nod(){ // sacode a cabeça como se dissese um "sim".
  int nod_amplitude = 30; // se aumentar a amplitude será necessário aumentar o intervalo de tempo cycle_time;
  int cycle_time = 700;
  int velocity_adjust = 30;
  if (nod_repetitions == 1){
    if (head_nod_state == '0'){ // estado 0, inicializa o relógio de execução da função nod().
      head_nod_state = '1';
      eva_tilt_value -= nod_amplitude; // movimento para baixo.
      ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - velocity_adjust);
      delay(20);
    }
    else if (head_nod_state == '1'){ // estado 1, movimento para baixo.
      if ((millis() - head_timer) > cycle_time){
        head_nod_state = '2';
        head_timer = millis();
        eva_tilt_value += nod_amplitude; // movimento para cima.
        ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - velocity_adjust); 
        delay(20);
      }
    }
    else if (head_nod_state == '2'){ // estado 2, movimento para cima.
      if ((millis() - head_timer) > cycle_time){
        head_nod_state = '3';
        head_timer = millis();
        eva_tilt_value -= nod_amplitude; // movimento para baixo.
        ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - velocity_adjust); 
        delay(20);
      }
    }
    else if (head_nod_state == '3'){ // estado 2, movimento para baixo.
      if ((millis() - head_timer) > cycle_time){
        head_nod_state = 'f';
        head_timer = millis();
        eva_tilt_value += nod_amplitude; // movimento para cima.
        ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - velocity_adjust); 
        delay(20);
      }
    }
    else if (head_nod_state == 'f'){ // // estado f, finaliza o movimento.
      if ((millis() - head_timer) > cycle_time){
        head_nod_state = '0';
        head_state = 'i'; // muda para o estado idle 'i'.
      }
    }
  }
  ////////////////////////////
  else { // duas repetições do nod()
    if (head_nod_state == '0'){ // estado 0, inicializa o relógio de execução da função shake().
      head_nod_state = '1';
      eva_tilt_value -= nod_amplitude; // movimento para a baixo.
      ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value,  eva_velocity - velocity_adjust);
      delay(20);
    }
    else if (head_nod_state == '1'){ // estado 1, movimento para a baixo.
      if ((millis() - head_timer) > cycle_time){
        head_nod_state = '2';
        head_timer = millis();
        eva_tilt_value += nod_amplitude; // movimento para cima.
        ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value,  eva_velocity - velocity_adjust); 
        delay(20);
      }
    }
    else if (head_nod_state == '2'){ // estado 2, movimento para cima.
      if ((millis() - head_timer) > cycle_time){
        head_nod_state = '3';
        head_timer = millis();
        eva_tilt_value -= nod_amplitude; // movimento para baixo.
        ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value,  eva_velocity - velocity_adjust); 
        delay(20);
      }
    }
    else if (head_nod_state == '3'){ // estado 3, movimento para baixo.
      if ((millis() - head_timer) > cycle_time){
        head_nod_state = '4';
        head_timer = millis();
        eva_tilt_value += nod_amplitude; // movimento para cima.
        ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value,  eva_velocity - velocity_adjust); 
        delay(20);
      }
    }
    else if (head_nod_state == '4'){ // estado 4, movimento para cima.
      if ((millis() - head_timer) > cycle_time){
        head_nod_state = '5';
        head_timer = millis();
        eva_tilt_value -= nod_amplitude; // movimento para baixo.
        ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value,  eva_velocity - velocity_adjust); 
        delay(20);
      }
    }
    else if (head_nod_state == '5'){ // estado 5, movimento para baixo.
      if ((millis() - head_timer) > cycle_time){
        head_nod_state = '6';
        head_timer = millis();
        eva_tilt_value += nod_amplitude; // movimento para cima.
        ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value,  eva_velocity - velocity_adjust); 
        delay(20);
      }
    }
    else if (head_nod_state == '6'){ // estado 6, movimento para cima.
      if ((millis() - head_timer) > cycle_time){
        head_nod_state = '7';
        head_timer = millis();
        eva_tilt_value -= nod_amplitude; // movimento para baixo.
        ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value,  eva_velocity - velocity_adjust); 
        delay(20);
      }
    }
    else if (head_nod_state == '7'){ // estado 7, movimento para baixo.
      if ((millis() - head_timer) > cycle_time){
        head_nod_state = 'f';
        head_timer = millis();
        eva_tilt_value += nod_amplitude; // movimento para cima.
        ax12a.moveSpeed(EVA_TILT_SERVO_ID, eva_tilt_value, eva_velocity - velocity_adjust); 
        delay(20);
      }
    }
    ////// fim
    else if (head_nod_state == 'f'){ // estado f, finaliza o movimento.
      if ((millis() - head_timer) > cycle_time){
        head_nod_state = '0';
        head_state = 'i'; // muda para o estado idle 'i' para o shake.
      }
    }
  }
}


