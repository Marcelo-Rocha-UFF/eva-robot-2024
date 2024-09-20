import xml.etree.ElementTree as ET

import time

from paho.mqtt import client as mqtt_client

from tkinter import *
import tkinter

import sys
sys.path.append('/home/marcelo/Insync/marcelo_rocha@midiacom.uff.br/Google Drive/UFF Doutorado MidiaCom/eva-robot-2024/evaml-evasim-sourcecode/version2.0/evasim_refatorado')

import config # Module with network device settings
broker = config.MQTT_BROKER_ADRESS # broker adress
port = config.MQTT_PORT # broker port



# MQTT
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # Reconnect then subscriptions will be renewed.
    # client.subscribe(topic=[(topic_base + '/state', 1), ])
    # client.subscribe(topic=[(topic_base + '/var/dollar', 1), ])

client = mqtt_client.Client()
client.on_connect = on_connect
# client.on_message = on_message
client.connect(broker, port)
client.loop_start()

class NodeProcessing():
    def __init__(self):
        pass
    # topic_base may be SIM or EVA or FRED. It is defined in config.py file
    def process(self, topic_base = "SIM", node = None, terminal = None, memory = None): # process nodes
        ##############################################################################################################################################
        # Tag <voice> processing
        ##############################################################################################################################################
        if node.tag == "voice":
            terminal.insert(INSERT, "\nSTATE: Selected Voice => " + node.attrib["tone"])
            terminal.see(tkinter.END)
            terminal.insert(INSERT, "\nTIP: If the <talk> command doesn't speak some text, try emptying the audio_cache_files folder", "tip")
            if running_mode == "SIMULATOR":
                client.publish(topic_base + "/log", "Using the voice: " + node.attrib["tone"]) # 

        ##############################################################################################################################################
        # Tag <light> processing
        ##############################################################################################################################################
        elif node.tag == "light":
            state = node.attrib["state"]
            
            # lightEffect = "ON"
            # # Process light Effects settings
            # if root.find("settings").find("lightEffects") != None:
            #     if root.find("settings").find("lightEffects").attrib["mode"] == "OFF":
            #         lightEffect = "OFF"
            
            # Following case, if the state is off, and may not have a color attribute defined
            if state == "OFF":
                color = "BLACK"
                # if lightEffect == "OFF":
                #     message_state = "\nSTATE: Light Effects DISABLED."
                # else:
                message_state = "\nSTATE: Turnning off the light."
                terminal.insert(INSERT, message_state)
                terminal.see(tkinter.END)
            else:
                color = node.attrib["color"]
                # if lightEffect == "OFF":
                #     message_state = "\nSTATE: Light Effects DISABLED."
                #     state = "OFF"
                # else:
                message_state = "\nSTATE: Turnning on the light. Color = " + color + "."
                terminal.insert(INSERT, message_state)
                terminal.see(tkinter.END) # Autoscrolling
            
            client.publish(topic_base + "/light", color + "|" + state); # Command for the physical robot
            print("LIGHT", topic_base, color, state)
            if running_mode == "ROBOT":
                client.publish(topic_base + "/light", color + "|" + state); # Command for the physical robot
            else:
                time.sleep(0.1) # Emulates real bulb response time

        ##############################################################################################################################################
        # Tag <wait> processing
        ##############################################################################################################################################
        elif node.tag == "wait":
            duration = node.attrib["duration"]
            terminal.insert(INSERT, "\nSTATE: Pausing. Duration = " + duration + " ms")
            terminal.see(tkinter.END)
            time.sleep(int(duration)/1000) # Convert to seconds

        ##############################################################################################################################################
        # Tag <led> processing
        ##############################################################################################################################################
        # elif node.tag == "led":
        #     animation = node.attrib["animation"]
        #     terminal.insert(INSERT, "\nSTATE: Matrix Leds. Animation = " + node.attrib["animation"])
        #     terminal.see(tkinter.END)

        #     if running_mode == "ROBOT":
        #         # client.publish(topic_base + "/leds", "STOP")
        #         # client.publish(topic_base + "/leds", animation)
        #     if animation == "STOP":
        #         client.publish(topic_base + "/leds", "STOP") 
        #         evaMatrix("grey")
        #     elif animation == "LISTEN":
        #         evaMatrix("green")
        #     elif animation == "SPEAK":
        #         evaMatrix("blue")
        #     elif animation == "ANGRY" or animation == "ANGRY2":
        #         evaMatrix("red")
        #     elif animation == "HAPPY":
        #         evaMatrix("green")
        #     elif animation == "SAD":
        #         evaMatrix("blue")
        #     elif animation == "SURPRISE":
        #         evaMatrix("yellow")
        #     elif animation == "WHITE":
        #         evaMatrix("white")
        #     elif animation == "RAINBOW":
        #         evaMatrix("white")
        #         print("Falta gerar a imagem do RAINBOW para os leds do EvaSIM")
        #     else: print("A wrong led animation was selected.")