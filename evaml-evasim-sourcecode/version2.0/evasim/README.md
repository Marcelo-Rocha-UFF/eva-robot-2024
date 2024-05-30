# **EvaSIM 2.0 - Simulator Software for the EVA robot**
 
The EvaSIM simulator was developed with the aim of assisting in the development of scripts for the EVA robot. One of its applications is to serve as a testing and debugging platform for scripts developed for the physical robot, representing, in a simplified way, the physical elements that make up the robot, such as: the Matrix Voice board, the display with the robot's expressions, the smart bulb and etc. EvaSIM plays an important role as an aid tool in the development of scripts for EVA, as it is capable of displaying information about what is being executed in your terminal emulator, in addition to presenting (in two tables) the variables used in the scripts next to their respective values.

The simulator can run both the codes generated by the EvaML language parser and the JSON files that represent the graphic scripts created with the EVA Visual Programming Language, VPL. After loading a script into the simulator, it is capable of interpreting this code and each element executed has its representation in the simulator interface, such as: the robot's facial expressions, the smart lamp, the LEDs on the robot's chest or some text that was spoken to him.


This work proposes a new version for the **EvaSIM simulator**. In this new version, the simulator now has two execution modes: **Simulator Mode** and **EVA Robot Mode**. Furthermore, a **Wizard of OZ (WoZ)** control panel was added to its graphical user interface (GUI), which allows the robot to be operated remotely through buttons that control its functionalities. The next figure presents the new EvaSIM interface with all its new elements and resources indicated by items 1 to 8.

![alt text](img-evasim-gui.png)

As follow, a brief description of each of these items will be made.

**Terminal Emulator** - In item (1), the EvaSIM terminal emulator can be seen. In this new version, in addition to having its data presentation area expanded, by increasing its number of lines and columns, a scroll bar was added to the right side of the terminal, allowing greater control over the display of text that exceeds its limit on the number of visible lines.

**Execution Modes** - As previously stated, the simulator can run in *Simulator* and *EVA Robot* modes (item (2)). In the first mode, the simulator works as in its previous version, simulating the behavior of the robot's physical components (eyes, LEDs, head movement, etc.) simulating voice capture with a window with a text box and using a keyboard as an input interface. To simulate facial expression recognition, EvaSIM uses a window with expression options represented through *Emojis*.

In *EVA Robot mode*, the simulator works, in part, as a script player for the physical robot. The script elements, which control the robot's elements, start to act directly on the robot's physical components, that is, a command to move the robot's head, makes its head actually move, as well as the other elements: the robot's eyes, its RGB LEDs and its smart bulb. Furthermore, the robot's speech is now controlled by the Text-To-Speech module (eva-tts-module) of the physical robot. This module is responsible for requesting the IBM-Watson cloud service, transforming text into speech (in audio). It is important to highlight that the simulator, even in EVA Robot mode, continues to display, in its terminal, the elements that are being executed and the variables continue to be displayed in the memory tables in the graphical user interface. In this mode, unlike *Simulator mode*, voice capture is done by the Speech-To-Text module (eva-stt-module) of the physical robot. This module is responsible for requesting STT services from the Google Cloud API. After transforming the speech (audio file) into text (a string), the eva-stt module sends the string returned by the Google API to the simulator and this information is displayed in the memory table that presents the values ​​of the special variable “$” or the variable specified in the new var attribute of the **\<listen>** command. This behavior is repeated for all EVA features that return values ​​obtained from interaction with users, such as: **\<userEmotion>**, **\<userID>** and **\<qrReader>**.

**Display Control** - Item (3) in the figure controls the robot's facial expressions and allows the user to change the EVA's facial expression to one of its eight available expressions.

**RGB LED Animation** - The LEDs on the EVA's chest play an important role as a non-verbal communication element for the robot. Item (4) presents buttons that can execute one of the 10 possible LED animations available for the EVA.

**Smart Bulb** - Item (5) allows the smart bulb to be turned on and off as well as having its color selected through the group of buttons available on the interface.

**Arm Movement** - In this new proposal for the EVA robot, the ability to move its arms has been added. Item (6) shows 14 buttons (seven for each arm) with the types of possible movements.

**Head Movement** - In item (7) you can see the buttons for controlling the movement of the robot's head.

**Text-To-Speech** - The last item, number 8, allows the user to listen to the audio generated by IBM Watson from the texts entered into the interface. Some voice and language options are available. You can use this feature to check how the robot speaks when using certain phonemes. The sentences generated through this tool are stored in the robot's audio folder (TTS) and, if they are spoken by the robot, in future interactions, they will be available offline.

As follow, we can see a general archtecture of EvaSIM 2.0.

![alt text](img-evasim-arch.png)

This new version of the **EvaSIM** simulator was proposed with the aim of integrating the entire software and hardware ecosystem that was developed with the new proposal for the software architecture of the EVA robot and its new functionalities. In addition to behaving like a simulator, which is its function, **EvaSIM** can now execute scripts acting directly on the physical robot's hardware. This work also proposes the addition of new elements (buttons) to the EvaSIM graphical interface, offering the user the ability to control various robot functionalities remotely (WoZ Condition).