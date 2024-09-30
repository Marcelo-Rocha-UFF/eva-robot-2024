import platform
import subprocess
 
import config # Module with the constants and parameters used in other modules.

# I stopped using the Playsound library because it was too much trouble!

# Playsound for Linux
if platform.system() == "Linux":
    # As future work, it would be interesting to use the SOX library as well as in the Audio Module of the physical robot.
    def playsound(audio_file, block = True):
        if block == True:
            play = subprocess.Popen(['play', audio_file], stdout=subprocess.PIPE)
            play.communicate()[0]
        else:
            play = subprocess.Popen(['play', audio_file], stdout=subprocess.PIPE)



# Playsound for Windows (It is not working because we are not still using Windows)
elif platform.system() == "Windows":
    print("Windows audio library loaded")
    # playing audio
    import sounddevice as sd
    import soundfile as sf
    # my playsound function
    def playsound(file, block = True):
        # Extract data and sampling rate from file
        data, fs = sf.read(file, dtype='float32')  
        sd.play(data, fs)
        if block == True: status = sd.wait()  # Wait until file is done playing