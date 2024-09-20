from tkinter import *
import tkinter
from  tkinter import ttk # Using tables

# Closing application
def on_closing(window, self):
    # if messagebox.askokcancel("Quit", "Do you want to quit?"):
    print("Eva says: Bye bye!")
    self.estado = "stopped"
    window.destroy()
    

# Graphical user interface class
class Gui(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        parent.title("TTS - IBM Watson")
        self.w = 190
        self.h = 75
        self.estado = "running"
        parent.geometry(str(self.w) + "x" + str(self.h))

        # Define the closing app function
        parent.protocol("WM_DELETE_WINDOW", lambda: on_closing(parent, self)) 

        # Does not show the minimize button
        parent.resizable(0,0)

        # Font size 10 for buttons and texts in general
        self.font1 = ('Arial', 10)

        # Setting the default font for application
        parent.option_add( "*font", "Arial 9")

        # Define the top frame
        self.frame_top = tkinter.Frame(master=parent) #self.h

        self.frame_top.pack(side=tkinter.TOP)

        # Defining the image files
        self.tts_ibm_0 = PhotoImage(file = "images/tts_ibm_0.png")
        self.tts_ibm_1 = PhotoImage(file = "images/tts_ibm_1.png")
        self.tts_ibm_2 = PhotoImage(file = "images/tts_ibm_2.png")
        self.tts_ibm_3 = PhotoImage(file = "images/tts_ibm_3.png")
        self.tts_ibm_4 = PhotoImage(file = "images/tts_ibm_4.png")

        # Define the frame that will accommodate the canvas with the EVA image
        self.frame_robot = tkinter.Frame(master=self.frame_top, width= 360) #self.h

        self.frame_robot.pack(side=tkinter.LEFT)

        # Creating the graphic canvas
        self.canvas = Canvas(self.frame_robot, width = 430, height = 900) # Canvas is necessary to use images with transparency
        self.canvas.pack(side=tkinter.LEFT)
        
       
        


