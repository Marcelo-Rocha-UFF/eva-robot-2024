import threading
import time

from paho.mqtt import client as mqtt_client

from tkinter import *
from  tkinter import ttk # Using tables

import hashlib
import os

from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import ApiException

import sys

sys.path.append('/home/marcelo/Insync/marcelo_rocha@midiacom.uff.br/Google Drive/UFF Doutorado MidiaCom/eva-robot-2024/evaml-evasim-sourcecode/version2.0/evasim_refatorado')

import platform 
import config # Module with network device configurations.

broker = config.MQTT_BROKER_ADRESS # Broker address.
port = config.MQTT_PORT # Broker Port.
topic_base = config.SIMULATOR_TOPIC_BASE
voice_tone = config.VOICE_TONE

x_pos = 95
y_pos = 30
event_anim_state = threading.Event() # used to start and stop threads

# Select the GUI definition file for the host operating system
if platform.system() == "Linux":
    print("Linux platform identified. Loading GUI formatting for Linux.")
    import gui_sim_tts_ibm_watson_linux as gui_sim_tts_ibm_watson # Definition of the graphical user interface (Linux)
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
gui = gui_sim_tts_ibm_watson.Gui(window) # Instance of the Gui class within the graphical user interface definition module


# Watson API configuration key.
with open("sim_tts_ibm_watson/ibm_cred.txt", "r") as ibm_cred: 
    ibm_config = ibm_cred.read().splitlines()
apikey = ibm_config[0]
url = ibm_config[1]

# Setup Watson service.
authenticator = IAMAuthenticator(apikey)

# TTS service.
tts = TextToSpeechV1(authenticator = authenticator)
tts.set_service_url(url)

auth_start_time = time.time() # Time of authentication.
first_requisition = True; # Indicates that this is the first request for the Watson service.
        

# MQTT
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    # Subscribing in on_connect() means that if we lose the connection and
    # Reconnect then subscriptions will be renewed.
    client.subscribe(topic=[(topic_base + '/talk', 1), ])
    print("SIM - Text-To-Speech Module - Connected.")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global voice_tone, auth_start_time, apikey, url, authenticator, tts, first_requisition
    if msg.topic == topic_base + '/talk':
        print("Using IBM Watson to convert text to audio...")
        # Assumes the default UTF-8 (Generates the hashing of the audio file).
        # Additionally, use the voice timbre attribute in the file hash.
        if len(msg.payload.decode().split("|")) == 2:
            voice_tone = msg.payload.decode().split("|")[0]
            msg.payload = (msg.payload.decode()).split("|")[1]
            msg.payload = msg.payload.encode()

        print("Voice:", voice_tone, "Message:", msg.payload.decode())
        hash_object = hashlib.md5(msg.payload)
        file_name = "_audio_"  + voice_tone + hash_object.hexdigest()
        
        audio_file_is_ok = False
        while(not audio_file_is_ok):
            # Checks if the speech audio already exists in the cache folder.
            if not (os.path.isfile("sim_tts_ibm_watson/tts_cache_files/" + file_name + config.WATSON_AUDIO_EXTENSION)): # If it doesn't exist, call Watson.
                print("The file is not cached... Let's try to generate it!")
                event_anim_state.set()
                # Criação de uma instância de Thread
                threading.Thread(target=anim, args=(event_anim_state,)).start()
                # Tests with the first request after a module reset (There is no problem in this way).
                # ================================================== ======================================
                # Watson appears to impose a limited connection time from the first request.
                # 1min of inactivity -> OK
                # 2min of inactivity -> OK
                # 8min of inactivity -> OK

                # Tests with one request from another, without resetting the module.
                # ================================================== ======================================
                # 3min of inactivity from the first request -> OK
                # 3.30min of inactivity from the first request -> OK
                # 4min of inactivity from a first req. -> Crashed! (Request rejected)
                # 5min of inactivity from the first request.-> Crashed! (Request rejected)

                # Checks if the module has been inactive for more than 3min (180s) since the first request.
                print(first_requisition, (time.time() - auth_start_time))
                if (not(first_requisition) and (time.time() - auth_start_time >= 180)):
                    print("The module has been inactive for more than 3 minutes (since the first request) and a new authentication will be performed.")
                    # Wtson API key (config.)
                    with open("sim_tts_ibm_watson/ibm_cred.txt", "r") as ibm_cred: 
                        ibm_config = ibm_cred.read().splitlines()
                    apikey = ibm_config[0]
                    url = ibm_config[1]
                    # Setup Watson service
                    authenticator = IAMAuthenticator(apikey)
                    # TTS service
                    tts = TextToSpeechV1(authenticator = authenticator)
                    tts.set_service_url(url)
                    first_requisition = False
                    auth_start_time = time.time() # Momento da autenticação.

                # Start the TTS process
                tts_start = time.time() # Variable used to mark the processing time of the TTS service.
                while(not audio_file_is_ok):
                    # Functions of the TTS service for EVA
                    with open("sim_tts_ibm_watson/tts_cache_files/" + file_name + config.WATSON_AUDIO_EXTENSION, 'wb') as audio_file:
                        try:
                            res = tts.synthesize(msg.payload.decode(), accept = config.ACCEPT_AUDIO_EXTENSION, voice = voice_tone).get_result()
                            print("Writing content to disk...")
                            audio_file.write(res.content)
                            file_size = os.path.getsize("sim_tts_ibm_watson/tts_cache_files/" + file_name + config.WATSON_AUDIO_EXTENSION)
                            print("File size:", file_size, " bytes.")
                            if file_size == 0: # Corrupted file!
                                print("#### Corrupted file....")
                                os.remove("sim_tts_ibm_watson/tts_cache_files/" + file_name + config.WATSON_AUDIO_EXTENSION)
                            else:
                                tts_ending = time.time()
                                client.publish(topic_base + "/log", "The audio was generated correctly in (s): %.2f" % (tts_ending - tts_start))
                                print("The file will be played!")
                                event_anim_state.clear()
                                client.publish(topic_base + "/log", "EVA is busy trying to speak the text: " + msg.payload.decode())
                                client.publish(topic_base + "/speech", file_name)
                                audio_file_is_ok = True
                                first_requisition = False
                        except ApiException as ex:
                            print ("The function failed with the following error code: " + str(ex.code) + ": " + ex.message)
                            exit(1)
            else:
                print("The file is cached!")
                if (os.path.getsize("sim_tts_ibm_watson/tts_cache_files/" + file_name + config.WATSON_AUDIO_EXTENSION)) == 0: # Corrupted file
                    print("The generated audio file is 0 bytes, corrupt and will be removed!")
                    os.remove("sim_tts_ibm_watson/tts_cache_files/" + file_name + config.WATSON_AUDIO_EXTENSION)
                else:
                    print("The file is more than 0 bytes and will be played now!")
                    client.publish(topic_base + "/log", "The audio was found in the cache.")
                    client.publish(topic_base + "/log", "EVA is busy trying to speak the text: " + msg.payload.decode())
                    client.publish(topic_base + "/speech", file_name)
                    audio_file_is_ok = True  


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


def anim(event):
    while(gui.estado == "running"):
        if event_anim_state.is_set():
            gui.canvas.create_image(x_pos, y_pos, image = gui.tts_ibm_1)
            time.sleep(0.4)
            gui.canvas.create_image(x_pos, y_pos, image = gui.tts_ibm_4)
            time.sleep(0.4)
            gui.canvas.create_image(x_pos, y_pos, image = gui.tts_ibm_0)
        else:
            return


# Draw the sound speaker
gui.canvas.create_image(x_pos, y_pos, image = gui.tts_ibm_0)

gui.mainloop()