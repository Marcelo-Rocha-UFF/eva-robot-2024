#!/usr/bin/env python3
# EvaSIM 2.0 - Software Simulador para o robô EVA
# Software developed by Marcelo Marques da Rocha
# MidiaCom Laboratory - Universidade Federal Fluminense
# This work was funded by CAPES and Google Research

import platform 

import hashlib
import re
import os

import random as rnd
import xml.etree.ElementTree as ET

import eva_memory # EvaSIM memory module
import json_to_evaml_conv # json to XML conversion module (No longer used in this version of the simulator)

from tkinter import *
from tkinter import messagebox
from tkinter import filedialog as fd
import tkinter


# Adapter module for the audio library
# Depending on the OS it matters and defines a function called "playsound"
from play_audio import playsound

import time
import threading
import sys

import config # Module with the constants and parameters used in other modules.

TTS_IBM_WATSON = False # Define the use of IBM Watson service
ROBOT_MODE_ENABLED = False # 

if len(sys.argv) > 1: # Verify if is an argument in the command line
    for parameter in sys.argv[1:]: # Sweep all parameters
        if parameter.lower() == "tts=ibm-watson": # Watson was selected
            TTS_IBM_WATSON = True
        elif parameter.lower() == "robot-mode=on":
            ROBOT_MODE_ENABLED = True
        elif parameter.lower() == "h" or parameter.lower() == "-h" or parameter.lower() == "help" or parameter.lower() == "-help":
            print("\n############################################################")
            print("                   EvaSIM Help Information")
            print("############################################################")
            print("-help, help\tShow all available parameters.") 
            print("tts=ibm-watson\tUse the IBM Watson TTS service.") 
            print("robot-mode=on\tEnable robot mode control and execution.")
            print("############################################################\n")
            exit(1)
        else:
            print("\nSorry, I guess you entered an illegal parameter.")
            exit(1)
            
# Select the GUI definition file for the host operating system
if platform.system() == "Linux":
    print("\nLinux platform identified. Loading GUI formatting for Linux.\n")
    import gui_linux as EvaSIM_gui # Definition of the graphical user interface (Linux)
    audio_ext = ".mp3" # Audio extension used by the audio library on Linux
    ibm_audio_ext = "audio/mp3" # Audio extension used to generate watson audios
elif platform.system() == "Windows":
    # This version of the Graphical User Interface (GUI) has been discontinued.
    print("Windows platform identified. Loading GUI formatting for Windows.")
    print("This version of the Graphical User Interface (GUI) has been discontinued. Sorry!\n")
    exit(1)
else:
    print("Sorry, the current OS is not supported by EvaSIM.") # Incompatible OS
    exit(1)


broker = config.MQTT_BROKER_ADRESS # broker adress
port = config.MQTT_PORT # broker port
topic_base = config.EVA_TOPIC_BASE

EVA_ROBOT_STATE = "FREE"
EVA_DOLLAR = ""
RUNNING_MODE = "SIMULATOR" # EvaSIM operating mode (Physical Robot Simulator or Player)

log_seq_numbers = {} # It is used to define the order of the log texts sent.

# Watson library import and api key configuration
if TTS_IBM_WATSON: # Only if tts=ibm-watson option was selected in command line
    print("\n\nWARNING: You have chosen to use the IBM Watson Text-To-Speech service. To do this, you must have installed the Watson library for Python and you must also have, in the EvaSIM directory, the file (ibm_cred.txt) with the IBM service credentials.")
    print("\n\nPlease, press <ENTER> to continue or <ctrl> + c to stop.")
    input()

    from ibm_watson.text_to_speech_v1 import Voice
    from ibm_watson import TextToSpeechV1
    from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

    with open("ibm_cred.txt", "r") as ibm_cred:
        ibm_config = ibm_cred.read().splitlines()
    apikey = ibm_config[0]
    url = ibm_config[1]
    # Setup watson service
    authenticator = IAMAuthenticator(apikey)
    # TTS service
    tts = TextToSpeechV1(authenticator = authenticator)
    tts.set_service_url(url)


# import and config mqtt library and client
if ROBOT_MODE_ENABLED: # Only if robot-mode=on was selected in command line
    print("\n\nWARNING: You have chosen to use the Robot mode. To do this, you must have installed the paho.mqtt library and also install and configure the mosquitto broker.")
    print("\n\nPlease, press <ENTER> to continue or <ctrl> + c to stop.")
    input()
    from paho.mqtt import client as mqtt_client
    # MQTT
    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        # Subscribing in on_connect() means that if we lose the connection and
        # Reconnect then subscriptions will be renewed.
        client.subscribe(topic=[(topic_base + '/state', 1), ])
        client.subscribe(topic=[(topic_base + '/var/dollar', 1), ])
        client.subscribe(topic=[(topic_base + '/abort', 1), ])
        client.subscribe(topic=[(topic_base + '/terminal', 1), ])
        

    # The callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg):
        global EVA_ROBOT_STATE
        global EVA_DOLLAR
        if msg.topic == topic_base + '/state':
            EVA_ROBOT_STATE = "FREE" # unblock EvaSIM execution
        elif msg.topic == topic_base + '/var/dollar':
            EVA_DOLLAR = msg.payload.decode()
            EVA_ROBOT_STATE = "FREE" # unblock EvaSIM execution
        elif msg.topic == topic_base + '/abort': # topic used to abort the EvaSIM execution based on some external problem
            gui.terminal.insert(INSERT, "\nAborting -> Execution was aborted due to an external problem: " + msg.payload.decode(), "error") 
            gui.terminal.see(tkinter.END)
            stopScript(None)
        elif msg.topic == topic_base + '/terminal': # topic used to print external messages in EvaSIM terminal
            gui.terminal.insert(INSERT, "\nExternal message -> " + msg.payload.decode() + ".", "tip") 
            gui.terminal.see(tkinter.END)


    client = mqtt_client.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker, port)
    client.loop_start()

else: # User not selected the robot-mode=on in command line
    class Fake_Mqtt_Client(): # A fake mqtt class to work with mqtt commands
        def __init__(self):
            print("A fake mqtt client was created!")
        def publish(self, fake_topic, fake_message):
            print(f"A fake publish method with topic: {fake_topic} and message: {fake_message} is being executed.")
    client = Fake_Mqtt_Client()



# VM global variables
root = {}
script_node = {}
links_node = {}
fila_links =  [] # Link queue (commands)
thread_pop_pause = False
play = False # Play status of the script. This variable has an influence on the function. link_process
script_file = "" # Variable that stores the pointer to the xml script file on disk.

# Variable control function that blocks popups
def lock_thread_pop():
    global thread_pop_pause
    thread_pop_pause = True

def unlock_thread_pop():
    global thread_pop_pause
    thread_pop_pause = False


# Create the Tkinter window
window = Tk()
window.geometry("0x0+100+40")
gui = EvaSIM_gui.Gui(window) # Instance of the Gui class within the graphical user interface definition module

font1 = gui.font1 # Sse the same font defined in the GUI module

# EVA expressions images
im_eyes_neutral = PhotoImage(file = "images/eyes_neutral.png")
im_eyes_angry = PhotoImage(file = "images/eyes_angry.png")
im_eyes_sad = PhotoImage(file = "images/eyes_sad.png")
im_eyes_happy = PhotoImage(file = "images/eyes_happy.png")
im_eyes_fear = PhotoImage(file = "images/eyes_fear.png")
im_eyes_surprise = PhotoImage(file = "images/eyes_surprise.png")
im_eyes_disgust = PhotoImage(file = "images/eyes_disgust.png")
im_eyes_inlove = PhotoImage(file = "images/eyes_inlove.png")
im_eyes_on = PhotoImage(file = "images/eyes_on.png")

# Matrix Voice images
im_matrix_blue = PhotoImage(file = "images/matrix_blue.png")
im_matrix_green = PhotoImage(file = "images/matrix_green.png")
im_matrix_yellow = PhotoImage(file = "images/matrix_yellow.png")
im_matrix_white = PhotoImage(file = "images/matrix_white.png")
im_matrix_red = PhotoImage(file = "images/matrix_red.png")
im_matrix_grey = PhotoImage(file = "images/matrix_grey.png")
im_bt_play = PhotoImage(file = "images/bt_play.png")
im_bt_stop = PhotoImage(file = "images/bt_stop.png")


# Function to write memory data to the variable table
def tab_load_mem_vars():
    for i in gui.tab_vars.get_children(): # Clear table values
        gui.tab_vars.delete(i)

    for var_name in eva_memory.vars: # Read memory by inserting values ​​into the table
        gui.tab_vars.insert(parent='',index='end',text='', values=(var_name, eva_memory.vars[var_name]))


# Function to write memory data to the mem dollar table
def tab_load_mem_dollar():
    indice = 1 # Index for the dollar variable
    for i in gui.tab_dollar.get_children(): # Clear table values
        gui.tab_dollar.delete(i)

    for var_dollar in eva_memory.var_dolar: # Read memory by inserting values ​​into the table
        if indice == len(eva_memory.var_dolar):
            var_name = "$"
        else:
            var_name = "$" + str(indice)

        gui.tab_dollar.insert(parent='',index='end',text='', values=(var_name, var_dollar[0], var_dollar[1]))
        indice = indice + 1


# Eva initialization function
def evaInit():
    gui.bt_power['state'] = DISABLED
    gui.bt_power.unbind("<Button-1>")
    evaEmotion("POWER_ON")
    gui.terminal.insert(INSERT, "\nSTATE: Initializing.")
    gui.terminal.insert(INSERT, "\nSTATE: Entering in standby mode.")
    gui.bt_import['state'] = NORMAL
    gui.bt_import.bind("<Button-1>", importFileThread)
    gui.bt_reload['state'] = DISABLED
    gui.bt_reload.bind("<Button-1>", reloadFile)
    evaMatrix("white")
    while gui.bt_run_sim['state'] == DISABLED: # Matrix light animation on stand by
        evaMatrix("white")
        time.sleep(0.5)
        evaMatrix("grey")
        time.sleep(0.5)


# Eva powerOn function
def powerOn(self):
    threading.Thread(target=evaInit, args=()).start()


# Run in Simulator mode
def setSimMode(self):
    global RUNNING_MODE
    RUNNING_MODE = "SIMULATOR"
    runScript()


# Runs in EVA Robot Player mode
def setEVAMode(self):
    global RUNNING_MODE
    RUNNING_MODE = "EVA_ROBOT"
    runScript()

# Activate the thread that runs the script
def runScript():
    global play, fila_links, log_seq_numbers
    # initialize the robot memory
    print("Intializing the robot memory.")
    eva_memory.var_dolar = []
    eva_memory.vars = {}
    eva_memory.reg_case = 0
    # initialize the log seq numbers
    print("Intializing the log seq numbers.")
    log_seq_numbers = {}
    # Cleaning the tables
    print("Clearing memory map tables.")
    tab_load_mem_dollar()
    tab_load_mem_vars()
    # Initializing the memory of simulator
    fila_links =  []
    # Buttons states
    gui.bt_run_sim['state'] = DISABLED
    gui.bt_run_sim.unbind("<Button-1>")
    gui.bt_run_robot['state'] = DISABLED
    gui.bt_run_robot.unbind("<Button-1>")
    gui.bt_import['state'] = DISABLED
    gui.bt_reload['state'] = DISABLED
    gui.bt_stop['state'] = NORMAL
    gui.bt_stop.bind("<Button-1>", stopScript)
    gui.bt_import.unbind("<Button-1>")
    play = True # ativa a var do play do script
    root.find("settings").find("voice").attrib["key"]
    busca_links(root.find("settings").find("voice").attrib["key"]) # o primeiro elemento da interação é o voice
    threading.Thread(target=link_process, args=()).start()

# Activate the script play var
def stopScript(self):
    global play, EVA_ROBOT_STATE
    gui.bt_run_sim['state'] = NORMAL
    gui.bt_run_sim.bind("<Button-1>", setSimMode)
    if ROBOT_MODE_ENABLED: gui.bt_run_robot['state'] = NORMAL
    gui.bt_run_robot.bind("<Button-1>", setEVAMode)
    gui.bt_stop['state'] = DISABLED
    gui.bt_stop.unbind("<Button-1>")
    gui.bt_import['state'] = NORMAL
    gui.bt_reload['state'] = NORMAL
    gui.bt_import.bind("<Button-1>", importFileThread)
    play = False # desativa a var de play do script. Faz com que o script seja interrompido
    EVA_ROBOT_STATE = "FREE" # libera a execução, caso esteja executando algum comando bloqueante

# Import file thread
def importFileThread(self):
    threading.Thread(target=importFile, args=()).start()

# Eva Import Script function
def importFile():
    global root, script_node, links_node, script_file
    print("Importing a file.")
    # Now EvaSIM can read json
    filetypes = (('evaML files', '*.xml *.json'), )
    script_file = fd.askopenfile(mode = "r", title = 'Open an EvaML Script File', initialdir = './', filetypes = filetypes)
    # imagine that the guy will read a json or an xml
    if (re.findall(r'\.(xml|json|JSON|XML)', str(script_file)))[0].lower() == "json": # leitura de json
        print("Converting and running a JSON file.")
        # Script_file is not a string and still has information beyond the file path
        # So it needs to be processed before being passed to the conversion module
        json_to_evaml_conv.converte(str(script_file).split("'")[1], tkinter)
        script_file = "_json_to_evaml_converted.xml" # Json file converted to XML
    else: # Reading an XML
        print("Running a XML file.")
    # VM variables
    tree = ET.parse(script_file)  # XML code file
    root = tree.getroot() # EvaML root node
    script_node = root.find("script")
    links_node = root.find("links")
    gui.bt_run_sim['state'] = NORMAL
    gui.bt_run_sim.bind("<Button-1>", setSimMode)
    if ROBOT_MODE_ENABLED: gui.bt_run_robot['state'] = NORMAL
    gui.bt_run_robot.bind("<Button-1>", setEVAMode)
    gui.bt_stop['state'] = DISABLED
    gui.bt_reload['state'] = NORMAL
    evaEmotion("NEUTRAL")
    only_file_name = str(script_file).split("/")[-1].split("'")[0]
    window.title("Eva Simulator for EvaML - Version 2.0 - UFF / MidiaCom / CICESE -- [ " + only_file_name + " ]")
    gui.terminal.insert(INSERT, '\nSTATE: Script => ' + only_file_name + ' was LOADED.')
    gui.terminal.see(tkinter.END)

def reloadFile(self):
    global root, script_node, links_node, script_file
    script_file.seek(0) # Places the file object pointer at the beginning
    tree = ET.parse(script_file) # # XML code file
    root = tree.getroot() # EvaML root node
    script_node = root.find("script")
    links_node = root.find("links")
    evaEmotion("NEUTRAL")
    only_file_name = str(script_file).split("/")[-1].split("'")[0]
    gui.terminal.insert(INSERT, '\nSTATE: Script => ' + only_file_name + ' was RELOADED.')
    gui.terminal.see(tkinter.END)


def clear_terminal(self):
    gui.terminal.delete('1.0', END)
    # Creating terminal text
    gui.terminal.insert(INSERT, "=============================================================================================================================\n")
    gui.terminal.insert(INSERT, "                                                                                                                       Eva Simulator for EvaML\n")
    gui.terminal.insert(INSERT, "                                                                                                   Version 2.0 - UFF / MidiaCom / CICESE - [2024]\n")
    gui.terminal.insert(INSERT, "=============================================================================================================================")

# Connect callbacks to buttons
# The use of another module to define the GUI did not allow callbacks to be associated with buttons at the time of their creation
# Using the bind method to define callbacks has a limitation
# The element, even in the "disable" state, continues to respond to mouse click events
# Therefore, when disabling a button, it is necessary to use "unbind" to unbind the callback from the button
# If the button is placed in the "normal" state, the callback must be reset using "bind" again
gui.bt_power.bind("<Button-1>", powerOn)
gui.bt_clear.bind("<Button-1>", clear_terminal)


# WoZ light functions
def woz_light_blue(self):
    client.publish(topic_base + "/light", "BLUE|ON")
def woz_light_green(self):
    client.publish(topic_base + "/light", "GREEN|ON")
def woz_light_black(self):
    client.publish(topic_base + "/light", "BLACK|OFF")
def woz_light_pink(self):
    client.publish(topic_base + "/light", "PINK|ON")
def woz_light_red(self):
    client.publish(topic_base + "/light", "RED|ON")
def woz_light_yellow(self):
    client.publish(topic_base + "/light", "YELLOW|ON")
def woz_light_white(self):
    client.publish(topic_base + "/light", "WHITE|ON")



# WoZ light buttons binding
gui.bt_bulb_green_btn.bind("<Button-1>", woz_light_green)
gui.bt_bulb_blue_btn.bind("<Button-1>", woz_light_blue)
gui.bt_bulb_off_btn.bind("<Button-1>", woz_light_black)
gui.bt_bulb_pink_btn.bind("<Button-1>", woz_light_pink)
gui.bt_bulb_red_btn.bind("<Button-1>", woz_light_red)
gui.bt_bulb_yellow_btn.bind("<Button-1>", woz_light_yellow)
gui.bt_bulb_white_btn.bind("<Button-1>", woz_light_white)


# WoZ expressions functions
def woz_expression_angry(self):
    client.publish(topic_base + "/evaEmotion", "ANGRY")
def woz_expression_fear(self):
    client.publish(topic_base + "/evaEmotion", "FEAR")
def woz_expression_happy(self):
    client.publish(topic_base + "/evaEmotion", "HAPPY")
def woz_expression_neutral(self):
    client.publish(topic_base + "/evaEmotion", "NEUTRAL")
def woz_expression_sad(self):
    client.publish(topic_base + "/evaEmotion", "SAD")
def woz_expression_surprise(self):
    client.publish(topic_base + "/evaEmotion", "SURPRISE")
def woz_expression_disgust(self):
    client.publish(topic_base + "/evaEmotion", "DISGUST")
def woz_expression_inlove(self):
    client.publish(topic_base + "/evaEmotion", "INLOVE")


# WoZ expression buttons binding
gui.bt_exp_angry.bind("<Button-1>", woz_expression_angry)
gui.bt_exp_fear.bind("<Button-1>", woz_expression_fear)
gui.bt_exp_happy.bind("<Button-1>", woz_expression_happy)
gui.bt_exp_neutral.bind("<Button-1>", woz_expression_neutral)
gui.bt_exp_sad.bind("<Button-1>", woz_expression_sad)
gui.bt_exp_surprise.bind("<Button-1>", woz_expression_surprise)
gui.bt_exp_disgust.bind("<Button-1>", woz_expression_disgust)
gui.bt_exp_inlove.bind("<Button-1>", woz_expression_inlove)

# WoZ led functions
def woz_led_stop(self):
    client.publish(topic_base + '/syslog', "Leds Animation: " + "STOP") 
    client.publish(topic_base + "/leds", "STOP")
def woz_led_angry(self):
    client.publish(topic_base + "/leds", "STOP")
    client.publish(topic_base + "/leds", "ANGRY")
def woz_led_sad(self):
    client.publish(topic_base + "/leds", "STOP")
    client.publish(topic_base + "/leds", "SAD")
def woz_led_angry2(self):
    client.publish(topic_base + "/leds", "STOP")
    client.publish(topic_base + "/leds", "ANGRY2")
def woz_led_happy(self):
    client.publish(topic_base + "/leds", "STOP")
    client.publish(topic_base + "/leds", "HAPPY")
def woz_led_listen(self):
    client.publish(topic_base + "/leds", "STOP")
    client.publish(topic_base + "/leds", "LISTEN")
def woz_led_rainbow(self):
    client.publish(topic_base + "/leds", "STOP")
    client.publish(topic_base + "/leds", "RAINBOW")
def woz_led_speak(self):
    client.publish(topic_base + "/leds", "STOP")
    client.publish(topic_base + "/leds", "SPEAK")
def woz_led_surprise(self):
    client.publish(topic_base + "/leds", "STOP")
    client.publish(topic_base + "/leds", "SURPRISE")
def woz_led_white(self):
    client.publish(topic_base + "/leds", "STOP")
    client.publish(topic_base + "/leds", "WHITE")


# WoZ led buttons binding
gui.bt_led_stop.bind("<Button-1>", woz_led_stop)
gui.bt_led_angry.bind("<Button-1>", woz_led_angry)
gui.bt_led_sad.bind("<Button-1>", woz_led_sad)
gui.bt_led_angry2.bind("<Button-1>", woz_led_angry2)
gui.bt_led_happy.bind("<Button-1>", woz_led_happy)
gui.bt_led_listen.bind("<Button-1>", woz_led_listen)
gui.bt_led_rainbow.bind("<Button-1>", woz_led_rainbow)
gui.bt_led_speak.bind("<Button-1>", woz_led_speak)
gui.bt_led_surprise.bind("<Button-1>", woz_led_surprise)
gui.bt_led_white.bind("<Button-1>", woz_led_white)


# WoZ head motion functions
def woz_head_motion_yes(self):
    client.publish(topic_base + "/motion/head", "2YES")
def woz_head_motion_no(self):
    client.publish(topic_base + "/motion/head", "2NO")
def woz_head_motion_center(self):
    client.publish(topic_base + "/motion/head", "CENTER")
def woz_head_motion_left(self):
    client.publish(topic_base + "/motion/head", "LEFT")
def woz_head_motion_right(self):
    client.publish(topic_base + "/motion/head", "RIGHT")
def woz_head_motion_up(self):
    client.publish(topic_base + "/motion/head", "UP")
def woz_head_motion_down(self):
    client.publish(topic_base + "/motion/head", "DOWN")
def woz_head_motion_2left(self):
    client.publish(topic_base + "/motion/head", "2LEFT")
def woz_head_motion_2right(self):
    client.publish(topic_base + "/motion/head", "2RIGHT")
def woz_head_motion_2up(self):
    client.publish(topic_base + "/motion/head", "2UP")
def woz_head_motion_2down(self):
    client.publish(topic_base + "/motion/head", "2DOWN")
def woz_head_motion_up_left(self):
    client.publish(topic_base + "/motion/head", "UP_LEFT")
def woz_head_motion_up_right(self):
    client.publish(topic_base + "/motion/head", "UP_RIGHT")
def woz_head_motion_down_left(self):
    client.publish(topic_base + "/motion/head", "DOWN_LEFT")
def woz_head_motion_down_right(self):
    client.publish(topic_base + "/motion/head", "DOWN_RIGHT")

# WoZ arms motion functions
def woz_arm_left_motion_up(self):
    client.publish(topic_base + "/motion/arm/left", "UP")
def woz_arm_right_motion_up(self):
    client.publish(topic_base + "/motion/arm/right", "UP")
def woz_arm_left_motion_down(self):
    client.publish(topic_base + "/motion/arm/left", "DOWN")
def woz_arm_right_motion_down(self):
    client.publish(topic_base + "/motion/arm/right", "DOWN")
def woz_arm_left_motion_pos_0(self):
    client.publish(topic_base + "/motion/arm/left", "POSITION 0")
def woz_arm_right_motion_pos_0(self):
    client.publish(topic_base + "/motion/arm/right", "POSITION 0")
def woz_arm_left_motion_pos_1(self):
    client.publish(topic_base + "/motion/arm/left", "POSITION 1")
def woz_arm_right_motion_pos_1(self):
    client.publish(topic_base + "/motion/arm/right", "POSITION 1")
def woz_arm_left_motion_pos_2(self):
    client.publish(topic_base + "/motion/arm/left", "POSITION 2")
def woz_arm_right_motion_pos_2(self):
    client.publish(topic_base + "/motion/arm/right", "POSITION 2")
def woz_arm_left_motion_pos_3(self):
    client.publish(topic_base + "/motion/arm/left", "POSITION 3")
def woz_arm_right_motion_pos_3(self):
    client.publish(topic_base + "/motion/arm/right", "POSITION 3")
def woz_arm_left_motion_shake(self):
    client.publish(topic_base + "/motion/arm/left", "SHAKE2")
def woz_arm_right_motion_shake(self):
    client.publish(topic_base + "/motion/arm/right", "SHAKE2")



# Woz arms motion buttons binding
gui.bt_arm_left_motion_up.bind("<Button-1>", woz_arm_left_motion_up)
gui.bt_arm_right_motion_up.bind("<Button-1>", woz_arm_right_motion_up)
gui.bt_arm_left_motion_down.bind("<Button-1>", woz_arm_left_motion_down)
gui.bt_arm_right_motion_down.bind("<Button-1>", woz_arm_right_motion_down)
gui.bt_arm_left_motion_pos_0.bind("<Button-1>", woz_arm_left_motion_pos_0)
gui.bt_arm_right_motion_pos_0.bind("<Button-1>", woz_arm_right_motion_pos_0)
gui.bt_arm_left_motion_pos_1.bind("<Button-1>", woz_arm_left_motion_pos_1)
gui.bt_arm_right_motion_pos_1.bind("<Button-1>", woz_arm_right_motion_pos_1)
gui.bt_arm_left_motion_pos_2.bind("<Button-1>", woz_arm_left_motion_pos_2)
gui.bt_arm_right_motion_pos_2.bind("<Button-1>", woz_arm_right_motion_pos_2)
gui.bt_arm_left_motion_pos_3.bind("<Button-1>", woz_arm_left_motion_pos_3)
gui.bt_arm_right_motion_pos_3.bind("<Button-1>", woz_arm_right_motion_pos_3)
gui.bt_arm_left_motion_shake.bind("<Button-1>", woz_arm_left_motion_shake)
gui.bt_arm_right_motion_shake.bind("<Button-1>", woz_arm_right_motion_shake)

# WoZ head motion buttons binding
gui.bt_head_motion_yes.bind("<Button-1>", woz_head_motion_yes)
gui.bt_head_motion_no.bind("<Button-1>", woz_head_motion_no)
gui.bt_head_motion_center.bind("<Button-1>", woz_head_motion_center)
gui.bt_head_motion_left.bind("<Button-1>", woz_head_motion_left)
gui.bt_head_motion_right.bind("<Button-1>", woz_head_motion_right)
gui.bt_head_motion_up.bind("<Button-1>", woz_head_motion_up)
gui.bt_head_motion_down.bind("<Button-1>", woz_head_motion_down)
gui.bt_head_motion_2left.bind("<Button-1>", woz_head_motion_2left)
gui.bt_head_motion_2right.bind("<Button-1>", woz_head_motion_2right)
gui.bt_head_motion_2up.bind("<Button-1>", woz_head_motion_2up)
gui.bt_head_motion_2down.bind("<Button-1>", woz_head_motion_2down)
gui.bt_head_motion_up_left.bind("<Button-1>", woz_head_motion_up_left)
gui.bt_head_motion_up_right.bind("<Button-1>", woz_head_motion_up_right)
gui.bt_head_motion_down_left.bind("<Button-1>", woz_head_motion_down_left)
gui.bt_head_motion_down_right.bind("<Button-1>", woz_head_motion_down_right)


# TTS function
def woz_tts(self):
    client.publish(topic_base + "/syslog", "EVA will try to speak a text: " + gui.msg_tts_text.get('1.0','end').strip())
    voice_option = gui.Lb_voices.get(ANCHOR)
    print(voice_option + "|" + gui.msg_tts_text.get('1.0','end').strip())
    client.publish(topic_base + "/talk", voice_option + "|" + gui.msg_tts_text.get('1.0','end'))


# TTS buttons binding
gui.bt_send_tts.bind("<Button-1>", woz_tts)


# Led "animations"
def ledAnimation(animation):
    if RUNNING_MODE == "EVA_ROBOT":
        client.publish(topic_base + "/leds", "STOP")
        client.publish(topic_base + "/leds", animation)
    if animation == "STOP":
        evaMatrix("grey")
    elif animation == "LISTEN":
        evaMatrix("green")
    elif animation == "SPEAK":
        evaMatrix("blue")
    elif animation == "ANGRY" or animation == "ANGRY2":
        evaMatrix("red")
    elif animation == "HAPPY":
        evaMatrix("green")
    elif animation == "SAD":
        evaMatrix("blue")
    elif animation == "SURPRISE":
        evaMatrix("yellow")
    elif animation == "WHITE":
        evaMatrix("white")
    elif animation == "RAINBOW":
        evaMatrix("white")
        print("Falta gerar a imagem do RAINBOW para os leds do EvaSIM")
    else: print("A wrong led animation was selected.")


# Set the Eva emotion
def evaEmotion(expression):
    if expression == "NEUTRAL":
        gui.canvas.create_image(156, 161, image = im_eyes_neutral)
    elif expression == "ANGRY":
        gui.canvas.create_image(156, 161, image = im_eyes_angry)
    elif expression == "HAPPY":
        gui.canvas.create_image(156, 161, image = im_eyes_happy)
    elif expression == "SAD":
        gui.canvas.create_image(156, 161, image = im_eyes_sad)
    elif expression == "FEAR":
        gui.canvas.create_image(156, 161, image = im_eyes_fear)
    elif expression == "SURPRISE":
        gui.canvas.create_image(156, 161, image = im_eyes_surprise)
    elif expression == "DISGUST":
        gui.canvas.create_image(156, 161, image = im_eyes_disgust)
    elif expression == "INLOVE":
        gui.canvas.create_image(156, 161, image = im_eyes_inlove)
    elif expression == "POWER_ON": 
        gui.canvas.create_image(156, 161, image = im_eyes_on)
    else: 
        print("A wrong expression was selected.")
    if RUNNING_MODE == "SIMULATOR":
        time.sleep(1) # apenas um tempo simbólico para o simulador


# Set the Eva matrix
def evaMatrix(color):
    if color == "blue":
        gui.canvas.create_image(155, 349, image = im_matrix_blue)
    elif color == "red":
        gui.canvas.create_image(155, 349, image = im_matrix_red)
    elif color == "yellow":
        gui.canvas.create_image(155, 349, image = im_matrix_yellow)
    elif color == "green":
        gui.canvas.create_image(155, 349, image = im_matrix_green)
    elif color == "white":
        gui.canvas.create_image(155, 349, image = im_matrix_white)
    elif color == "grey": # somente para representar a luz da matrix apagada
        gui.canvas.create_image(155, 349, image = im_matrix_grey)
    else : 
        print("A wrong color to matrix was selected.")


# Set the image of light (color and state)
def light(color, state):
    color_map = {"WHITE":"#ffffff", "BLACK":"#000000", "RED":"#ff0000", "PINK":"#e6007e", "GREEN":"#00ff00", "YELLOW":"#ffff00", "BLUE":"#0000ff"}
    if color_map.get(color) != None:
        color = color_map.get(color)
    if state == "ON":
        gui.canvas.create_oval(300, 205, 377, 285, fill = color, outline = color )
        gui.canvas.create_image(340, 285, image = gui.bulb_image) # redesenha a lampada
    else:
        gui.canvas.create_oval(300, 205, 377, 285, fill = "#000000", outline = "#000000" ) # cor preta indica light off
        gui.canvas.create_image(340, 285, image = gui.bulb_image) # redesenha a lampada


# Virtual machine functions
# Execute the commands
def exec_comando(node):
    global EVA_ROBOT_STATE
    global img_neutral, img_happy, img_angry, img_sad, img_surprise
    if node.tag == "voice":
        gui.terminal.insert(INSERT, "\nSTATE: Selected Voice => " + node.attrib["tone"])
        gui.terminal.see(tkinter.END)
        gui.terminal.insert(INSERT, "\nTIP: If the <talk> command doesn't speak some text, try emptying the audio_cache_files folder", "tip")
        if RUNNING_MODE == "EVA_ROBOT":
            client.publish(topic_base + "/syslog", "Using the voice: " + node.attrib["tone"]) # 


    if node.tag == "motion": # Movement of the head and arms
        if node.get("leftArm") != None: # Move the left arm
            gui.terminal.insert(INSERT, "\nSTATE: Moving the left arm! Movement type => " + node.attrib["leftArm"], "motion")
            gui.terminal.see(tkinter.END)
        if node.get("rightArm") != None: # Move the right arm
            gui.terminal.insert(INSERT, "\nSTATE: Moving the right arm! Movement type => " + node.attrib["rightArm"], "motion")
            gui.terminal.see(tkinter.END)
        if node.get("head") != None: # Move head with the new format (<head> element)
                gui.terminal.insert(INSERT, "\nSTATE: Moving the head! Movement type => " + node.attrib["head"], "motion")
                gui.terminal.see(tkinter.END)
        else: # Check if the old version was used
            if node.get("type") != None: # Maintaining compatibility with the old version of the motion element
                gui.terminal.insert(INSERT, "\nSTATE: Moving the head! Movement type => " + node.attrib["type"], "motion")
                gui.terminal.see(tkinter.END)
        print("Moving the head and/or the arms.")
        if RUNNING_MODE == "EVA_ROBOT":
            if node.get("leftArm") != None: # Move the left arm
                client.publish(topic_base + "/motion/arm/left", node.attrib["leftArm"]); # comando para o robô físico
            if node.get("rightArm") != None:  # Move the right arm
                client.publish(topic_base + "/motion/arm/right", node.attrib["rightArm"]); # comando para o robô físico
            if node.get("head") != None: # Move head with the new format (<head> element)
                    client.publish(topic_base + "/motion/head", node.attrib["head"]); # Command for the physical robot
                    time.sleep(0.2) # This pause is necessary for arm commands to be received via the serial port
            else: # Check if the old version was used
                if node.get("type") != None: # Maintaining compatibility with the old version of the motion element    
                    client.publish(topic_base + "/motion/head", node.attrib["type"]); # Command for the physical robot
                    time.sleep(0.2) # This pause is necessary for arm commands to be received via the serial port
        else:
            time.sleep(0.1) # A symbolic time. In the robot, the movement does not block the script and takes different times


    elif node.tag == "light":
        lightEffect = "ON"
        state = node.attrib["state"]
        # Process light Effects settings
        if root.find("settings").find("lightEffects") != None:
            if root.find("settings").find("lightEffects").attrib["mode"] == "OFF":
                lightEffect = "OFF"
        
        # Following case, if the state is off, and may not have a color attribute defined
        if state == "OFF":
            color = "BLACK"
            if lightEffect == "OFF":
                message_state = "\nSTATE: Light Effects DISABLED."
            else:
                message_state = "\nSTATE: Turnning off the light."
            gui.terminal.insert(INSERT, message_state)
            gui.terminal.see(tkinter.END)
        else:
            color = node.attrib["color"]
            if lightEffect == "OFF":
                message_state = "\nSTATE: Light Effects DISABLED."
                state = "OFF"
            else:
                message_state = "\nSTATE: Turnning on the light. Color = " + color + "."
            gui.terminal.insert(INSERT, message_state)
            gui.terminal.see(tkinter.END) # Autoscrolling
        light(color , state)

        if RUNNING_MODE == "EVA_ROBOT":
            client.publish(topic_base + "/light", color + "|" + state); # Command for the physical robot
        else:
            time.sleep(0.1) # Emulates real bulb response time


    elif node.tag == "wait":
        duration = node.attrib["duration"]
        gui.terminal.insert(INSERT, "\nSTATE: Pausing. Duration = " + duration + " ms")
        gui.terminal.see(tkinter.END)
        time.sleep(int(duration)/1000) # Convert to seconds


    elif node.tag == "led":
        # Selection of the execution mode is done within the ledAnimation() function
        ledAnimation(node.attrib["animation"])
        gui.terminal.insert(INSERT, "\nSTATE: Matrix Leds. Animation = " + node.attrib["animation"])
        gui.terminal.see(tkinter.END)
        

    elif node.tag == "mqtt":
        mqtt_topic = node.attrib["topic"]
        if (len(mqtt_topic)) == 0: # erro
            gui.terminal.insert(INSERT, "\nError -> The topic is empty.")
            gui.terminal.see(tkinter.END)
            exit(1)

        if node.text == None: # There is no text to send.
            gui.terminal.insert(INSERT, "\nError -> There is no message to send.")
            gui.terminal.see(tkinter.END)
            exit(1)

        texto = node.text
        palavras = texto.split()
        texto = ' '.join(palavras) # Removendo mais de um espaço entre as palavras.
        texto = texto.replace('\n', '').replace('\r', '').replace('\t', '') # Remove tabulações e salto de linha.
        # Replace variables throughout the text. variables must exist in memory
        
        if "#" in texto:
            var_list = re.findall(r'\#[a-zA-Z]+[a-zA-Z0-9_-]*', texto) # Generate list of occurrences of vars (#...)
            for v in var_list:
                if v[1:] in eva_memory.vars:
                    texto = texto.replace(v, str(eva_memory.vars[v[1:]]))
                else:
                    # If the variable does not exist in the robot's memory, it displays an error message
                    print("[b white on red blink] FATAL ERROR [/]:  The variable [b white]#" + v[1:] + "[/] used in[b white] MQTT[/] element, [b yellow reverse] has not been declared [/]. Please, check your code.✋⛔️")
                    exit(1)

        # This part replaces the $, or the $-1 or the $1 in the text
        if "$" in texto: # Check if there is $ in the text
            # Checks if var_dollar has any value in the robot's memory
            if (len(eva_memory.var_dolar)) == 0:
                exit(1)
            else: # Find the patterns $ $n or $-n in the string and replace with the corresponding values
                dollars_list = re.findall(r'\$[-0-9]*', texto) # Find dollar patterns and return a list of occurrences
                dollars_list = sorted(dollars_list, key=len, reverse=True) # Sort the list in descending order of length (of the element)
                for var_dollar in dollars_list:
                    if len(var_dollar) == 1: # Is the dollar ($)
                        texto = texto.replace(var_dollar, eva_memory.var_dolar[-1][0])
                    else: # May be of type $n or $-n
                        if "-" in var_dollar: # $-n type
                            indice = int(var_dollar[2:]) # Var dollar is of type $-n. then just take n and convert it to int
                            texto = texto.replace(var_dollar, eva_memory.var_dolar[-(indice + 1)][0]) 
                        else: # tipo $n
                            indice = int(var_dollar[1:]) # Var dollar is of type $n. then just take n and convert it to int
                            texto = texto.replace(var_dollar, eva_memory.var_dolar[(indice - 1)][0])


        client.publish(mqtt_topic, texto)
        print("Publishing a MQTT message to an external device.", mqtt_topic, texto)
        gui.terminal.insert(INSERT, "\nSTATE: MQTT publishing. Topic = " + mqtt_topic + " and Message = " + texto + ".")
        gui.terminal.see(tkinter.END)


    elif node.tag == "random":
        min = node.attrib["min"]
        max = node.attrib["max"]
        # Check if min <= max
        if (int(min) > int(max)):
            gui.terminal.insert(INSERT, "\nError -> The 'min' attribute of the random command must be less than or equal to the 'max' attribute. Please, check your code.", "error")
            gui.terminal.see(tkinter.END)
            exit(1)

        if node.get("var") == None: # Maintains compatibility with the use of the $ variable
            eva_memory.var_dolar.append([str(rnd.randint(int(min), int(max))), "<random>"])
            gui.terminal.insert(INSERT, "\nSTATE: Generating a random number (using the variable $): " + eva_memory.var_dolar[-1][0])
            tab_load_mem_dollar()
            gui.terminal.see(tkinter.END)
            print("random command, min = " + min + ", max = " + max + ", valor = " + eva_memory.var_dolar[-1][0])
        else:
            var_name = node.attrib["var"]
            eva_memory.vars[var_name] = str(rnd.randint(int(min), int(max)))
            print("Eva ram => ", eva_memory.vars)
            gui.terminal.insert(INSERT, "\nSTATE: Generating a random number (using the user variable '" + var_name + "'): " + str(eva_memory.vars[var_name]))
            tab_load_mem_vars() # Enter data from variable memory into the var table
            gui.terminal.see(tkinter.END)
            print("random command USING VAR, min = " + min + ", max = " + max + ", valor = ")


    elif node.tag == "listen":
        if node.get("language") == None: # Maintains compatibility with the use of <listen> in old scripts
            # It will be used the default value defined in config.py file
            language_for_listen = config.LANG_DEFAULT_SPEECH_RECOGNITION
        else:
            language_for_listen =  node.attrib["language"]

        if RUNNING_MODE == "EVA_ROBOT": 
            client.publish(topic_base + "/syslog", "EVA is listening...")
            EVA_ROBOT_STATE = "BUSY"
            ledAnimation("LISTEN")
            client.publish(topic_base + "/listen", language_for_listen)

            while (EVA_ROBOT_STATE != "FREE"):
                pass

            if node.get("var") == None: # Maintains compatibility with the use of the $ variable
                eva_memory.var_dolar.append([EVA_DOLLAR, "<listen>"])
                gui.terminal.insert(INSERT, "\nSTATE: Listening (language -> " + language_for_listen + "): var = $" + ", value = " + eva_memory.var_dolar[-1][0])
                tab_load_mem_dollar()
                gui.terminal.see(tkinter.END)
                ledAnimation("STOP")
                
            else:
                var_name = node.attrib["var"]
                eva_memory.vars[var_name] = EVA_DOLLAR
                print("Eva ram => ", eva_memory.vars)
                gui.terminal.insert(INSERT, "\nSTATE: Listening (language -> " + language_for_listen + "): (using the user variable '" + var_name + "'): " + EVA_DOLLAR)
                tab_load_mem_vars() # Enter data from variable memory into the var table
                gui.terminal.see(tkinter.END)
                print("Listen command USING VAR...")
                ledAnimation("STOP")

        else:
            lock_thread_pop()
            ledAnimation("LISTEN")
            # Pop up window closing function for the <return> key)
            def fechar_pop_ret(self): 
                print(var.get())
                if node.get("var") == None: # Maintains compatibility with the use of the $ variable
                    eva_memory.var_dolar.append([var.get(), "<listen>"])
                    gui.terminal.insert(INSERT, "\nSTATE: Listening (language -> " + language_for_listen + "): var = $" + ", value = " + eva_memory.var_dolar[-1][0])
                    tab_load_mem_dollar()
                    gui.terminal.see(tkinter.END)
                    pop.destroy()
                    unlock_thread_pop() # Reactivate the script processing thread
                else:
                    var_name = node.attrib["var"]
                    eva_memory.vars[var_name] = var.get()
                    print("Eva ram => ", eva_memory.vars)
                    gui.terminal.insert(INSERT, "\nSTATE: Listening (language -> " + language_for_listen + "): (using the user variable '" + var_name + "'): " + var.get())
                    tab_load_mem_vars() # Enter data from variable memory into the var table
                    gui.terminal.see(tkinter.END)
                    print("Listen command USING VAR...")
                    pop.destroy()
                    unlock_thread_pop() # Reactivate the script processing thread
            
            # Pop up window closing function for OK button
            def fechar_pop_bt(): 
                print(var.get())
                if node.get("var") == None: # Maintains compatibility with the use of the $ variable
                    eva_memory.var_dolar.append([var.get(), "<listen>"])
                    gui.terminal.insert(INSERT, "\nSTATE: Listening (language -> " + language_for_listen + ">: var = $" + ", value = " + eva_memory.var_dolar[-1][0])
                    tab_load_mem_dollar()
                    gui.terminal.see(tkinter.END)
                    pop.destroy()
                    unlock_thread_pop() # Reactivate the script processing thread
                else:
                    var_name = node.attrib["var"]
                    eva_memory.vars[var_name] = var.get()
                    print("Eva ram => ", eva_memory.vars)
                    gui.terminal.insert(INSERT, "\nSTATE: Listening (language -> " + language_for_listen + "): (using the user variable '" + var_name + "'): " + var.get())
                    tab_load_mem_vars() # Enter data from variable memory into the var table
                    gui.terminal.see(tkinter.END)
                    print("Listen command USING VAR...")
                    pop.destroy()
                    unlock_thread_pop() # Reactivate the script processing thread
                
            # Window (GUI) creation
            var = StringVar()
            pop = Toplevel(gui)
            pop.title("Listen Command")
            # Disable the maximize and close buttons
            pop.resizable(False, False)
            pop.protocol("WM_DELETE_WINDOW", False)
            w = 450
            h = 150
            ws = gui.winfo_screenwidth()
            hs = gui.winfo_screenheight()
            x = (ws/2) - (w/2)
            y = (hs/2) - (h/2)  
            pop.geometry('%dx%d+%d+%d' % (w, h, x, y))
            label = Label(pop, text="Eva is listening (language -> " + language_for_listen + ")... Please, enter your answer!", font = ('Arial', 10))
            label.pack(pady=20)
            E1 = Entry(pop, textvariable = var, font = ('Arial', 10))
            E1.bind("<Return>", fechar_pop_ret)
            E1.pack()
            Button(pop, text="    OK    ", font = font1, command=fechar_pop_bt).pack(pady=20)
            # Wait for release, waiting for the user's response
            while thread_pop_pause: 
                time.sleep(0.5)
            ledAnimation("STOP")


    elif node.tag == "log": # Send a log information
        global log_seq_numbers
        if node.text == None: # There is no text to send
            print("There is no text to send in the element <log>.")
            gui.terminal.insert(INSERT, "\nError -> There is no text to send in the element <log>. Please, check your code.", "error")
            gui.terminal.see(tkinter.END)
            exit(1)

        texto = node.text
        # Replace variables throughout the text. variables must exist in memory
        if "#" in texto:
            # Checks if the robot's memory (vars) is empty
            if eva_memory.vars == {}:
                gui.terminal.insert(INSERT, "\nError -> No variables have been defined. Please, check your code.", "error")
                gui.terminal.see(tkinter.END)
                exit(1)

            var_list = re.findall(r'\#[a-zA-Z]+[a-zA-Z0-9_-]*', texto) # Generate list of occurrences of vars (#...)
            for v in var_list:
                if v[1:] in eva_memory.vars:
                    texto = texto.replace(v, str(eva_memory.vars[v[1:]]))
                else:
                    # If the variable does not exist in the robot's memory, it displays an error message
                    print("================================")
                    error_string = "\nError -> The variable #" + v[1:] + " has not been declared. Please, check your code."
                    gui.terminal.insert(INSERT, error_string, "error")
                    gui.terminal.see(tkinter.END)
                    exit(1)

        # This part replaces the $, or the $-1 or the $1 in the text
        if "$" in texto: # Check if there is $ in the text
            # Checks if var_dollar has any value in the robot's memory
            if (len(eva_memory.var_dolar)) == 0:
                gui.terminal.insert(INSERT, "\nError-> The variable $ has no value. Please, check your code.", "error")
                gui.terminal.see(tkinter.END)
                exit(1)
            else: # Find the patterns $ $n or $-n in the string and replace with the corresponding values
                dollars_list = re.findall(r'\$[-0-9]*', texto) # Find dollar patterns and return a list of occurrences
                dollars_list = sorted(dollars_list, key=len, reverse=True) # Sort the list in descending order of length (of the element)
                for var_dollar in dollars_list:
                    if len(var_dollar) == 1: # Is the dollar ($)
                        texto = texto.replace(var_dollar, eva_memory.var_dolar[-1][0])
                    else: # May be of type $n or $-n
                        if "-" in var_dollar: # $-n type
                            indice = int(var_dollar[2:]) # Var dollar is of type $-n. then just take n and convert it to int
                            texto = texto.replace(var_dollar, eva_memory.var_dolar[-(indice + 1)][0]) 
                        else: # tipo $n
                            indice = int(var_dollar[1:]) # Var dollar is of type $n. then just take n and convert it to int
                            texto = texto.replace(var_dollar, eva_memory.var_dolar[(indice - 1)][0])

        if node.attrib["name"] in log_seq_numbers:
            log_seq_number = log_seq_numbers[node.attrib["name"]] = log_seq_numbers[node.attrib["name"]] + 1
        else:
            log_seq_number = log_seq_numbers[node.attrib["name"]] = 1

        client.publish(topic_base + "/log", node.attrib["name"] + "_" + str(log_seq_number) + '_' + texto)    
        gui.terminal.insert(INSERT, '\nSTATE: Sending log name:' + node.attrib["name"] + ', log text: ' + texto )
        gui.terminal.see(tkinter.END)


    elif node.tag == "talk": # Blocking function
        if node.text == None: # There is no text to speech
            print("There is no text to speech in the element <talk>.")
            gui.terminal.insert(INSERT, "\nError -> There is no text to speech in the element <talk>. Please, check your code.", "error")
            gui.terminal.see(tkinter.END)
            exit(1)

        texto = node.text
        # Replace variables throughout the text. variables must exist in memory
        if "#" in texto:
            # Checks if the robot's memory (vars) is empty
            if eva_memory.vars == {}:
                gui.terminal.insert(INSERT, "\nError -> No variables have been defined. Please, check your code.", "error")
                gui.terminal.see(tkinter.END)
                exit(1)

            var_list = re.findall(r'\#[a-zA-Z]+[0-9]*', texto) # Generate list of occurrences of vars (#...)
            for v in var_list:
                if v[1:] in eva_memory.vars:
                    texto = texto.replace(v, str(eva_memory.vars[v[1:]]))
                else:
                    # If the variable does not exist in the robot's memory, it displays an error message
                    print("================================")
                    error_string = "\nError -> The variable #" + v[1:] + " has not been declared. Please, check your code."
                    gui.terminal.insert(INSERT, error_string, "error")
                    gui.terminal.see(tkinter.END)
                    exit(1)

        # This part replaces the $, or the $-1 or the $1 in the text
        if "$" in texto: # Check if there is $ in the text
            # Checks if var_dollar has any value in the robot's memory
            if (len(eva_memory.var_dolar)) == 0:
                gui.terminal.insert(INSERT, "\nError-> The variable $ has no value. Please, check your code.", "error")
                gui.terminal.see(tkinter.END)
                exit(1)
            else: # Find the patterns $ $n or $-n in the string and replace with the corresponding values
                dollars_list = re.findall(r'\$[-0-9]*', texto) # Find dollar patterns and return a list of occurrences
                dollars_list = sorted(dollars_list, key=len, reverse=True) # Sort the list in descending order of length (of the element)
                for var_dollar in dollars_list:
                    if len(var_dollar) == 1: # Is the dollar ($)
                        texto = texto.replace(var_dollar, eva_memory.var_dolar[-1][0])
                    else: # May be of type $n or $-n
                        if "-" in var_dollar: # $-n type
                            indice = int(var_dollar[2:]) # Var dollar is of type $-n. then just take n and convert it to int
                            texto = texto.replace(var_dollar, eva_memory.var_dolar[-(indice + 1)][0]) 
                        else: # tipo $n
                            indice = int(var_dollar[1:]) # Var dollar is of type $n. then just take n and convert it to int
                            texto = texto.replace(var_dollar, eva_memory.var_dolar[(indice - 1)][0])
            
        # This part implements the random text generated by using the / character
        texto = texto.split(sep="/") # Text becomes a list with the number of sentences divided by character. /
        print(texto)
        ind_random = rnd.randint(0, len(texto)-1)
        gui.terminal.insert(INSERT, '\nSTATE: Speaking: "' + texto[ind_random] + '"')
        gui.terminal.see(tkinter.END)

        if RUNNING_MODE == "EVA_ROBOT":
            client.publish(topic_base + "/syslog", "EVA will try to speak a text: " + texto[ind_random])
            ledAnimation("SPEAK")
            EVA_ROBOT_STATE = "BUSY" # Speech is a blocking function. the robot is busy
            if node.get("tone") == None: # Usuario não selecionou a voz no talk. A opção global será utilizada
                client.publish(topic_base + "/talk", root.find("settings")[0].attrib["tone"] + "|" + texto[ind_random])
            else:
                client.publish(topic_base + "/talk", node.attrib["tone"] + "|" + texto[ind_random]) # voz selecionado em talk será utilizada
            while(EVA_ROBOT_STATE != "FREE"):
                pass
            ledAnimation("STOP")
        else:
            if not TTS_IBM_WATSON: # without IBM-Watson
                lock_thread_pop()
                ledAnimation("SPEAK")
                # Pop up window closing function for OK button
                def fechar_pop_bt():
                    pop.destroy()
                    unlock_thread_pop() # Reactivate the script processing thread
                    
                # Window (GUI) creation
                var = StringVar()
                pop = Toplevel(gui)
                pop.title("TTS - Message Box - EVA is speaking!")
                # Disable the maximize and close buttons
                # pop.resizable(False, False)
                pop.protocol("WM_DELETE_WINDOW", False)
                w = int(45 * len(texto[ind_random])/4.5)
                if w < 330: # minimum width allowed
                    w = 330
                h = 200
                ws = gui.winfo_screenwidth()
                hs = gui.winfo_screenheight()
                x = (ws/2) - (w/2)
                y = (hs/2) - (h/2)  
                pop.geometry('%dx%d+%d+%d' % (w, h, x, y))
                label = Label(pop, text=texto[ind_random], font = ('Arial', 12))
                label.pack(pady=20)
                Button(pop, text="    OK    ", font = ('Arial', 12), command=fechar_pop_bt).pack(pady=20)
                # Wait for release, waiting for the user's response
                while thread_pop_pause: 
                    time.sleep(0.5)
                ledAnimation("STOP")

                # # We had a problem here. Something like a deadlock, perhaps...
                # gui.option_add('*Dialog.msg.width', 30)
                # gui.option_add('*Dialog.msg.font', 'Arial 14')
                # lock_thread_pop()
                # lock = threading.Lock()
                # lock.acquire()
                # messagebox.showinfo("TTS - Message Box - EVA is speaking!", texto[ind_random])
                # lock.release()
                # time.sleep(.1)
                # while thread_pop_pause: 
                #     time.sleep(0.5)
                #     ledAnimation("STOP")

            elif TTS_IBM_WATSON:
                # Using IBM Watson ################################
                # Assume the default UTF-8 (Generates the hashing of the audio file)
                # Also, uses the voice tone attribute in file hashing
                if node.get("tone") == None: # Usuario não selecionou a voz no talk. A opção global será utilizada
                    tone_voice = root.find("settings")[0].attrib["tone"]
                else:
                    tone_voice = node.attrib["tone"]

                hash_object = hashlib.md5(texto[ind_random].encode())
                file_name = "_audio_"  + tone_voice + hash_object.hexdigest()

                # Checks if the speech audio already exists in the folder
                if not (os.path.isfile("audio_cache_files/" + file_name + audio_ext)): # If it doesn't exist, call Watson
                    audio_file_is_ok = False
                    while(not audio_file_is_ok):
                        # Eva TTS functions
                        with open("audio_cache_files/" + file_name + audio_ext, 'wb') as audio_file:
                            try:
                                res = tts.synthesize(texto[ind_random], accept = ibm_audio_ext, voice = tone_voice).get_result()
                                audio_file.write(res.content)
                                playsound("audio_cache_files/" + file_name + audio_ext, block = True) # Play the audio of the speech
                            except:
                                print("Voice exception")
                                gui.terminal.insert(INSERT, "\nError when trying to select voice tone, please verify the tone atribute.\n", "error")
                                gui.terminal.see(tkinter.END)
                                exit(1)
                        file_size = os.path.getsize("audio_cache_files/" + file_name + audio_ext)
                        if file_size == 0: # Corrupted file
                            print("#### Corrupted file.. (It's necessary to use the same implementation like in tts-module in EVA robot!)")
                            os.remove("audio_cache_files/" + file_name + audio_ext)
                        else:
                            audio_file_is_ok = True
                else:
                    playsound("audio_cache_files/" + file_name + audio_ext, block = True) # Play the audio of the speech
            ##############################


    elif node.tag == "evaEmotion":
        emotion = node.attrib["emotion"]
        if RUNNING_MODE == "EVA_ROBOT":
            client.publish(topic_base + "/evaEmotion", emotion) # Command for physical EVA
        gui.terminal.insert(INSERT, "\nSTATE: Expressing an emotion => " + emotion)
        gui.terminal.see(tkinter.END)
        evaEmotion(emotion)


    elif node.tag == "audio":
        sound_file =  node.attrib["source"]
        block = False # Audio play does not block script execution
        if node.attrib["block"] == "TRUE":
            block = True
        message_audio = '\nSTATE: Playing a sound: "' + "audio_files/" + sound_file + ".wav" + '", block=' + str(block)

        # Process Audio Effects settings
        if root.find("settings").find("audioEffects") != None:
            if root.find("settings").find("audioEffects").attrib["mode"] == "OFF":
                # Mode off implies the use of MUTED-SOUND file 
                sound_file = "my_sounds/MUTED-SOUND.wav"
                message_audio = "\nSTATE: Audio Effects DISABLED."

        gui.terminal.insert(INSERT, message_audio)
        gui.terminal.see(tkinter.END)

        try:
            if block == True:
                if RUNNING_MODE == "EVA_ROBOT":
                    client.publish(topic_base + "/syslog", "EVA will play a sound in blocking mode.")
                    EVA_ROBOT_STATE = "BUSY"
                    client.publish(topic_base + "/audio", sound_file + "|" + "TRUE")
                    while (EVA_ROBOT_STATE != "FREE"):
                        pass
                else:
                    print(sound_file)
                    playsound("audio_files/" + sound_file + ".wav", block = block)

            else: # Block = False
                if RUNNING_MODE == "EVA_ROBOT":
                    client.publish(topic_base + "/syslog", "EVA will play a sound in no-blocking mode.")
                    client.publish(topic_base + "/audio", sound_file + "|" + "FALSE")
                else:
                    playsound("audio_files/" + sound_file + ".wav", block = block) 
        except Exception as e:
            # Handle an exception. I didn't find any exceptions in the library documentation
            error_string = "\nError -> " + str(e) + "."
            gui.terminal.insert(INSERT, error_string, "error")
            gui.terminal.see(tkinter.END)
            exit(1)


##########################################################
    elif node.tag == "case":
        # Case 1 (Exact)
        global valor
        eva_memory.reg_case = 0 # Clear the case flag
        valor = node.attrib["value"]
        valor = valor.lower() # Comparisons are not case sensitive
        # Handles comparison types and operators
        # Case 1 (op = "exact")
        if node.attrib['op'] == "exact": # Exact é sempre uma comparação de STRINGS
            # Case in which a user variable was defined for a command: QRcode, random, userEmotion or userId
            if node.attrib['var'] != "$":
                # It remains to check whether the variable exists in the robot's memory
                # eva_memory.vars[st_var_value[1:]
                print("value: ", valor, type(valor), node.attrib['var'], eva_memory.vars[node.attrib['var']])
                if valor[0] == "#": # é uma referência a uma variável
                    valor = valor[1:] # remove o # da referência
                if valor == str(eva_memory.vars[node.attrib['var']]).lower(): # Comparação de STRINGS
                    print("case = true")
                    eva_memory.reg_case = 1 # Turn on the reg case indicating that the comparison result was true

            # Checks if var_dollar memory has any value
            elif (len(eva_memory.var_dolar)) == 0:
                gui.terminal.insert(INSERT, "\nError -> The variable $ has no value. Please, check your code.", "error")
                gui.terminal.see(tkinter.END)
                exit(1)  

            
            elif valor == eva_memory.var_dolar[-1][0].lower():
                # Compare value with the top of the stack of the var_dollar variable
                print("value: ", valor, type(valor))
                print("case = true")
                eva_memory.reg_case = 1 # Turn on the reg_case indicating that the comparison result was true
        
        # Case 2 (op = "contain")
        elif node.attrib['op'] == "contain":      
            # Checa se a comparação é com o dollar
            if "$" == node.attrib['var'][0]:
                if (len(eva_memory.var_dolar)) == 0: # Checks if var_dollar memory has any value
                    gui.terminal.insert(INSERT, "\nError -> The variable $ has no value. Please, check your code.", "error")
                    gui.terminal.see(tkinter.END)
                    exit(1)  
                else:
                    # Checks if the string in value is contained in $
                    print("value: ", valor, type(valor))
                    if valor in eva_memory.var_dolar[-1][0].lower(): 
                        print("case = true")
                        eva_memory.reg_case = 1 # Turn on the reg case indicating that the comparison result was true
            # se não é com dollar então é com uma var do usuário
            elif node.attrib['var'] in eva_memory.vars: # verifica se a variável de usuário existe na memória
                if "#" == valor[0]:
                    valor = valor[1:]
                    if str(eva_memory.vars[valor]).lower() in str(eva_memory.vars[node.attrib['var']]).lower():
                        print("case = true")
                        eva_memory.reg_case = 1 # Turn on the reg case indicating that the comparison result was true
                else:
                    if valor in eva_memory.vars[node.attrib['var']]:
                        print("case = true")
                        eva_memory.reg_case = 1 # Turn on the reg case indicating that the comparison result was true
            else:
                gui.terminal.insert(INSERT, "\nError -> The variable '" + node.attrib['var'] + "' does no exist. Please, check your code.", "error")
                gui.terminal.see(tkinter.END)
##########################################################


        # case 3 (MATHEMATICAL COMPARISON)
        else:
            # Function to obtain an operand from $, n, #n, or value
            def get_op(st_var_value):
                # Is a constant?
                if st_var_value.isnumeric():
                    return int(st_var_value)

                # Is $?
                if st_var_value == "$":
                    # Checks if var_dollar memory has any value
                    if (len(eva_memory.var_dolar)) == 0:
                        gui.terminal.insert(INSERT, "\nError -> The variable $ has no value. Please, check your code.", "error")
                        gui.terminal.see(tkinter.END)
                        exit(1)
                    return int(eva_memory.var_dolar[-1][0]) # Returns the value of $ converted for int

                # Is a variable of type #n?
                if "#" in st_var_value:
                    # Checks if var #... DOES NOT exist in memory
                    if (st_var_value[1:] not in eva_memory.vars):
                        error_string = "\nError -> The variable #" + valor[1:] + " has not been declared. Please, check your code."
                        gui.terminal.insert(INSERT, error_string, "error")
                        gui.terminal.see(tkinter.END)
                        exit(1)
                    return int(eva_memory.vars[st_var_value[1:]]) # Returns the value of #n converted for int
                
                # If it is not a number, nor a dollar, nor a #, then it is a variable of this type var = "x" in <switch>
                # Checks if the variable exists in memory
                if (st_var_value not in eva_memory.vars):
                    error_string = "\nError -> The variable #" + valor[1:] + " has not been declared. Please, check your code."
                    gui.terminal.insert(INSERT, error_string, "error")
                    gui.terminal.see(tkinter.END)
                    exit(1)
                return int(eva_memory.vars[st_var_value]) # Returns the value of n converted for int

            # Obtains the operands to perform mathematical comparison operations
            # The restriction on not using constants in var of <switch> was guaranteed in the parser
            op1 = get_op(node.attrib['var'])
            op2 = get_op(valor)

            # Performs the operations ==, >, <, >=, <= and != to compare operands 1 and 2
            if node.attrib['op'] == "eq": # Equality
                if op1 == op2: # It is needed to remove the # from the variable
                    print("case = true")
                    eva_memory.reg_case = 1 # Turn on the reg_case indicating that the comparison result was true

            elif node.attrib['op'] == "lt": # Less than
                if op1 < op2:
                    print("case = true")
                    eva_memory.reg_case = 1 # Turn on the reg_case indicating that the comparison result was true

            elif node.attrib['op'] == "gt": # Greater than
                if op1 > op2:
                    print("case = true")
                    eva_memory.reg_case = 1 # Turn on the reg_case indicating that the comparison result was true
            
            elif node.attrib['op'] == "lte": # Less than or Equal
                if op1 <= op2:
                    print("case = true")
                    eva_memory.reg_case = 1 # Turn on the reg_case indicating that the comparison result was true

            elif node.attrib['op'] == "gte": # Greater than or Equal
                if op1 >= op2:
                    print("case = true")
                    eva_memory.reg_case = 1 # Turn on the reg_case indicating that the comparison result was true

            elif node.attrib['op'] == "ne": # Not equal
                if op1 != op2:
                    print("case = true")
                    eva_memory.reg_case = 1 # Turn on the reg_case indicating that the comparison result was true        


    elif node.tag == "default": # Default is always true
        print("Default = true")
        eva_memory.reg_case = 1 # Turn on the reg_case indicating that the comparison result was true


    elif node.tag == "counter":
        var_name = node.attrib["var"]
        var_value = int(node.attrib["value"])
        op = node.attrib["op"]
        # Checks if the operation is different from assignment and checks if var ... DOES NOT exist in memory
        if op != "=":
            if (var_name not in eva_memory.vars):
                error_string = "\nError -> The variable " + var_name + " has not been declared. Please, check your code."
                gui.terminal.insert(INSERT, error_string, "error")
                gui.terminal.see(tkinter.END)
                exit(1)

        if op == "=": # Perform the assignment
            eva_memory.vars[var_name] = var_value

        if op == "+": # Perform the addition
            eva_memory.vars[var_name] += var_value

        if op == "-": # Perform the addition
            eva_memory.vars[var_name] -= var_value

        if op == "*": # Perform the product
            eva_memory.vars[var_name] *= var_value

        if op == "/": # Performs the division (it was /=) but I changed it to //= (integer division)
            eva_memory.vars[var_name] //= var_value

        if op == "%": # Calculate the module
            eva_memory.vars[var_name] %= var_value
        
        print("Eva ram => ", eva_memory.vars)
        gui.terminal.insert(INSERT, "\nSTATE: Counter: var = " + var_name + ", value = " + str(var_value) + ", op(" + op + "), result = " + str(eva_memory.vars[var_name]))
        tab_load_mem_vars() # Enter data from variable memory into the variable table
        gui.terminal.see(tkinter.END)


    elif node.tag == "textEmotion":
        # Falta implementar o modo Simulador ###############
        if RUNNING_MODE == "EVA_ROBOT": 
            client.publish(topic_base + "/syslog", "EVA is analysing the text emotion...")
            EVA_ROBOT_STATE = "BUSY"
            ledAnimation("RAINBOW")
            if node.get("language") == None:
                client.publish(topic_base + "/textEmotion", config.LANG_DEFAULT_GOOGLE_TRANSLATING + "|" + eva_memory.var_dolar[-1][0])
            else:
                client.publish(topic_base + "/textEmotion", node.attrib["language"] + "|" + eva_memory.var_dolar[-1][0])
                

            while (EVA_ROBOT_STATE != "FREE"):
                pass
            
            if node.get("var") == None: # Maintains compatibility with the use of the $ variable
                eva_memory.var_dolar.append([EVA_DOLLAR, "<textEmotion>"])
                gui.terminal.insert(INSERT, "\nSTATE: textEmotion: var=$" + ", value = " + eva_memory.var_dolar[-1][0])
                tab_load_mem_dollar()
                gui.terminal.see(tkinter.END)
                ledAnimation("STOP")
            else:
                var_name = node.attrib["var"]
                eva_memory.vars[var_name] = EVA_DOLLAR
                print("Eva ram => ", eva_memory.vars)
                gui.terminal.insert(INSERT, "\nSTATE: textEmotion (using the user variable '" + var_name + "'): " + str(eva_memory.vars[var_name]))
                tab_load_mem_vars() # Enter data from variable memory into the var table
                gui.terminal.see(tkinter.END)
                print("textEmotion command USING VAR...")
            ledAnimation("STOP")
        
        else:

            lock_thread_pop()
            ledAnimation("LISTEN")
            def fechar_pop(): # Pop up window closing function
                print(var.get())
                if node.get("var") == None: # Maintains compatibility with the use of the $ variable
                    eva_memory.var_dolar.append([var.get(), "<textEmotion>"])
                    gui.terminal.insert(INSERT, "\nSTATE: textEmotion: var = $" + ", value = " + eva_memory.var_dolar[-1][0])
                    tab_load_mem_dollar()
                    gui.terminal.see(tkinter.END)
                else:
                    var_name = node.attrib["var"]
                    eva_memory.vars[var_name] = var.get()
                    print("Eva ram => ", eva_memory.vars)
                    gui.terminal.insert(INSERT, "\nSTATE: textEmotion (using the user variable '" + var_name + "'): " + str(eva_memory.vars[var_name]))
                    tab_load_mem_vars() # Enter data from variable memory into the var table
                    gui.terminal.see(tkinter.END)
                    print("textEmotion command USING VAR...")
                pop.destroy()
                ledAnimation("STOP")
                unlock_thread_pop() # Reactivate the script processing thread

            var = StringVar()
            var.set("NEUTRAL")
            img_neutral = PhotoImage(file = "images/img_neutral.png")
            img_happy = PhotoImage(file = "images/img_happy.png")
            img_angry = PhotoImage(file = "images/img_angry.png")
            img_sad = PhotoImage(file = "images/img_sad.png")
            img_surprise = PhotoImage(file = "images/img_surprise.png")
            img_fear = PhotoImage(file = "images/img_fear.png")
            img_disgust = PhotoImage(file = "images/img_disgust.png")
            pop = Toplevel(gui)
            pop.title("textEmotion Command")
            # Disable the maximize and close buttons
            pop.resizable(False, False)
            pop.protocol("WM_DELETE_WINDOW", False)
            w = 970
            h = 250
            ws = gui.winfo_screenwidth()
            hs = gui.winfo_screenheight()
            x = (ws/2) - (w/2)
            y = (hs/2) - (h/2)  
            pop.geometry('%dx%d+%d+%d' % (w, h, x, y))
            Label(pop, text="Eva is analysing the sentiment of your text. Please, choose one emotion!", font = ('Arial', 10)).place(x = 290, y = 10)
            # Images are displayed using labels
            Label(pop, image=img_neutral).place(x = 10, y = 50)
            Label(pop, image=img_happy).place(x = 147, y = 50)
            Label(pop, image=img_angry).place(x = 284, y = 50)
            Label(pop, image=img_sad).place(x = 421, y = 50)
            Label(pop, image=img_surprise).place(x = 558, y = 50)
            Label(pop, image=img_fear).place(x = 695, y = 50)
            Label(pop, image=img_disgust).place(x = 832, y = 50)
            Radiobutton(pop, text = "Neutral", variable = var, font = font1, command = None, value = "NEUTRAL").place(x = 35, y = 185)
            Radiobutton(pop, text = "Happy", variable = var, font = font1, command = None, value = "HAPPY").place(x = 172, y = 185)
            Radiobutton(pop, text = "Angry", variable = var, font = font1, command = None, value = "ANGRY").place(x = 312, y = 185)
            Radiobutton(pop, text = "Sad", variable = var, font = font1, command = None, value = "SAD").place(x = 452, y = 185)
            Radiobutton(pop, text = "Surprise", variable = var, font = font1, command = None, value = "SURPRISE").place(x = 580, y = 185)
            Radiobutton(pop, text = "Fear", variable = var, font = font1, command = None, value = "FEAR").place(x = 725, y = 185)
            Radiobutton(pop, text = "Disgust", variable = var, font = font1, command = None, value = "DISGUST").place(x = 855, y = 185)
            Button(pop, text = "           OK          ", font = font1, command = fechar_pop).place(x = 430, y = 215)
            # Wait for release, waiting for the user's response
            while thread_pop_pause: 
                time.sleep(0.5)


    elif node.tag == "userEmotion":
        # global img_neutral, img_happy, img_angry, img_sad, img_surprise
        
        if RUNNING_MODE == "EVA_ROBOT": 
            client.publish(topic_base + "/syslog", "EVA is capturing the user emotion...")
            EVA_ROBOT_STATE = "BUSY"
            ledAnimation("LISTEN")
            client.publish(topic_base + "/userEmotion", " ")

            while (EVA_ROBOT_STATE != "FREE"):
                pass

            if node.get("var") == None: # Maintains compatibility with the use of the $ variable
                eva_memory.var_dolar.append([EVA_DOLLAR, "<listen>"])
                gui.terminal.insert(INSERT, "\nSTATE: userEmotion: var=$" + ", value = " + eva_memory.var_dolar[-1][0])
                tab_load_mem_dollar()
                gui.terminal.see(tkinter.END)
                ledAnimation("STOP")
            else:
                var_name = node.attrib["var"]
                eva_memory.vars[var_name] = EVA_DOLLAR
                print("Eva ram => ", eva_memory.vars)
                gui.terminal.insert(INSERT, "\nSTATE: userEmotion (using the user variable '" + var_name + "'): " + str(eva_memory.vars[var_name]))
                tab_load_mem_vars() # Enter data from variable memory into the variable table
                gui.terminal.see(tkinter.END)
                print("userEmotion command USING VAR...")
                ledAnimation("STOP")
        else:

            lock_thread_pop()
            ledAnimation("LISTEN")
            def fechar_pop(): # Pop up window closing function
                print(var.get())
                if node.get("var") == None: # Maintains compatibility with the use of the $ variable
                    eva_memory.var_dolar.append([var.get(), "<userEmotion>"])
                    gui.terminal.insert(INSERT, "\nSTATE: userEmotion: var = $" + ", value = " + eva_memory.var_dolar[-1][0])
                    tab_load_mem_dollar()
                    gui.terminal.see(tkinter.END)
                else:
                    var_name = node.attrib["var"]
                    eva_memory.vars[var_name] = var.get()
                    print("Eva ram => ", eva_memory.vars)
                    gui.terminal.insert(INSERT, "\nSTATE: userEmotion (using the user variable '" + var_name + "'): " + str(eva_memory.vars[var_name]))
                    tab_load_mem_vars() # Enter data from variable memory into the var table
                    gui.terminal.see(tkinter.END)
                    print("userEmotion command USING VAR...")
                pop.destroy()
                ledAnimation("STOP")
                unlock_thread_pop() # Reactivate the script processing thread

            var = StringVar()
            var.set("NEUTRAL")
            img_neutral = PhotoImage(file = "images/img_neutral.png")
            img_happy = PhotoImage(file = "images/img_happy.png")
            img_angry = PhotoImage(file = "images/img_angry.png")
            img_sad = PhotoImage(file = "images/img_sad.png")
            img_surprise = PhotoImage(file = "images/img_surprise.png")
            img_fear = PhotoImage(file = "images/img_fear.png")
            img_disgust = PhotoImage(file = "images/img_disgust.png")
            pop = Toplevel(gui)
            pop.title("userEmotion Command")
            # Disable the maximize and close buttons
            pop.resizable(False, False)
            pop.protocol("WM_DELETE_WINDOW", False)
            w = 970
            h = 250
            ws = gui.winfo_screenwidth()
            hs = gui.winfo_screenheight()
            x = (ws/2) - (w/2)
            y = (hs/2) - (h/2)  
            pop.geometry('%dx%d+%d+%d' % (w, h, x, y))
            Label(pop, text="Eva is analysing your face expression. Please, choose one emotion!", font = ('Arial', 10)).place(x = 290, y = 10)
            # Images are displayed using labels
            Label(pop, image=img_neutral).place(x = 10, y = 50)
            Label(pop, image=img_happy).place(x = 147, y = 50)
            Label(pop, image=img_angry).place(x = 284, y = 50)
            Label(pop, image=img_sad).place(x = 421, y = 50)
            Label(pop, image=img_surprise).place(x = 558, y = 50)
            Label(pop, image=img_fear).place(x = 695, y = 50)
            Label(pop, image=img_disgust).place(x = 832, y = 50)
            Radiobutton(pop, text = "Neutral", variable = var, font = font1, command = None, value = "NEUTRAL").place(x = 35, y = 185)
            Radiobutton(pop, text = "Happy", variable = var, font = font1, command = None, value = "HAPPY").place(x = 172, y = 185)
            Radiobutton(pop, text = "Angry", variable = var, font = font1, command = None, value = "ANGRY").place(x = 312, y = 185)
            Radiobutton(pop, text = "Sad", variable = var, font = font1, command = None, value = "SAD").place(x = 452, y = 185)
            Radiobutton(pop, text = "Surprise", variable = var, font = font1, command = None, value = "SURPRISE").place(x = 580, y = 185)
            Radiobutton(pop, text = "Fear", variable = var, font = font1, command = None, value = "FEAR").place(x = 725, y = 185)
            Radiobutton(pop, text = "Disgust", variable = var, font = font1, command = None, value = "DISGUST").place(x = 855, y = 185)
            Button(pop, text = "           OK          ", font = font1, command = fechar_pop).place(x = 430, y = 215)
            # Wait for release, waiting for the user's response
            while thread_pop_pause: 
                time.sleep(0.5)


    elif node.tag == "qrRead":
        if RUNNING_MODE == "EVA_ROBOT": 
            client.publish(topic_base + "/syslog", "EVA is capturing QR Code information...")
            EVA_ROBOT_STATE = "BUSY"
            client.publish(topic_base + "/qrRead", " ")
            ledAnimation("LISTEN")
            

            while (EVA_ROBOT_STATE != "FREE"):
                pass
        
            if node.get("var") == None: # Maintains compatibility with the use of the $ variable
                eva_memory.var_dolar.append([EVA_DOLLAR, "<qrRead>"])
                gui.terminal.insert(INSERT, "\nSTATE: QR Code reading: var = $" + ", value = " + eva_memory.var_dolar[-1][0])
                tab_load_mem_dollar()
                gui.terminal.see(tkinter.END)
                ledAnimation("STOP")
            else:
                var_name = node.attrib["var"]
                eva_memory.vars[var_name] = EVA_DOLLAR
                print("Eva ram => ", eva_memory.vars)
                gui.terminal.insert(INSERT, "\nSTATE: QR Code reading (using the user variable '" + var_name + "'): " + str(eva_memory.vars[var_name]))
                tab_load_mem_vars() # Enter data from variable memory into the var table
                gui.terminal.see(tkinter.END)
                print("qrRead command USING VAR...")
            ledAnimation("STOP")

        else:

            lock_thread_pop()
            ledAnimation("LISTEN")
            # Pop up window closing function for the <return> key
            def fechar_pop_ret(self): 
                print(var.get())
                if node.get("var") == None: # Maintains compatibility with the use of the $ variable
                    eva_memory.var_dolar.append([var.get(), "<qrRead>"])
                    gui.terminal.insert(INSERT, "\nSTATE: QR Code reading: var = $" + ", value = " + eva_memory.var_dolar[-1][0])
                    tab_load_mem_dollar()
                    gui.terminal.see(tkinter.END)
                    pop.destroy()
                    unlock_thread_pop() # Reactivate the script processing thread
                else:
                    var_name = node.attrib["var"]
                    eva_memory.vars[var_name] = var.get()
                    print("Eva ram => ", eva_memory.vars)
                    gui.terminal.insert(INSERT, "\nSTATE: QR Code reading (using the user variable '" + var_name + "'): " + str(eva_memory.vars[var_name]))
                    tab_load_mem_vars() # Enter data from variable memory into the var table
                    gui.terminal.see(tkinter.END)
                    print("qrRead command USING VAR...")
                    pop.destroy()
                    unlock_thread_pop() # Reactivate the script processing thread
            
            # Pop up window closing function for OK button
            def fechar_pop_bt(): 
                print(var.get())
                if node.get("var") == None: # Maintains compatibility with the use of the $ variable
                    eva_memory.var_dolar.append([var.get(), "<qrRead>"])
                    gui.terminal.insert(INSERT, "\nSTATE: QR Code reading: var = $" + ", value = " + eva_memory.var_dolar[-1][0])
                    tab_load_mem_dollar()
                    gui.terminal.see(tkinter.END)
                    pop.destroy()
                    unlock_thread_pop() # Reactivate the script processing thread
                else:
                    var_name = node.attrib["var"]
                    eva_memory.vars[var_name] = var.get()
                    print("Eva ram => ", eva_memory.vars)
                    gui.terminal.insert(INSERT, "\nSTATE: QR Code reading (using the user variable '" + var_name + "'): " + str(eva_memory.vars[var_name]))
                    tab_load_mem_vars() # Enter data from variable memory into the var table
                    gui.terminal.see(tkinter.END)
                    print("qrRead command USING VAR...")
                    pop.destroy()
                    unlock_thread_pop() # Reactivate the script processing thread
                
            # Window (GUI) creation
            img_qr = PhotoImage(file = "images/img_qr.png")
            var = StringVar()
            pop = Toplevel(gui)
            pop.title("qrRead Command")
            # Disable the maximize and close buttons
            pop.resizable(False, False)
            pop.protocol("WM_DELETE_WINDOW", False)
            w = 350
            h = 200
            ws = gui.winfo_screenwidth()
            hs = gui.winfo_screenheight()
            x = (ws/2) - (w/2)
            y = (hs/2) - (h/2)  
            pop.geometry('%dx%d+%d+%d' % (w, h, x, y))
            label = Label(pop, text="Eva is reading a QR Code... \nPlease, enter the information contained in the QRCode!", font = ('Arial', 10))
            label.pack(pady=20)
            Label(pop, image=img_qr).place(x = 260, y = 110)
            E1 = Entry(pop, textvariable = var, font = ('Arial', 10))
            E1.bind("<Return>", fechar_pop_ret)
            E1.pack()
            Button(pop, text="    OK    ", font = font1, command=fechar_pop_bt).pack(pady=20)
            # Wait for release, waiting for the user's response
            while thread_pop_pause: 
                time.sleep(0.5)
            ledAnimation("STOP")


    elif node.tag == "userID":
        if RUNNING_MODE == "EVA_ROBOT": 
            EVA_ROBOT_STATE = "BUSY"
            client.publish(topic_base + "/userID", " ")
            ledAnimation("LISTEN")
            

            while (EVA_ROBOT_STATE != "FREE"):
                pass
        
            if node.get("var") == None: # Maintains compatibility with the use of the $ variable
                eva_memory.var_dolar.append([EVA_DOLLAR, "<userID>"])
                gui.terminal.insert(INSERT, "\nSTATE: userID: var = $" + ", value = " + eva_memory.var_dolar[-1][0])
                tab_load_mem_dollar()
                gui.terminal.see(tkinter.END)
 
            else:
                var_name = node.attrib["var"]
                eva_memory.vars[var_name] = EVA_DOLLAR
                print("Eva ram => ", eva_memory.vars)
                gui.terminal.insert(INSERT, "\nSTATE: userID (using the user variable '" + var_name + "'): " + str(eva_memory.vars[var_name]))
                tab_load_mem_vars() # Enter data from variable memory into the var table
                gui.terminal.see(tkinter.END)
                print("userID command USING VAR...")
            
            ledAnimation("STOP")

        else:

            lock_thread_pop()
            ledAnimation("LISTEN")
            # Pop up window closing function for the <return> key
            def fechar_pop_ret(self): 
                print(var.get())
                if node.get("var") == None: # mantém a compatibilidade com o uso da variável $
                    eva_memory.var_dolar.append([var.get(), "<userID>"])
                    gui.terminal.insert(INSERT, "\nSTATE: userID: var = $" + ", value = " + eva_memory.var_dolar[-1][0])
                    tab_load_mem_dollar()
                    gui.terminal.see(tkinter.END)
                    pop.destroy()
                    unlock_thread_pop() # Reactivate the script processing thread
                else:
                    var_name = node.attrib["var"]
                    eva_memory.vars[var_name] = var.get()
                    print("Eva ram => ", eva_memory.vars)
                    gui.terminal.insert(INSERT, "\nSTATE: userID reading (using the user variable '" + var_name + "'): " + str(eva_memory.vars[var_name]))
                    tab_load_mem_vars() # Enter data from variable memory into the var table
                    gui.terminal.see(tkinter.END)
                    print("userID command USING VAR...")
                    pop.destroy()
                    unlock_thread_pop() # Reactivate the script processing thread
            
            # Pop up window closing function for OK button
            def fechar_pop_bt(): 
                print(var.get())
                if node.get("var") == None: # Maintains compatibility with the use of the $ variable
                    eva_memory.var_dolar.append([var.get(), "<userID>"])
                    gui.terminal.insert(INSERT, "\nSTATE: userID: var = $" + ", value = " + eva_memory.var_dolar[-1][0])
                    tab_load_mem_dollar()
                    gui.terminal.see(tkinter.END)
                    pop.destroy()
                    unlock_thread_pop() # Reactivate the script processing thread
                else:
                    var_name = node.attrib["var"]
                    eva_memory.vars[var_name] = var.get()
                    print("Eva ram => ", eva_memory.vars)
                    gui.terminal.insert(INSERT, "\nSTATE: userID (using the user variable '" + var_name + "'): " + str(eva_memory.vars[var_name]))
                    tab_load_mem_vars() # Enter data from variable memory into the var table
                    gui.terminal.see(tkinter.END)
                    print("userID command USING VAR...")
                    pop.destroy()
                    unlock_thread_pop() # Reactivate the script processing thread
                
            # Window (GUI) creation
            img_userID = PhotoImage(file = "images/img_userID.png")
            var = StringVar()
            pop = Toplevel(gui)
            pop.title("userID Command")
            # Disable the maximize and close buttons
            pop.resizable(False, False)
            pop.protocol("WM_DELETE_WINDOW", False)
            w = 350
            h = 200
            ws = gui.winfo_screenwidth()
            hs = gui.winfo_screenheight()
            x = (ws/2) - (w/2)
            y = (hs/2) - (h/2)  
            pop.geometry('%dx%d+%d+%d' % (w, h, x, y))
            label = Label(pop, text="Eva is recognizing a face... \nPlease, enter the user name!", font = ('Arial', 10))
            label.pack(pady=20)
            Label(pop, image=img_userID).place(x = 260, y = 110)
            E1 = Entry(pop, textvariable = var, font = ('Arial', 10))
            E1.bind("<Return>", fechar_pop_ret)
            E1.pack()
            Button(pop, text="    OK    ", font = font1, command=fechar_pop_bt).pack(pady=20)
            # Wait for release, waiting for the user's response
            while thread_pop_pause: 
                time.sleep(0.5)
            ledAnimation("STOP")


def busca_commando(key : str): # The keys are strings
	# Search in settings. This is because "voice" is in settings and voice is always the first element
	for elem in root.find("settings").iter():
		if elem.get("key") != None: # Check if node has key attribute
			if elem.attrib["key"] == key:
				return elem
	# Search within the script
	for elem in root.find("script").iter(): # Go through all nodes in the script
		if elem.get("key") != None: # Check if node has key attribute
			if elem.attrib["key"] == key:
				return elem


# Search and insert links in the list that have "att_from" equal to the "from" attribute of the link
def busca_links(att_from):
    achou_link = False
    for i in range(len(links_node)):
        if att_from == links_node[i].attrib["from"]:
            fila_links.append(links_node[i])
            achou_link = True

    for l in fila_links:
        print("link: " + l.attrib["from"] + " -> " + l.attrib["to"] )
    return achou_link


# Execute commands in the link stack
def link_process(anterior = -1):
    global play, fila_links
    print("Play state............", play)
    gui.terminal.insert(INSERT, "\n---------------------------------------------------")
    gui.terminal.insert(INSERT, "\nSTATE: Starting the script: " + root.attrib["name"] + "_EvaML.xml")
    gui.terminal.see(tkinter.END)

    if RUNNING_MODE == "EVA_ROBOT":
        client.publish(topic_base + "/syslog", "Starting the script: " + root.attrib["name"] + "_EvaML.xml")

    while (len(fila_links) != 0) and (play == True):
        from_key = fila_links[0].attrib["from"] # Key of the command to execute
        to_key = fila_links[0].attrib["to"] # Key of next command
        comando_from = busca_commando(from_key).tag # Tag of the command to be executed
        comando_target = busca_commando(to_key).tag # Tag of target command
        print("Elemem:", comando_from,  ", from:", from_key, ", to_key:", to_key)

        # Prevents the same node from running consecutively. This happens with the node that precedes the "cases"
        if anterior != from_key:
            exec_comando(busca_commando(from_key))
            anterior = from_key
            print("ant: ", anterior, ", from: ", from_key)

        if (comando_from == "case") or (comando_from == "default"): # If the command executed was a case or a default
            if eva_memory.reg_case == 1: # Check the flag to see if the "case" was true
                if comando_target == "case" or comando_target == "default":
                    fila_aux = []
                    for l in fila_links:
                        if l.attrib["from"] == from_key:
                            fila_aux.append(l)
                    fila_links = []
                    for f in fila_aux:
                        busca_links(f.attrib["to"])
                else:
                    fila_links = [] # Empty the queue, as the flow will continue from this "case" onwards
                    print("Jumping the command = ", comando_from)
                    # Follows the flow of the success "case" looking for the "prox. link"
                    if not(busca_links(to_key)): # If there is no longer a link, the command indicated by "to_key" is the last one in the flow
                        exec_comando(busca_commando(to_key))
                        print("End of block.")
            else:
                print("Len de fila links:", len(fila_links))
                print("The element:", comando_from, " will be removed from queue.")
                fila_links.pop(0) # If the "case" failed, it is removed from the queue and consequently its flow is discarded
                print("false")
        else: # If the command was not a "case"
            print("The element:", comando_from, " will be removed from queue.")
            fila_links.pop(0) # Remove the link from the queue
            if not(busca_links(to_key)): # As previously mentioned
                exec_comando(busca_commando(to_key))
                print("End of block.")

    gui.terminal.insert(INSERT, "\nSTATE: End of script.")
    gui.terminal.see(tkinter.END)
    # Restore the buttons states (run and stop)
    gui.bt_run_sim['state'] = NORMAL
    gui.bt_run_sim.bind("<Button-1>", setSimMode)
    if ROBOT_MODE_ENABLED: gui.bt_run_robot['state'] = NORMAL
    gui.bt_run_robot.bind("<Button-1>", setEVAMode)
    gui.bt_import['state'] = NORMAL
    gui.bt_reload['state'] = NORMAL
    gui.bt_import.bind("<Button-1>", importFileThread)
    gui.bt_stop['state'] = DISABLED
    gui.bt_stop.unbind("<Button1>")


gui.mainloop()