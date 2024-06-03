import json
import xml.etree.ElementTree as ET
import re
from pprint import pprint

script = ""
comandos_json= ""
links = ""
links_json = ""
evaml = ""

def converte(json_file_name, tkinter):
  global script, comandos_json, links, links_json, evaml
  # Reading from json file
  with open(json_file_name, 'r') as openfile:
    json_object = json.load(openfile) # Is a dict.
      
  comandos_json = json_object["data"]["node"] # List of nodes. Each node (a command) is a dict. with their corresponding element key/value pairs.
  links_json = json_object["data"]["link"] # List of links. Each link is a dict. with the keys "from" and "to".

  # Creates the root element <evaml> and its subelements.
  evaml_atributos = {"name":json_object["nombre"]}
  evaml = ET.Element("evaml", evaml_atributos )
  #
  settings = ET.SubElement(evaml, "settings")
  # Add the settings sub-elements with their attributes.
  for comando in comandos_json:
    voice_found = False # 
    if comando["type"] == "voice": # Search voice command and its attributes.
      voice_atributos = {"tone":comando["voice"], "key":str(comando["key"])}
      comandos_json.remove(comando) # Exclude voice so that it is not processed in the next step.
      voice_found = True
      voice = ET.SubElement(settings, "voice", voice_atributos)
      break
  
    if not voice_found: # Voice must exist in JSON and must be the first element of the VPL.
      print("Oops! The Voice element is missing...") # it's required that the voice be the first element of VPL.
      warning_message = "Sorry! I didn't find the Voice element.\n\nPlease the Voice element must be the first element of the script!\n\nThe EvaSIM will be closed!"
      tkinter.messagebox.showerror(title="Error!", message=warning_message)
      exit(1)

  # These elements have their default values ​​as they have not yet been implemented in the robot.
  lightEffects_atributos = {"mode":"on"}
  lightEffects = ET.SubElement(settings, "lightEffects", lightEffects_atributos)

  audioEffects_atributos = {"mode":"on",  "vol":"100%"}
  audioEffects = ET.SubElement(settings, "audioEffects", audioEffects_atributos)

  # Create the other sections of the EvaML document.
  script = ET.SubElement(evaml, "script")
  links = ET.SubElement(evaml, "links")

  # Call processing functions
  processa_nodes(script, comandos_json, tkinter) # Convert json nodes to XML nodes.
  processa_links(links, links_json) # Convert json links to XML links.


# Processing commands in the json file #######################################################################################
def processa_nodes(script, comandos_json, tkinter):
  for comando in comandos_json:

    # <light>
    if comando["type"] == "light":
      light_atributos = {"key" : str(comando["key"]), "state" : comando["state"].upper(), "color" : comando["lcolor"].upper()}
      ET.SubElement(script, "light", light_atributos)
  

    # <motion>
    elif comando["type"] == "mov":
      # Mapping the types of head movements.
      if   (comando["mov"] == "n"): motion_type = "YES"
      elif (comando["mov"] == "s"): motion_type = "NO"
      elif (comando["mov"] == "c"): motion_type = "CENTER"
      elif (comando["mov"] == "l"): motion_type = "LEFT"
      elif (comando["mov"] == "r"): motion_type = "RIGHT"
      elif (comando["mov"] == "u"): motion_type = "UP"
      elif (comando["mov"] == "d"): motion_type = "DOWN"
      elif (comando["mov"] == "a"): motion_type = "ANGRY"
      elif (comando["mov"] == "U"): motion_type = "2UP"
      elif (comando["mov"] == "D"): motion_type = "2DOWN"
      elif (comando["mov"] == "R"): motion_type = "2RIGHT"
      else: motion_type = "2LEFT"


      motion_atributo = {"key" : str(comando["key"]), "type" : motion_type}
      ET.SubElement(script, "motion", motion_atributo)


    # <audio>
    elif comando["type"] == "sound":
      audio_atributos = {"key" : str(comando["key"]), "source" : comando["src"], "block" : str(comando["wait"]).upper()}
      ET.SubElement(script, "audio", audio_atributos)


    # <evaEmotion>
    elif comando["type"] == "emotion":
      # Mapping expression names (4 expressions).
      if (comando["emotion"] == "anger"): eva_emotion = "ANGRY"
      elif (comando["emotion"] == "joy"): eva_emotion = "HAPPY"
      elif (comando["emotion"] == "ini"): eva_emotion = "NEUTRAL"
      else: eva_emotion = "SAD"

      eva_emotion_atributos = {"key" : str(comando["key"]), "emotion" :eva_emotion}
      ET.SubElement(script, "evaEmotion", eva_emotion_atributos)

    # <leds>
    elif comando["type"] == "led":
      # Mapping led animations names.
      if (comando["anim"] == "anger"): animatiom = "ANGRY"
      elif (comando["anim"] == "joy"): animatiom = "HAPPY"
      elif (comando["anim"] == "escuchaT"): animatiom = "LISTEN"
      elif (comando["anim"] == "sad"): animatiom = "SAD"
      elif (comando["anim"] == "hablaT_v2"): animatiom = "SPEAK"
      elif (comando["anim"] == "stop"): animatiom = "STOP"
      elif (comando["anim"] == "surprise"): animatiom = "SURPRISE"

      led_atributos = {"key" : str(comando["key"]), "animation" :animatiom}
      ET.SubElement(script, "led", led_atributos)


    # <wait>
    elif comando["type"] == "wait":
      wait_atributos = {"key" : str(comando["key"]), "duration" : str(comando["time"])}
      ET.SubElement(script, "wait", wait_atributos)

    
    # <listen>
    elif comando["type"] == "listen":
      listen_atributos = {"key" : str(comando["key"])}
      ET.SubElement(script, "listen", listen_atributos)

    
    # <random>
    elif comando["type"] == "random":
      random_atributos = {"key" : str(comando["key"]), "min" : str(comando["min"]), "max" : str(comando["max"])}
      ET.SubElement(script, "random", random_atributos)


    # <talk>
    elif comando["type"] == "speak":
      speak_atributos = {"key" : str(comando["key"])}
      talk = ET.SubElement(script, "talk", speak_atributos)
      talk.text = comando["text"]


    # <userEmotion>
    elif comando["type"] == "user_emotion":
      user_emotion_atributos = {"key" : str(comando["key"])}
      ET.SubElement(script, "userEmotion", user_emotion_atributos)


    # <counter>
    elif comando["type"] == "counter":
      # Mapping operations types.
      if (comando["ops"] == "assign"): op = "="
      elif (comando["ops"] == "rest"): op = "%"
      elif (comando["ops"] == "mul"): op = "*"
      elif (comando["ops"] == "sum"): op = "+"
      elif (comando["ops"] == "div"): op = "/"

      counter_atributos = {"key" : str(comando["key"]), "var" : comando["count"], "op" : op , "value" : str(comando["value"])}
      ET.SubElement(script, "counter", counter_atributos)



    # <if>
    elif comando["type"] == "if":
      exp_logica = comando["text"] # String with the logical expression of the condition.
      tag = "case" # we have this variable here, so that, if necessary, we create the default element.
      # Mapping "op" types.
      if (comando["opt"]) == 4: # Exact is always compared with $.
        var = "$"
        op = "exact" #
        value = exp_logica # There is no exp in this one. logic in the content, just a string.
        if (value == ""): # If op is exact and value "", the "condition" is defined here as <default>. This creates a restriction on building scripts using the VPL.
          tag = "default"
      elif (comando["opt"]) == 2: # Contain with $.
        op = "contain"
        value = comando["text"]
        var = "$"
      elif (comando["opt"]) == 5: # Mathematical comparison.
        if ("==" in exp_logica): # Make the map. and removes it from the expression, leaving only the operands separated by empty spaces.
          op = "eq"
          exp_logica = exp_logica.replace("==", "  ")
        elif (">=" in exp_logica):
          op = "gte"
          exp_logica = exp_logica.replace(">=", "  ")
        elif ("<=" in exp_logica):
          op = "lte"
          exp_logica = exp_logica.replace("<=", "  ")
        elif ("!=" in exp_logica):
          op = "ne"
          exp_logica = exp_logica.replace("!=", "  ")
        elif (">" in exp_logica):
          op = "gt"
          exp_logica = exp_logica.replace(">", "  ")
        elif ("<" in exp_logica):
          op = "lt"
          exp_logica = exp_logica.replace("<", "  ")

        # With opt equal to 5, command["text"] has something like this #x == 2 or $ == 2 (mathematical comparison).
        if ("$" in exp_logica):
          var = "$" # Dollar is the first operand.
        else:
          # The exp. logic has one or two operands of type #n.
          # The regular expression returns a list of #x, #y, etc.
          var = (re.findall(r'\#[a-zA-Z]+[0-9]*', exp_logica)) 
        
        if (type(var) == str): # Type str indicates that var is $, otherwise var is a list resulting from the regular expression.
          # Getting the "value". try to read a number.
          value = (re.findall(r'[0-9]+', exp_logica))
          if (len(value) == 0): # Did not find a number in the expression.
            # If it is not a capture the var #n on the right.
            value = re.findall(r'\#[a-zA-Z]+[0-9]*', exp_logica)[0] # Captures the variable of type #n and puts it in value. in this case you need to go with #.
          else: # Found the number. Remembering that exp. regular returns a list.
            value = value[0] # So value[0] is the string returned by exp. regular.
        else: # In this case $ is not in exp. and var is a list. we need to check if it has one or two elements.
          print(len(var))
          if (len(var) == 1): # The left operand is a var #n.
            var = var[0][1:] # We get the variable without the #.
            value = (re.findall(r'[0-9]+', exp_logica))[0] # In this case value can only be a number.
          else: # Var has two elements, that is, the two operands are of type #n #m.
            var = var[0][1:] # We get the variable without the #.
            value = var[1] # A var in value must go with the character #.
      if_atributos = {"key" : str(comando["key"]), "op" : op, "value" : value, "var" : var}
      ET.SubElement(script, tag , if_atributos)

    # All supported commands have been tested.
    else:
      warning_message = """Sorry, an unsupported VPL element was found. Please, check your JSON script!

=========================
  Supported VPL Elements List
=========================
        
* Voice
* Random
* Wait
* Talk
* Light
* Motion
* evaEmotion
* Audio
* Led
* Counter
* Condition
* Listen
* userEmotion

The EvaSIM will be closed..."""

      tkinter.messagebox.showerror(title="Error!", message=warning_message)
      exit(1)


# Processing links in the json file #######################################################################################################
def processa_links(links, links_json):
  for link in links_json:
    link_atributos = {"from" : str(link["from"]), "to" : str(link["to"])}
    ET.SubElement(links, "link", link_atributos)

  # Generate the XML file on disk.
  xml_processed = ET.tostring(evaml, encoding="unicode")
  print("Processando XML..............")
  with open("_json_to_evaml_converted.xml", "w") as text_file: # Writes the processed xml (temporary) to a file to be imported by the parser.
      text_file.write(xml_processed)


