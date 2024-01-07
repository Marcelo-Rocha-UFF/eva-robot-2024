import cv2
import serial


classificador = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
camera = cv2.VideoCapture(2)

iddle_time_limit = 100
iddle_time = iddle_time_limit
x_center = 320
y_center = 240
x_range = 50
y_range = 60

web_serial_port = '/dev/ttyACM0'
baud_rate = '1000000'
web_cam = serial.Serial(web_serial_port, baud_rate)

t_angle = 90
p_angle = 90
t_angle_bkp = 90
p_angle_bkp = 90
web_cam_velocity_x = 1
web_cam_velocity_y = 1
eva_follow = True

def center_webcam():
    # centraliza a webcam
    global t_angle, p_angle
    t_angle = 90
    p_angle = 90
    web_cam.write(("t" + chr(t_angle)).encode())
    web_cam.write(("p" + chr(p_angle)).encode())
    if eva_follow:
        web_cam.write('c'.encode())


def is_x_center(x, l) -> bool:
    x_left = x_center - x_range
    x_right = x_center + x_range
    rect_center = x + (l / 2)
    if (rect_center >= x_left) and (rect_center <= x_right):
        return True
    else:
        return False


def is_y_center(y, a) -> bool:
    y_up = y_center - y_range
    y_down = y_center + y_range
    rect_center = y + (a / 2)
    if (rect_center >= y_up) and (rect_center <= y_down):
        return True
    else:
        return False


center_webcam() # Centraliza a camera

while True:
    iddle_time -= 1
    conectado, imagem = camera.read()
    imagemCinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    facesDetectadas = classificador.detectMultiScale(imagemCinza)
    for (x, y, l, a) in facesDetectadas:
        if (l > 200) and (l < 300): # processa somente faces dentro dos limites 170, 27
            iddle_time = iddle_time_limit
            cv2.rectangle(imagem, (x, y), (x + l, y + a), (0, 255, 0), 1)
            if not is_x_center(x, l):
                if x_center - (x + l/2) > 0:
                    p_angle += web_cam_velocity_x
                    web_cam.write(("p" + chr(p_angle)).encode())
                else:
                    p_angle -= web_cam_velocity_x
                    web_cam.write(("p" + chr(p_angle)).encode())

            if not is_y_center(y, a):
                if y_center - (y + a/2) > 0:
                    t_angle -= web_cam_velocity_y
                    web_cam.write(("t" + chr(t_angle)).encode())
                else:
                    t_angle += web_cam_velocity_y
                    web_cam.write(("t" + chr(t_angle)).encode())

            if eva_follow: # COntrola a cabeça do EVA
                if (is_x_center(x, l) and is_y_center(y, a)):
                    if (t_angle != t_angle_bkp):
                        web_cam.write(("#t" + chr(t_angle)).encode())
                        t_angle_bkp = t_angle
                        print("t_angle:", t_angle, t_angle * 5.75)
                        print("p_angle:", p_angle, p_angle * 5.68)

                    if (p_angle != p_angle_bkp):
                        web_cam.write(("#p" + chr(p_angle)).encode())
                        p_angle_bkp = p_angle
                        print("t_angle:", t_angle, t_angle * 5.75)
                        print("p_angle:", p_angle, p_angle * 5.68)

    
    cv2.imshow("Face", imagem)
    cv2.waitKey(1)


    if iddle_time == 0:
        center_webcam()
        iddle_time = iddle_time_limit

camera.release()

cv2.destroyAllWindows()
