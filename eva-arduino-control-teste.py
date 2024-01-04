# Programa para testar os comandos pela porta serial do Arduino
# Podem ser enviados comandos para controlar a Webcam (Pan and Tilt). Exemplos: t60, p120, t90, p90 etc.
# Também aceita comandos para o controle da movimentação da cabeça do EVA, tipo: u, U, n, s etc.
# Os comandos para a movimentação dos braços ainda serão implementados no software do Arduino

import serial

web_serial_port = '/dev/ttyACM0'

baud_rate = '1000000' # Velocidade compatível com a dos servos AX12

web_cam = serial.Serial(web_serial_port, baud_rate)

# PAN -> Horizontal
# TILT -> Vertical

# Comando "t" Tilt
# vertical 40 (up) < 90 > 120 (down) esses são os limites.

# Comando "p" Pan 
# horizontal 55 (direita da cam) < 90 > 125 (parece ser o suficiente, mas pode ir mais para os dois lados)

while (True):
    print("Comando ('t' ou 'p' + angulo): ")

    c =  input()
    
    if len(c) > 1: # comando no formato para a webcam
        com_byte = c[0] + chr(int(c[1:]))

    else:
        com_byte = c: # comando no formato para os AX12

    print("com_byte: ", com_byte)

    web_cam.write(com_byte.encode())
