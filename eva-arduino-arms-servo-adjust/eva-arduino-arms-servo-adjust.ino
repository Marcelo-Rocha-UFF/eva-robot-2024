// #include <VarSpeedServo.h>
#include <Servo.h>

#define EVA_LEFT_ARM_SERVO_ID    8  // pino do braço esquerdo
#define EVA_RIGHT_ARM_SERVO_ID   9 // pino do braço direito

// VarSpeedServo left_arm; // Servo do braço esquerdo do robô
// VarSpeedServo right_arm; // Servo do braço direito do robô

Servo left_arm; // Servo do braço esquerdo do robô
Servo right_arm; // Servo do braço direito do robô

// Os valores mínimo e máximo de cada braço varia de acordo com o sentido do servo motor
int left_arm_init_pos = 170;
int left_arm_max_pos = 80; // era 10
int right_arm_init_pos = 40;
int right_arm_max_pos = 130; //era 170
int servo_center = 90;

int pause = 10;

void setup() {
  left_arm.attach(EVA_LEFT_ARM_SERVO_ID); // 
  right_arm.attach(EVA_RIGHT_ARM_SERVO_ID); // 
}

void loop() {

  for (int i=170; i>=60; i--){
    left_arm.write(i);
    delay(pause);
  }

  for (int i=40; i<=160; i++){
    right_arm.write(i);
    delay(pause);
  }

  for (int i=60; i<=170; i++){
    left_arm.write(i);
    delay(pause);
  }

  for (int i=160; i>=40; i--){
    right_arm.write(i);
    delay(pause);
  }


  


  
  // movimenta o braço esquerdo (Left) do robô para a posição inicial (170°), para o centro (90°) e para a posição máxima, (10°)
  // set_left_arm_init_pos();
  // delay(2000);
  // set_left_arm_center_pos();
  // delay(2000);
  // set_left_arm_max_pos();
  // delay(2000);

  // movimenta o braço direito (Right) do robô para a posição inicial (10°), para o centro (90°) e para a posição máxima, (170°)
  // set_right_arm_init_pos();
  // delay(2000);
  // set_right_arm_center_pos();
  // delay(2000);
  // set_right_arm_max_pos();
  // delay(2000);
}


void set_left_arm_init_pos(){
  left_arm.write(left_arm_init_pos);
  // left_arm.write(left_arm_init_pos, 50, true);
}


void set_left_arm_max_pos(){
  left_arm.write(left_arm_max_pos);
  // left_arm.write(left_arm_max_pos, 50, true);
}


void set_left_arm_center_pos(){
  left_arm.write(90);
  // left_arm.write(servo_center, 50, true);
}


void set_right_arm_init_pos(){
  right_arm.write(right_arm_init_pos);
  // right_arm.write(right_arm_init_pos, 50, true);
}


void set_right_arm_max_pos(){
  right_arm.write(right_arm_max_pos);
  // right_arm.write(right_arm_max_pos, 50, true);
}


void set_right_arm_center_pos(){
  right_arm.write(90);
  // right_arm.write(servo_center, 50, true);
}


