from paho.mqtt import client as mqtt_client

from tkinter import *
from tkinter import filedialog as fd

import sys

sys.path.append('/home/marcelo/Insync/marcelo_rocha@midiacom.uff.br/Google Drive/UFF Doutorado MidiaCom/eva-robot-2024/evaml-evasim-sourcecode/version2.0/evasim_refatorado')

import platform 

import config  # Module with network device configurations.

# Select the GUI definition file for the host operating system
if platform.system() == "Linux":
    print("Linux platform identified. Loading GUI formatting for Linux.")
    import gui_sim_eva_robot_linux as gui_sim_eva_robot # Definition of the graphical user interface (Linux)
    audio_ext = ".mp3" # Audio extension used by the audio library on Linux
    ibm_audio_ext = "audio/mp3" # Audio extension used to generate watson audios
elif platform.system() == "Windows":
    # This version of the Graphical User Interface (GUI) has been discontinued.
    print("Windows platform identified. Loading GUI formatting for Windows.")
    print("This version of the Graphical User Interface (GUI) has been discontinued. Sorry!")
    exit(1)
    # import gui_windows as EvaSIM_gui # definition of the graphical user interface (Windows) [This file is outdated and has been discontinued]
    # audio_ext = ".wav"
    # ibm_audio_ext = "audio/wav"
else:
    print("Sorry, the current OS is not supported by EvaSIM.") # Incompatible OS
    exit(1)

# Create the Tkinter window
window = Tk()

gui = gui_sim_eva_robot.Gui(window) # Instance of the Gui class within the graphical user interface definition module

font1 = gui.font1 # Sse the same font defined in the GUI module


broker = config.MQTT_BROKER_ADRESS # Broker address.
port = config.MQTT_PORT # Broker Port.
topic_base = config.SIMULATOR_TOPIC_BASE


# Position for graphical elements
eye_x_pos = 216
eye_y_pos = 259
matrix_x_pos = 215
matrix_y_pos = 447


# MQTT
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    # Subscribing in on_connect() means that if we lose the connection and
    # Reconnect then subscriptions will be renewed.
    client.subscribe(topic=[(topic_base + '/evaEmotion', 1), ])
    client.subscribe(topic=[(topic_base + '/leds', 1), ])
    print("SIM - Display Module - Connected.")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    if msg.topic == topic_base + '/evaEmotion':
        # client.publish(topic_base + '/log', "EVA's facial expression: " + msg.payload.decode()) 
        if msg.payload.decode() == "NEUTRAL":
            gui.canvas.create_image(eye_x_pos, eye_y_pos, image = gui.im_eyes_neutral)
        elif msg.payload.decode() == "HAPPY":
            gui.canvas.create_image(eye_x_pos, eye_y_pos, image = gui.im_eyes_happy)
        elif msg.payload.decode() == "ANGRY":
            gui.canvas.create_image(eye_x_pos, eye_y_pos, image = gui.im_eyes_angry)
        elif msg.payload.decode() == "SAD":
            gui.canvas.create_image(eye_x_pos, eye_y_pos, image = gui.im_eyes_sad)
        elif msg.payload.decode() == "FEAR":
            gui.canvas.create_image(eye_x_pos, eye_y_pos, image = gui.im_eyes_fear)
        elif msg.payload.decode() == "SURPRISE":
            gui.canvas.create_image(eye_x_pos, eye_y_pos, image = gui.im_eyes_surprise)
        elif msg.payload.decode() == "DISGUST":
            gui.canvas.create_image(eye_x_pos, eye_y_pos, image = gui.im_eyes_disgust)
        elif msg.payload.decode() == "INLOVE":
            gui.canvas.create_image(eye_x_pos, eye_y_pos, image = gui.im_eyes_inlove)

    elif msg.topic == topic_base + '/leds':
        # client.publish(topic_base + '/log', "EVA's facial expression: " + msg.payload.decode()) 
        if msg.payload.decode() == "STOP":
            gui.canvas.create_image(matrix_x_pos, matrix_y_pos, image = gui.im_matrix_grey)
        elif msg.payload.decode() == "LISTEN":
            gui.canvas.create_image(matrix_x_pos, matrix_y_pos, image = gui.im_matrix_green)
        elif msg.payload.decode() == "SPEAK":
            gui.canvas.create_image(matrix_x_pos, matrix_y_pos, image = gui.im_matrix_blue)
        elif (msg.payload.decode() == "ANGRY" or msg.payload.decode() == "ANGRY2"):
            gui.canvas.create_image(matrix_x_pos, matrix_y_pos, image = gui.im_matrix_red)
        elif msg.payload.decode() == "HAPPY":
            gui.canvas.create_image(matrix_x_pos, matrix_y_pos, image = gui.im_matrix_green)
        elif msg.payload.decode() == "SAD":
            gui.canvas.create_image(matrix_x_pos, matrix_y_pos, image = gui.im_matrix_blue)
        elif msg.payload.decode() == "SURPRISE":
            gui.canvas.create_image(matrix_x_pos, matrix_y_pos, image = gui.im_matrix_yellow)
        elif msg.payload.decode() == "WHITE":
            gui.canvas.create_image(matrix_x_pos, matrix_y_pos, image = gui.im_matrix_white)
        elif msg.payload.decode() == "RAINBOW":
            gui.canvas.create_image(matrix_x_pos, matrix_y_pos, image = gui.im_matrix_white)
        else:
            print("A wrong led animation was selected.")


# Run the MQTT client thread.
client = mqtt_client.Client()
client.on_connect = on_connect
client.on_message = on_message
try:
    client.connect(broker, port)
except:
    print ("Unable to connect to Broker.")
    exit(1)

# You cannot use the "forever" method (as in other modules) because it blocks not allowing
# for the graphical interface thread loop to execute.
client.loop_start()

gui.canvas.create_image(eye_x_pos, eye_y_pos, image = gui.im_eyes_on)

gui.mainloop()