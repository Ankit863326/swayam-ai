import speech_recognition as sr

WAKE_WORD = "swayam"

def wait_for_wake_word():
    r = sr.Recognizer()
    print("😴 Sleeping... say 'Swayam' to wake me up")
    while True:
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.3)
            try:
                audio = r.listen(source, timeout=4, phrase_time_limit=3)
                text = r.recognize_google(audio).lower()
                print(f"[WakeWord] Heard: {text}")
                if WAKE_WORD in text:
                    print("✅ Swayam activated!")
                    return  # returns cleanly — MainExecution takes over
            except:
                pass