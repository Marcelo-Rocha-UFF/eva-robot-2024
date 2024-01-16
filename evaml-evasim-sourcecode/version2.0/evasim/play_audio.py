import platform

# Deixei de utilizar a biblioteca Playsound por dar muito problema!
# if platform.system() == "Linux":
#     from playsound import playsound as ps
#     print("Linux audio library loaded")
#     def playsound(audio_file, block = True):
#         ps(audio_file, block)

if platform.system() == "Linux":
    import pygame
    pygame.init()
    print("Linux (Pygame) audio library loaded")
    def playsound(audio_file, block = True):
        sound = pygame.mixer.Sound(audio_file)
        playing = sound.play()
        if block == True:
            while playing.get_busy():
                pygame.time.delay(100)
        else:
            pass


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