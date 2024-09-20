from paho.mqtt import client as mqtt_client

from tkinter import *
from tkinter import messagebox 
import sys

sys.path.append('/home/marcelo/Insync/marcelo_rocha@midiacom.uff.br/Google Drive/UFF Doutorado MidiaCom/eva-robot-2024/evaml-evasim-sourcecode/version2.0/evasim_refatorado')

import platform 

import config  # Module with network device configurations.

broker = config.MQTT_BROKER_ADRESS # Broker address.
port = config.MQTT_PORT # Broker Port.
topic_base = config.SIMULATOR_TOPIC_BASE

# Position for graphical elements
x_pos = 95
y_pos = 27


# MQTT
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    # Subscribing in on_connect() means that if we lose the connection and
    # Reconnect then subscriptions will be renewed.
    client.subscribe(topic=[(topic_base + '/talk', 1), ])
    print("SIM - TTS - MsgBox - Connected.")
            

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    # if msg.topic == topic_base + '/light':
    # client.publish(topic_base + '/log', 'Controlling the Smart Bulb (color|state): ' + msg.payload.decode())
    # messagebox.showinfo("showinfo", (msg.payload.decode()).split("|")[1])
    # Window (GUI) creation
    # var = StringVar()
    pop = Toplevel(gui)
    pop.title("TTS - Message Box - EVA is speaking!")
    def close_window(self):
        pop.destroy()
    # Disable the maximize and close buttons
    # pop.resizable(False, False)
    # pop.protocol("WM_DELETE_WINDOW", False)
    text = msg.payload.decode().split("|")[1]
    w = len(text) * 8
    if w < 400:
        w = 400
    h = 120
    ws = gui.winfo_screenwidth()
    hs = gui.winfo_screenheight()
    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2) 
    pop.geometry('%dx%d+%d+%d' % (w, h, x, y))
    label = Label(pop, text='"' + text + '"', font = ('Arial', 12))
    label.pack(pady=5) # pady=20
    # Label(pop, image=gui.tts_eva_img).place(x=10, y=10)
    # E1 = Entry(pop, textvariable = var, font = ('Arial', 10))
    # E1.bind("<Return>", fechar_pop_ret)
    # E1.pack()
    Button(pop, text="    OK    ", font = gui.font1, command=pop.destroy).pack(pady=20) # 
    pop.bind("<Return>", close_window)


# Select the GUI definition file for the host operating system
if platform.system() == "Linux":
    print("Linux platform identified. Loading GUI formatting for Linux.")
    import gui_sim_tts_msg_linux as gui_sim_tts_msg # Definition of the graphical user interface (Linux)
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

gui = gui_sim_tts_msg.Gui(window) # Instance of the Gui class within the graphical user interface definition module

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

 # Draw the smart bulb
gui.canvas.create_image(x_pos, y_pos, image = gui.tts_msgbox)


gui.mainloop()