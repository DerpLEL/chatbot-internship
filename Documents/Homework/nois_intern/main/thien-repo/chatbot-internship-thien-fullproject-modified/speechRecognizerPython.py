# From https://github.com/CODE-LY-CODE-HANH/Share_source_code/blob/master/python/tro_ly_ao/sua_loi_nhan_dang_giong_nnoi.py
import playsound
import speech_recognition as sr
import os
from gtts import gTTS
import pyttsx3

# chuyển văn bản thành âm thanh
def speak(text):
    print("Bot:  ", text)

    engine = pyttsx3.init()
    voices = engine.getProperty('voices')

    rate = engine.getProperty('rate')
    volume = engine.getProperty('volume')
    engine.setProperty('volume', volume - 0.0)  # tu 0.0 -> 1.0
    engine.setProperty('rate', rate - 50)

    #english version
    # engine.setProperty('voice', voices[1].id)
    # engine.say(text)
    # engine.runAndWait()

    # Vietnamese Version - broken
    # change_voice(engine, "vi", "VoiceGenderMale")
    # engine.say(text)
    # engine.runAndWait()





    # raw os stuff 
    tts = gTTS(text=text, lang="vi", slow=False)
    tts.save("C:\Users\QuanBH\Documents\Homework\nois_intern\main\thien-repo\chatbot-internship-thien-fullproject-modified\STTDump\sound.mp3")
    playsound.playsound("C:\\Users\\QuanBH\\Documents\\Homework\\nois_intern\\main\\thien-repo\\chatbot-internship-thien-fullproject-modified\\STTDump\\sound.mp3", True)
    os.remove("C:\Users\QuanBH\Documents\Homework\nois_intern\main\thien-repo\chatbot-internship-thien-fullproject-modified\STTDump\sound.mp3")


# chuyển giọng nói thành văn bản
def get_audio():
    ear_robot = sr.Recognizer()
    with sr.Microphone() as source:
        print("Bot:  Listening ! -- __ -- !")

        # python 3.7
        # ear_robot.language = "vi-VN"

        # ear_robot.pause_threshold = 4
        # audio = ear_robot.record(source , duration= 4)
        audio = ear_robot.listen(source)

        try:
            print(("Bot :  ...  "))

            # python 3.10
            text = ear_robot.recognize_google(audio, language="vi-VN")  #set language as vnese

            # python 3.7
            # text = ear_robot.recognize(audio)

            print("You:  ", text)
            return text
        except Exception as ex:
            speak("! ... ! Error ! ... !")
            print(ex)
            return 0

def change_voice(engine, language, gender='VoiceGenderFemale'):
        for voice in engine.getProperty('voices'):
            if language in voice.languages and gender == voice.gender:
                engine.setProperty('voice', voice.id)
                return True
        raise RuntimeError("Language '{}' for gender '{}' not found".format(language, gender))

#get_audio()  
#speak("xin chào bạn") --still error--