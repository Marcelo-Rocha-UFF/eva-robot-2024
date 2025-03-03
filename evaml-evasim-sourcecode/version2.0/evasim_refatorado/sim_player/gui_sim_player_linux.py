from tkinter import *
from tkinter import messagebox
import tkinter
from  tkinter import ttk # Using tables

# Closing application
def on_closing(window):
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        print("Eva says: Bye bye!")
        window.destroy()

# Graphical user interface class
class Gui(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        parent.title("Embodied Voice Assistant Simulator - Script Player for EvaML - Version 2.0 - UFF / MidiaCom / CICESE")
        self.w = 1270
        self.h = 620
        parent.geometry(str(self.w) + "x" + str(self.h))

        # Define the closing app function
        parent.protocol("WM_DELETE_WINDOW", lambda: on_closing(parent)) 

        # Does not show the minimize button
        parent.resizable(0,0)

        # Font size 10 for buttons and texts in general
        self.font1 = ('Arial', 10)

        # Setting the default font for application
        parent.option_add( "*font", "Arial 9")

        # # Defining the image files
        # self.eva_image = PhotoImage(file = "images/eva.png") 
        # self.bulb_image = PhotoImage(file = "images/bulb.png")
        # self.eva_woz = PhotoImage(file = "images/eva_woz.png")
        # Eva expressions images
        # self.im_eyes_neutral = PhotoImage(file = "images/eyes_neutral.png")
        # self.im_eyes_angry = PhotoImage(file = "images/eyes_angry.png")
        # self.im_eyes_sad = PhotoImage(file = "images/eyes_sad.png")
        # self.im_eyes_happy = PhotoImage(file = "images/eyes_happy.png")
        # self.im_eyes_on = PhotoImage(file = "images/eyes_on.png")
        # self.im_eyes_happy = PhotoImage(file = "images/eyes_fear.png")
        # self.im_eyes_disgust = PhotoImage(file = "images/eyes_disgust.png")
        # self.im_eyes_inlove = PhotoImage(file = "images/eyes_inlove.png")
        # self.im_eyes_on = PhotoImage(file = "images/eyes_surprise.png")
        # Button images
        # self.im_eyes_neutral_btn = PhotoImage(file = "images/eyes_neutral_btn.png")
        # self.im_eyes_angry_btn = PhotoImage(file = "images/eyes_angry_btn.png")
        # self.im_eyes_sad_btn = PhotoImage(file = "images/eyes_sad_btn.png")
        # self.im_eyes_happy_btn = PhotoImage(file = "images/eyes_happy_btn.png")
        # self.im_eyes_fear_btn = PhotoImage(file = "images/eyes_fear_btn.png")
        # self.im_eyes_surprise_btn = PhotoImage(file = "images/eyes_surprise_btn.png")
        # self.im_eyes_disgust_btn = PhotoImage(file = "images/eyes_disgust_btn.png")
        # self.im_eyes_inlove_btn = PhotoImage(file = "images/eyes_inlove_btn.png")
        
        # # Matrix Voice images
        # self.im_matrix_blue = PhotoImage(file = "images/matrix_blue.png")
        # self.im_matrix_green = PhotoImage(file = "images/matrix_green.png")
        # self.im_matrix_yellow = PhotoImage(file = "images/matrix_yellow.png")
        # self.im_matrix_white = PhotoImage(file = "images/matrix_white.png")
        # self.im_matrix_red = PhotoImage(file = "images/matrix_red.png")
        # self.im_matrix_grey = PhotoImage(file = "images/matrix_grey.png")

        self.im_bt_play = PhotoImage(file = "images/bt_play.png")
        self.im_bt_play_robot = PhotoImage(file = "images/bt_play_robot.png")
        self.im_bt_reload = PhotoImage(file = "images/bt_reload.png")
        self.im_bt_stop = PhotoImage(file = "images/bt_stop.png")


        # Define the top frame
        self.frame_top = tkinter.Frame(master=parent) #self.h
        # # define o frame bottom (Woz)
        # self.frame_bottom = tkinter.Frame(master=parent) #self.h
        # Pack Top and Bottom frames
        self.frame_top.pack(side=tkinter.TOP)
        # self.frame_bottom.pack(side=tkinter.TOP, pady = 10)

        # # Define the frame that will accommodate the canvas with the EVA image
        # self.frame_robot = tkinter.Frame(master=self.frame_top, width= 400) #self.h
        # Define the frame for the terminal and the button menu
        self.frame_centro = tkinter.Frame(master=self.frame_top, width= 750, height=self.h)
        # Define the frame for the memory tables
        self.frame_memory = tkinter.Frame(master=self.frame_top, width= 180, height=self.h)
        # Pack frames
        # self.frame_robot.pack(side=tkinter.LEFT)
        self.frame_centro.pack(side=tkinter.LEFT, padx=10) # fill=tkinter.Y,
        self.frame_memory.pack(side=tkinter.LEFT) # self.frame_memory.place(x=1100, y=60)
        # Creating the graphic canvas
        # self.canvas = Canvas(self.frame_robot, width = 400, height = 510) # Canvas is necessary to use images with transparency
        # self.canvas.pack(side=tkinter.LEFT, pady= 30)

        # Define the frames for the Bottom frame
        # Frame with expressions
        # self.frame_exp = tkinter.Frame(master=self.frame_bottom) #self.h
        # # Frame with Leds
        # self.frame_leds = tkinter.Frame(master=self.frame_bottom) #self.h
        # # Frame with bulb colors
        # self.frame_lampada = tkinter.Frame(master=self.frame_bottom) #self.h
        # # Frame with arm movement buttons
        # self.frame_arms_motion = tkinter.Frame(master=self.frame_bottom) #self.h
        # # Frame with head movement buttons
        # self.frame_head_motion = tkinter.Frame(master=self.frame_bottom) #self.h
        # # Frame with the speak button
        # self.frame_tts = tkinter.Frame(master=self.frame_bottom) #self.h
        # # Pack frames
        # self.frame_canvas_woz = tkinter.Frame(master=self.frame_bottom) #self.h

        # Pack frames
        # self.frame_exp.pack(side=tkinter.LEFT)
        # self.frame_leds.pack(side=tkinter.LEFT)
        # self.frame_lampada.pack(side=tkinter.LEFT)
        # self.frame_arms_motion.pack(side=tkinter.LEFT)
        # self.frame_head_motion.pack(side=tkinter.LEFT)
        # self.frame_tts.pack(side=tkinter.LEFT)
        # self.frame_canvas_woz.pack(side=tkinter.LEFT)

        # lfs_padx = 6
        # # Label frame expressions
        # self.lf_exp = LabelFrame(self.frame_exp, text = 'EVA Expressions', font = self.font1)
        # self.lf_exp.pack(side=tkinter.LEFT, padx=lfs_padx)
        # # Buttons with expressions
        # btn_exp_w = 60
        # btn_exp_pady = 0
        # self.bt_exp_neutral = Button (self.lf_exp, text = "Neutral", width = btn_exp_w, image = self.im_eyes_neutral_btn,font = self.font1, compound = TOP)
        # self.bt_exp_neutral.grid(row=0, column=0, padx=4, pady=btn_exp_pady)
        # self.bt_exp_happy = Button (self.lf_exp, text = "Happy", width = btn_exp_w, image = self.im_eyes_happy_btn,font = self.font1, compound = TOP)
        # self.bt_exp_happy.grid(row=0, column=1, padx=4, pady=btn_exp_pady)
        # self.bt_exp_angry = Button (self.lf_exp, text = "Angry", width = btn_exp_w, image = self.im_eyes_angry_btn,font = self.font1, compound = TOP)
        # self.bt_exp_angry.grid(row=1, column=0, padx=4, pady=btn_exp_pady)
        # self.bt_exp_sad = Button (self.lf_exp, text = "Sad", width = btn_exp_w, image = self.im_eyes_sad_btn,font = self.font1, compound = TOP)
        # self.bt_exp_sad.grid(row=1, column=1, padx=4, pady=btn_exp_pady)
        # self.bt_exp_fear = Button (self.lf_exp, text = "Fear", width = btn_exp_w, image = self.im_eyes_fear_btn,font = self.font1, compound = TOP)
        # self.bt_exp_fear.grid(row=2, column=0, padx=4, pady=btn_exp_pady)
        # self.bt_exp_surprise = Button (self.lf_exp, text = "Surprise", width = btn_exp_w, image = self.im_eyes_surprise_btn,font = self.font1, compound = TOP)
        # self.bt_exp_surprise.grid(row=2, column=1, padx=4, pady=btn_exp_pady)
        # self.bt_exp_disgust = Button (self.lf_exp, text = "Disgust", width = btn_exp_w, image = self.im_eyes_disgust_btn,font = self.font1, compound = TOP)
        # self.bt_exp_disgust.grid(row=3, column=0, padx=4, pady=btn_exp_pady)
        # self.bt_exp_inlove = Button (self.lf_exp, text = "In Love", width = btn_exp_w, image = self.im_eyes_inlove_btn,font = self.font1, compound = TOP)
        # self.bt_exp_inlove.grid(row=3, column=1, padx=4, pady=btn_exp_pady)

        # # Label frame Leds
        # self.lf_leds = LabelFrame(self.frame_leds, text = 'RGB Leds Animations', font = self.font1)
        # self.lf_leds.pack(side=tkinter.LEFT, padx=lfs_padx)
        # # Buttons with Leds
        # btn_led_w = 7
        # btn_led_h = 2
        # btn_led_pady = 4
        # self.bt_led_happy = Button (self.lf_leds, foreground = "green" , width = btn_led_w, height = btn_led_h, text = "HAPPY",font = self.font1, compound = LEFT)
        # self.bt_led_happy.grid(row=0, column=0, padx=4, pady=btn_led_pady)
        # self.bt_led_sad = Button (self.lf_leds, foreground = "blue" , width = btn_led_w,  height = btn_led_h,  text = "SAD",font = self.font1, compound = LEFT)
        # self.bt_led_sad.grid(row=0, column=1, padx=4, pady=btn_led_pady)
        # self.bt_led_angry = Button (self.lf_leds, foreground = "red" , width = btn_led_w,  height = btn_led_h, text = "ANGRY",font = self.font1, compound = LEFT)
        # self.bt_led_angry.grid(row=1, column=0, padx=4, pady=btn_led_pady)
        # self.bt_led_angry2 = Button (self.lf_leds, foreground = "red" , width = btn_led_w,  height = btn_led_h, text = "ANGRY2",font = self.font1, compound = LEFT)
        # self.bt_led_angry2.grid(row=1, column=1, padx=4, pady=btn_led_pady)
        # self.bt_led_stop = Button (self.lf_leds, foreground = "black" , width = btn_led_w,  height = btn_led_h, text = "STOP",font = self.font1, compound = LEFT)
        # self.bt_led_stop.grid(row=2, column=0, padx=4, pady=btn_led_pady)
        # self.bt_led_speak = Button (self.lf_leds, foreground = "blue" , width = btn_led_w,  height = btn_led_h, text = "SPEAK",font = self.font1, compound = LEFT)
        # self.bt_led_speak.grid(row=2, column=1, padx=4, pady=btn_led_pady)
        # self.bt_led_listen = Button (self.lf_leds, foreground = "green" , width = btn_led_w,  height = btn_led_h, text = "LISTEN",font = self.font1, compound = LEFT)
        # self.bt_led_listen.grid(row=3, column=0, padx=4, pady=btn_led_pady)
        # self.bt_led_surprise = Button (self.lf_leds, foreground = "yellow" , width = btn_led_w,  height = btn_led_h, text = "SURPRISE",font = self.font1, compound = LEFT)
        # self.bt_led_surprise.grid(row=3, column=1, padx=4, pady=btn_led_pady)
        # self.bt_led_white = Button (self.lf_leds, foreground = "white" , width = btn_led_w,  height = btn_led_h, text = "WHITE",font = self.font1, compound = LEFT)
        # self.bt_led_white.grid(row=4, column=0, padx=4, pady=btn_led_pady)
        # self.bt_led_rainbow = Button (self.lf_leds, foreground = "black" , width = btn_led_w,  height = btn_led_h, text = "RAINBOW",font = self.font1, compound = LEFT)
        # self.bt_led_rainbow.grid(row=4, column=1, padx=4, pady=btn_led_pady)
        

        # # Label frame bulb
        # btn_bulb_padx = 4
        # btn_bulb_pady = 11
        # self.lf_bulb = LabelFrame(self.frame_lampada, text = 'Smart Bulb Colors', font = self.font1)
        # self.lf_bulb.pack(side=tkinter.LEFT, padx=lfs_padx)
        # # Buttons with bulbs
        # btn_bulb_h = 2
        # btn_bulb_w = 3
        # self.bt_bulb_white_btn = Button (self.lf_bulb, bg='white', width = btn_bulb_w, height = btn_bulb_h,font = self.font1)
        # self.bt_bulb_white_btn.grid(row=0, column=0, padx=btn_bulb_padx, pady=btn_bulb_pady)
        # self.bt_bulb_off_btn = Button (self.lf_bulb, bg='black', width = btn_bulb_w, height = btn_bulb_h,font = self.font1)
        # self.bt_bulb_off_btn.grid(row=0, column=1, padx=btn_bulb_padx, pady=btn_bulb_pady)
        # self.bt_bulb_red_btn = Button (self.lf_bulb, bg='red', width = btn_bulb_w, height = btn_bulb_h,font = self.font1)
        # self.bt_bulb_red_btn.grid(row=1, column=0, padx=btn_bulb_padx, pady=btn_bulb_pady)
        # self.bt_bulb_pink_btn = Button (self.lf_bulb, bg='#ed30cf', width = btn_bulb_w, height = btn_bulb_h,font = self.font1)
        # self.bt_bulb_pink_btn.grid(row=1, column=1, padx=btn_bulb_padx, pady=btn_bulb_pady)
        # self.bt_bulb_green_btn = Button (self.lf_bulb, bg='#3ded97', width = btn_bulb_w, height = btn_bulb_h,font = self.font1)
        # self.bt_bulb_green_btn.grid(row=2, column=0, padx=btn_bulb_padx, pady=btn_bulb_pady)
        # self.bt_bulb_yellow_btn = Button (self.lf_bulb, bg='yellow', width = btn_bulb_w, height = btn_bulb_h,font = self.font1)
        # self.bt_bulb_yellow_btn.grid(row=2, column=1, padx=btn_bulb_padx, pady=btn_bulb_pady)
        # self.bt_bulb_blue_btn = Button (self.lf_bulb, bg='blue', width = btn_bulb_w, height = btn_bulb_h,font = self.font1)
        # self.bt_bulb_blue_btn.grid(row=3, column=0, padx=btn_bulb_padx, pady=btn_bulb_pady)
        

        # # Arms motion frame
        # btn_arms_motion_padx = 2
        # btn_arms_motion_pady = 2
        # self.lf_arms_motion = LabelFrame(self.frame_arms_motion, text = 'Arms Motion', font = self.font1)
        # self.lf_arms_motion.pack(side=tkinter.LEFT, padx=lfs_padx)
        # # Buttons with arm movements
        # btn_arms_motion_w = 6
        # btn_arms_motion_h = 1
        # self.lbl_arm_left = tkinter.Label(self.lf_arms_motion, bg="gray70", width=btn_arms_motion_w + 3, font = self.font1, text="LEFT", padx=btn_arms_motion_padx, pady=btn_arms_motion_pady)
        # self.lbl_arm_left.grid(row=0, column=0, padx=btn_arms_motion_padx, pady=btn_arms_motion_pady + 2)
        # self.lbl_arm_right = tkinter.Label(self.lf_arms_motion, bg="gray70", width=btn_arms_motion_w + 3, font = self.font1, text="RIGHT", padx=btn_arms_motion_padx, pady=btn_arms_motion_pady)
        # self.lbl_arm_right.grid(row=0, column=1, padx=btn_arms_motion_padx, pady=btn_arms_motion_pady + 2)

        # self.bt_arm_left_motion_pos_0 = Button (self.lf_arms_motion, width = btn_arms_motion_w, height = btn_arms_motion_h, text = 'P0',font = self.font1)
        # self.bt_arm_left_motion_pos_0.grid(row=1, column=0, padx=btn_arms_motion_padx, pady=btn_arms_motion_pady)
        # self.bt_arm_right_motion_pos_0 = Button (self.lf_arms_motion, width = btn_arms_motion_w, height = btn_arms_motion_h, text = 'P0',font = self.font1)
        # self.bt_arm_right_motion_pos_0.grid(row=1, column=1, padx=btn_arms_motion_padx, pady=btn_arms_motion_pady)
        # self.bt_arm_left_motion_pos_1 = Button (self.lf_arms_motion, width = btn_arms_motion_w, height = btn_arms_motion_h, text = 'P1',font = self.font1)
        # self.bt_arm_left_motion_pos_1.grid(row=2, column=0, padx=btn_arms_motion_padx, pady=btn_arms_motion_pady)
        # self.bt_arm_right_motion_pos_1 = Button (self.lf_arms_motion, width = btn_arms_motion_w, height = btn_arms_motion_h, text = 'P1',font = self.font1)
        # self.bt_arm_right_motion_pos_1.grid(row=2, column=1, padx=btn_arms_motion_padx, pady=btn_arms_motion_pady)

        # self.bt_arm_left_motion_pos_2 = Button (self.lf_arms_motion, width = btn_arms_motion_w, height = btn_arms_motion_h, text = 'P2',font = self.font1)
        # self.bt_arm_left_motion_pos_2.grid(row=3, column=0, padx=btn_arms_motion_padx, pady=btn_arms_motion_pady)
        # self.bt_arm_right_motion_pos_2 = Button (self.lf_arms_motion, width = btn_arms_motion_w, height = btn_arms_motion_h, text = 'P2',font = self.font1)
        # self.bt_arm_right_motion_pos_2.grid(row=3, column=1, padx=btn_arms_motion_padx, pady=btn_arms_motion_pady)
        # self.bt_arm_left_motion_pos_3 = Button (self.lf_arms_motion, width = btn_arms_motion_w, height = btn_arms_motion_h, text = 'P3',font = self.font1)
        # self.bt_arm_left_motion_pos_3.grid(row=4, column=0, padx=btn_arms_motion_padx, pady=btn_arms_motion_pady)
        # self.bt_arm_right_motion_pos_3 = Button (self.lf_arms_motion, width = btn_arms_motion_w, height = btn_arms_motion_h, text = 'P3',font = self.font1)
        # self.bt_arm_right_motion_pos_3.grid(row=4, column=1, padx=btn_arms_motion_padx, pady=btn_arms_motion_pady)

        # self.bt_arm_left_motion_up = Button (self.lf_arms_motion, width = btn_arms_motion_w, height = btn_arms_motion_h, text = 'UP',font = self.font1)
        # self.bt_arm_left_motion_up.grid(row=7, column=0, padx=btn_arms_motion_padx, pady=btn_arms_motion_pady)
        # self.bt_arm_right_motion_up = Button (self.lf_arms_motion, width = btn_arms_motion_w, height = btn_arms_motion_h, text = 'UP',font = self.font1)
        # self.bt_arm_right_motion_up.grid(row=7, column=1, padx=btn_arms_motion_padx, pady=btn_arms_motion_pady)

        # self.bt_arm_left_motion_down = Button (self.lf_arms_motion, width = btn_arms_motion_w, height = btn_arms_motion_h, text = 'DOWN',font = self.font1)
        # self.bt_arm_left_motion_down.grid(row=8, column=0, padx=btn_arms_motion_padx, pady=btn_arms_motion_pady)
        # self.bt_arm_right_motion_down = Button (self.lf_arms_motion, width = btn_arms_motion_w, height = btn_arms_motion_h, text = 'DOWN',font = self.font1)
        # self.bt_arm_right_motion_down.grid(row=8, column=1, padx=btn_arms_motion_padx, pady=btn_arms_motion_pady)

        # self.bt_arm_left_motion_shake = Button (self.lf_arms_motion, width = btn_arms_motion_w, height = btn_arms_motion_h, text = '2 x SHAKE',font = self.font1)
        # self.bt_arm_left_motion_shake.grid(row=9, column=0, padx=btn_arms_motion_padx, pady=btn_arms_motion_pady)
        # self.bt_arm_right_motion_shake = Button (self.lf_arms_motion, width = btn_arms_motion_w, height = btn_arms_motion_h, text = '2 x SHAKE',font = self.font1)
        # self.bt_arm_right_motion_shake.grid(row=9, column=1, padx=btn_arms_motion_padx, pady=btn_arms_motion_pady)
        

        # # Head motion frame
        # btn_head_motion_padx = 0
        # btn_head_motion_pady = 0
        # self.lf_head_motion = LabelFrame(self.frame_head_motion, text = 'Head Motion', font = self.font1)
        # self.lf_head_motion.pack(side=tkinter.LEFT, padx=lfs_padx)
        # # Buttons with head movements
        # btn_head_motion_w = 10
        # btn_head_motion_h = 2
        # self.bt_head_motion_up_left = Button (self.lf_head_motion, width = btn_head_motion_w, height = btn_head_motion_h, text = 'UP/LEFT',font = self.font1)
        # self.bt_head_motion_up_left.grid(row=0, column=0, padx=btn_head_motion_padx, pady=btn_head_motion_pady)
        # self.bt_head_motion_up = Button (self.lf_head_motion,  width = btn_head_motion_w, height = btn_head_motion_h, text = 'UP', font = self.font1)
        # self.bt_head_motion_up.grid(row=0, column=1, padx=btn_head_motion_padx, pady=btn_head_motion_pady)
        # self.bt_head_motion_2up = Button (self.lf_head_motion,  width = btn_head_motion_w, height = btn_head_motion_h, text = '2 x UP', font = self.font1)
        # self.bt_head_motion_2up.grid(row=0, column=2, padx=btn_head_motion_padx, pady=btn_head_motion_pady)
        # self.bt_head_motion_up_right = Button (self.lf_head_motion,  width = btn_head_motion_w, height = btn_head_motion_h, text = 'UP/RIGHT', font = self.font1)
        # self.bt_head_motion_up_right.grid(row=0, column=3, padx=btn_head_motion_padx, pady=btn_head_motion_pady)
        # self.bt_head_motion_left = Button (self.lf_head_motion,  width = btn_head_motion_w, height = btn_head_motion_h, text = 'LEFT', font = self.font1)
        # self.bt_head_motion_left.grid(row=1, column=0, padx=btn_head_motion_padx, pady=btn_head_motion_pady)
        # self.bt_head_motion_center = Button (self.lf_head_motion,  width = 2 * btn_head_motion_w + 5, height = 5,  text = 'CENTER', font = self.font1)
        # self.bt_head_motion_center.grid(row=1, column=1, padx=btn_head_motion_padx, pady=btn_head_motion_pady, columnspan = 2, rowspan = 2)
        # self.bt_head_motion_2left = Button (self.lf_head_motion,  width = btn_head_motion_w, height = btn_head_motion_h, text = '2 x LEFT', font = self.font1)
        # self.bt_head_motion_2left.grid(row=2, column=0, padx=btn_head_motion_padx, pady=btn_head_motion_pady)
        # self.bt_head_motion_right = Button (self.lf_head_motion,  width = btn_head_motion_w, height = btn_head_motion_h, text = 'RIGHT', font = self.font1)
        # self.bt_head_motion_right.grid(row=1, column=3, padx=btn_head_motion_padx, pady=btn_head_motion_pady)
        # self.bt_head_motion_2right = Button (self.lf_head_motion,  width = btn_head_motion_w, height = btn_head_motion_h, text = '2 x RIGHT', font = self.font1)
        # self.bt_head_motion_2right.grid(row=2, column=3, padx=btn_head_motion_padx, pady=btn_head_motion_pady)
        # self.bt_head_motion_down_left = Button (self.lf_head_motion,  width = btn_head_motion_w, height = btn_head_motion_h, text = 'DOWN/LEFT', font = self.font1)
        # self.bt_head_motion_down_left.grid(row=3, column=0, padx=btn_head_motion_padx, pady=btn_head_motion_pady)
        # self.bt_head_motion_down = Button (self.lf_head_motion,  width = btn_head_motion_w, height = btn_head_motion_h, text = 'DOWN', font = self.font1)
        # self.bt_head_motion_down.grid(row=3, column=1, padx=btn_head_motion_padx, pady=btn_head_motion_pady)
        # self.bt_head_motion_2down = Button (self.lf_head_motion,  width = btn_head_motion_w, height = btn_head_motion_h, text = '2 x DOWN', font = self.font1)
        # self.bt_head_motion_2down.grid(row=3, column=2, padx=btn_head_motion_padx, pady=btn_head_motion_pady)
        # self.bt_head_motion_down_right = Button (self.lf_head_motion,  width = btn_head_motion_w, height = btn_head_motion_h, text = 'DOWN/RIGHT', font = self.font1)
        # self.bt_head_motion_down_right.grid(row=3, column=3, padx=btn_head_motion_padx, pady=btn_head_motion_pady)
        # self.bt_head_motion_yes = Button (self.lf_head_motion, foreground="green", width = 2 * btn_head_motion_w + 5, height = 4, text = '2 x YES', font = self.font1)
        # self.bt_head_motion_yes.grid(row=4, column=0, padx=btn_head_motion_padx, pady=btn_head_motion_pady + 2, columnspan=2, rowspan=2)
        # self.bt_head_motion_no = Button (self.lf_head_motion, foreground="red", width = 2 * btn_head_motion_w + 5, height = 4, text = '2 x NO', font = self.font1)
        # self.bt_head_motion_no.grid(row=4, column=2, padx=btn_head_motion_padx, pady=btn_head_motion_pady + 2, columnspan=2, rowspan=2)


        # # Label frame TTS
        # self.lf_tts = LabelFrame(self.frame_tts, text = 'Text-To-Speech (TTS) - IBM Watson Service', font = self.font1)
        # self.lf_tts.pack(side=tkinter.LEFT, padx=lfs_padx)
        
        # self.lbl_voice_options = tkinter.Label(self.lf_tts, bg="gray70", width="20", font = self.font1, text="Voice Options", padx=5, pady=2)
        # self.lbl_voice_options.grid(row=0, column=0)
        
        # self.Lb_voices = Listbox(self.lf_tts, width= 21, height=12, font="Arial 10")
        # self.Lb_voices.insert(1, "en-US_AllisonV3Voice")
        # self.Lb_voices.insert(2, "en-US_EmmaExpressive")
        # self.Lb_voices.insert(3, "en-US_MichaelExpressive")
        # self.Lb_voices.insert(4, "en-US_HenryV3Voice")
        # self.Lb_voices.insert(5, "pt-BR_IsabelaV3Voice")
        # self.Lb_voices.insert(6, "es-ES_LauraV3Voice")
        # self.Lb_voices.insert(7, "es-ES_EnriqueV3Voice")
        # self.Lb_voices.grid(row=1, column=0,  rowspan=2, padx=5) #expand=True, fill=tkinter.BOTH
        # self.Lb_voices.selection_set(4)

        # tkinter.Label(self.lf_tts, width="30", font = self.font1, text="Text to speech:", pady=2).grid(row=0, column=1)
        # self.msg_tts_text = Text(self.lf_tts, height = 10, width=30, font="Arial 10")
        # self.msg_tts_text.grid(row=1, column=1)
        # self.bt_send_tts = Button (self.lf_tts, width=27, text = 'SEND (Speak)', font = self.font1)
        # self.bt_send_tts.grid(row=2, column=1)

        # # Canva for EVA WoZ image
        # self.canvas_woz = Canvas(self.frame_canvas_woz) # o canvas e' necessario para usar imagens com transparencia
        # self.canvas_woz.pack(side=tkinter.LEFT)
        # self.canvas_woz.create_image(95, 120, image = self.eva_woz)

        # Define the frame for the button menu
        self.frame_botoes = tkinter.Frame(master=self.frame_centro)
        self.frame_botoes.pack(pady=15, padx=10)

        # Define the frame for the terminal
        self.frame_terminal = tkinter.Frame(master=self.frame_centro)
        self.frame_terminal.pack(fill=tkinter.X)


        # Create the memory table
        # Define the table properties with the $ memory map
        tkinter.Label(self.frame_memory, bg="gray70", width="48", font = self.font1, text="System Variables $ (Memory Map)", pady=1).pack()

        # Define the table style
        style = ttk.Style()
        style.configure("mystyle.Treeview", highlightthickness=0, bd=0, font=('Arial', 10), rowheight=15) # Modify the font of the body
        style.configure("mystyle.Treeview.Heading", font=('Arial', 8,'bold')) # Modify the font of the headings
        self.tab_dollar = ttk.Treeview(self.frame_memory, style="mystyle.Treeview", height=18)
        self.tab_dollar.pack()

        self.tab_dollar['columns']= ('Index', 'Content', "Source")
        self.tab_dollar.column("#0", width=0,  stretch=NO)
        self.tab_dollar.column("Index",anchor=CENTER, width=45)
        self.tab_dollar.column("Content",anchor=CENTER, width=200)
        self.tab_dollar.column("Source",anchor=CENTER, width=90)

        self.tab_dollar.heading("#0",text="",anchor=CENTER)
        self.tab_dollar.heading("Index",text="Index",anchor=CENTER)
        self.tab_dollar.heading("Content",text="Content",anchor=CENTER)
        self.tab_dollar.heading("Source",text="Source",anchor=CENTER)

        # Label just to separate the tables
        tkinter.Label(self.frame_memory, text="", font = ('Arial', 6)).pack()

        # Defines the properties of the table with the user variable memory map
        tkinter.Label(self.frame_memory, width="48", bg="gray70", font = self.font1, text="User Variables (Memory Map)", pady=1).pack()
        self.tab_vars = ttk.Treeview(self.frame_memory, style="mystyle.Treeview", height=13)
        self.tab_vars.pack()

        self.tab_vars['columns']= ('Var', 'Value')
        self.tab_vars.column("#0", width=0,  stretch=NO)
        self.tab_vars.column("Var", anchor=CENTER, width=100)
        self.tab_vars.column("Value", anchor=CENTER, width=234)

        self.tab_vars.heading("#0",text="",anchor=CENTER)
        self.tab_vars.heading("Var", text="Var",anchor=CENTER)
        self.tab_vars.heading("Value",text="Value",anchor=CENTER)

        
        # # Draw the eva and the lamp off
        # self.canvas.create_image(160, 262, image = self.eva_image)
        # self.canvas.create_oval(300, 205, 377, 285, fill = "#000000", outline = "#000000" ) # cor preta indica light off
        # self.canvas.create_image(340, 285, image = self.bulb_image)


        # Creation of user interface buttons
        self.bt_padx = 8 # Adjust spacing between buttons
        self.bt_power = Button (self.frame_botoes, text = "Power On", font = self.font1)
        self.bt_power.pack(side=tkinter.LEFT, padx=self.bt_padx)
        self.bt_import = Button (self.frame_botoes, text = "Import Script File...", font = self.font1, state = DISABLED)
        self.bt_import.pack(side=tkinter.LEFT, padx=self.bt_padx)
        self.bt_reload = Button (self.frame_botoes, text = "Reload", image = self.im_bt_reload, font = self.font1, state = DISABLED, compound = LEFT)
        self.bt_reload.pack(side=tkinter.LEFT, padx=self.bt_padx)

        self.lf = LabelFrame(self.frame_botoes, text = 'Running Mode', font = self.font1)
        self.lf.pack(side=tkinter.LEFT, padx=self.bt_padx)

        self.bt_run_sim = Button (self.lf, text = "Simulator", image = self.im_bt_play, font = self.font1, state = DISABLED, compound = LEFT)
        self.bt_run_sim.pack(side=tkinter.LEFT, padx=self.bt_padx, pady=2)
        self.bt_run_robot = Button (self.lf, text = "EVA Robot", image = self.im_bt_play_robot, font = self.font1, state = DISABLED, compound = LEFT)
        self.bt_run_robot.pack(side=tkinter.LEFT, padx=self.bt_padx, pady=2)

        self.bt_stop = Button (self.frame_botoes, text = "Stop", font = self.font1, image = self.im_bt_stop, state = DISABLED, compound = LEFT)
        self.bt_stop.pack(side=tkinter.LEFT, padx=self.bt_padx)
        self.bt_clear = Button (self.frame_botoes, text = "Clear Terminal", font = self.font1, state = NORMAL, compound = LEFT)
        self.bt_clear.pack(side=tkinter.LEFT, padx=self.bt_padx)


        # Add a scrollbar(horizontal)
        self.v=Scrollbar(self.frame_terminal, orient='vertical')
        self.v.pack(side=RIGHT, fill='y')

        # Terminal text configuration
        self.terminal = Text (self.frame_terminal, fg = "cyan", bg = "black", height = "32", width = "125", yscrollcommand=self.v.set)
        self.terminal.configure(font = ("Arial", 10))
        self.terminal.tag_configure("error", foreground="red")
        self.terminal.tag_configure("motion", foreground="orange")
        self.terminal.tag_configure("tip", foreground="yellow")
        self.v.config(command=self.terminal.yview)
        # Clean, draw and place terminal in its frame
        self.terminal.delete('1.0', END)
        # Creating terminal text
        self.terminal.insert(INSERT, "=============================================================================================================================\n")
        self.terminal.insert(INSERT, "                                                                                      Embodied Voice Assistant Simulator - Script Player for EvaML\n")
        self.terminal.insert(INSERT, "                                                                                                   Version 2.0 - UFF / MidiaCom / CICESE - [2024]\n")
        self.terminal.insert(INSERT, "=============================================================================================================================")

        self.terminal.pack()

        # # Draw the eva and the lamp off
        # # Defining the image files
        # self.eva_image = PhotoImage(file = "images/eva.png") 
        # self.bulb_image = PhotoImage(file = "images/bulb.png")
        # self.canvas.create_image(160, 262, image = self.eva_image)
        # self.canvas.create_oval(300, 205, 377, 285, fill = "#000000", outline = "#000000" ) # cor preta indica light off
        # self.canvas.create_image(340, 285, image = self.bulb_image)
