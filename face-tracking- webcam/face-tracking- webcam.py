import cv2
import serial
import time

classificador = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
camera = cv2.VideoCapture(0)

iddle_time = 0
x_center = 320
y_center = 240
x_range = 35
y_range = 35

web_serial_port = '/dev/ttyACM0'
baud_rate = '9600'
web_cam = serial.Serial(web_serial_port, baud_rate)

t_angle = 90
p_angle = 90
web_cam_velocity_x = 1
web_cam_velocity_y = 1


def center_webcam():
    # centraliza a webcam
    global t_angle, p_angle
    t_angle = 90
    p_angle = 90
    web_cam.write(("t" + chr(t_angle)).encode())
    web_cam.write(("p" + chr(p_angle)).encode())


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


center_webcam()

while True:
    print(iddle_time)
    iddle_time += 1
    conectado, imagem = camera.read()
    imagemCinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    facesDetectadas = classificador.detectMultiScale(imagemCinza)
    for (x, y, l, a) in facesDetectadas:
        if (l > 100) and (l < 500): # processa somente faces dentro dos limites 170, 27
            iddle_time = 0
            cv2.rectangle(imagem, (x, y), (x + l, y + a), (0, 255, 0), 1)
            if not is_x_center(x, l):
                if x_center - (x + l/2) > 0:
                    t_angle += web_cam_velocity_x
                    web_cam.write(("t" + chr(t_angle)).encode())
                else:
                    t_angle -= web_cam_velocity_x
                    web_cam.write(("t" + chr(t_angle)).encode())

            if not is_y_center(y, a):
                if y_center - (y + a/2) > 0:
                    p_angle -= web_cam_velocity_y
                    web_cam.write(("p" + chr(p_angle)).encode())
                else:
                    p_angle += web_cam_velocity_y
                    web_cam.write(("p" + chr(p_angle)).encode())
    
    cv2.imshow("Face", imagem)
    cv2.waitKey(1)


    if iddle_time > 60:
        center_webcam()
        iddle_time = 0

camera.release()

cv2.destryAllWindows()
