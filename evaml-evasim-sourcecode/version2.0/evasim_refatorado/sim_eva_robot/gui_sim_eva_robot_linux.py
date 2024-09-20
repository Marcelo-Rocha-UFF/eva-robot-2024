from tkinter import *
import tkinter
from  tkinter import ttk # Using tables

import sys

sys.path.append('/home/marcelo/Insync/marcelo_rocha@midiacom.uff.br/Google Drive/UFF Doutorado MidiaCom/eva-robot-2024/evaml-evasim-sourcecode/version2.0/evasim_refatorado')


# Closing application
def on_closing(window):
    # if messagebox.askokcancel("Quit", "Do you want to quit?"):
    print("Eva says: Bye bye!")
    window.destroy()
    

# Graphical user interface class
class Gui(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        parent.title("EVA Robot - Body Simulation")
        self.w = 440
        self.h = 705
        parent.geometry(str(self.w) + "x" + str(self.h) + "+0+210")

        # Define the closing app function
        parent.protocol("WM_DELETE_WINDOW", lambda: on_closing(parent)) 

        # Does not show the minimize button
        parent.resizable(0,0)

        # Font size 10 for buttons and texts in general
        self.font1 = ('Arial', 10)

        # Setting the default font for application
        parent.option_add( "*font", "Arial 9")

        # EVA expressions images
        self.im_eyes_neutral = PhotoImage(file = "images/eyes_neutral.png")
        self.im_eyes_angry = PhotoImage(file = "images/eyes_angry.png")
        self.im_eyes_sad = PhotoImage(file = "images/eyes_sad.png")
        self.im_eyes_happy = PhotoImage(file = "images/eyes_happy.png")
        self.im_eyes_fear = PhotoImage(file = "images/eyes_fear.png")
        self.im_eyes_surprise = PhotoImage(file = "images/eyes_surprise.png")
        self.im_eyes_disgust = PhotoImage(file = "images/eyes_disgust.png")
        self.im_eyes_inlove = PhotoImage(file = "images/eyes_inlove.png")
        self.im_eyes_on = PhotoImage(file = "images/eyes_on.png")


        # Matrix Voice images
        self.im_matrix_blue = PhotoImage(file = "images/matrix_blue.png")
        self.im_matrix_green = PhotoImage(file = "images/matrix_green.png")
        self.im_matrix_yellow = PhotoImage(file = "images/matrix_yellow.png")
        self.im_matrix_white = PhotoImage(file = "images/matrix_white.png")
        self.im_matrix_red = PhotoImage(file = "images/matrix_red.png")
        self.im_matrix_grey = PhotoImage(file = "images/matrix_grey.png")
        self.im_bt_play = PhotoImage(file = "images/bt_play.png")
        self.im_bt_stop = PhotoImage(file = "images/bt_stop.png")

        # Defining the image files
        self.eva_image = PhotoImage(file = "images/eva.png")
        # self.background_image = PhotoImage(file = "images/background_cartoon.png")
        # self.background_image = PhotoImage(file = "images/background_night.png")
        # self.background_image = PhotoImage(file = "images/background_day.png")
        self.background_image = PhotoImage(file = "images/background_night2.png") 

        # Define the top frame
        self.frame_top = tkinter.Frame(master=parent) #self.h

        self.frame_top.pack(side=tkinter.TOP)
        # self.frame_bottom.pack(side=tkinter.TOP, pady = 0)

        # Define the frame that will accommodate the canvas with the EVA image
        self.frame_robot = tkinter.Frame(master=self.frame_top, width= 360) #self.h

        self.frame_robot.pack(side=tkinter.LEFT)

        # Creating the graphic canvas
        self.canvas = Canvas(self.frame_robot, width = 430, height = 900) # Canvas is necessary to use images with transparency
        self.canvas.pack(side=tkinter.LEFT, pady= 5)
        
        # Draw the eva and the background
        self.canvas.create_image(205, 350, image=self.background_image)
        self.canvas.create_image(220, 360, image = self.eva_image)


