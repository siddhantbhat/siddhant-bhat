import tkinter as tk
import tkinter.scrolledtext as scrolledtext
import google.generativeai as genai
import pyttsx3
import speech_recognition as sr
from googletrans import Translator
import threading
import requests
import feedparser
import re
from gtts import gTTS
from playsound import playsound
import os
import uuid


# ✅ Language selection
selected_language = 'zh-cn'

# ✅ Gemini API setup
genai.configure(api_key="AIzaSyByV11oqrFPjOoOBQGZicSrhJTDfLf0q0s")  # Replace with your actual key
model = genai.GenerativeModel("gemini-2.5-flash")

# ✅ Tools
engine = pyttsx3.init()
recognizer = sr.Recognizer()
translator = Translator()

# ✅ Clean text
def clean_text_for_speech(text):
    text = re.sub(r"http\S+|www\S+|https\S+", '', text)
    text = text.replace(":", "").replace("&", " and ").replace("–", "-").replace("/", " or ").replace("-", " ")
    text = text.replace("•", "")
    text = re.sub(r'[^\w\s.,!?]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# ✅ Speak function
def speak(text):
    output_box.insert(tk.END, f"\n🧠 Jarvis: {text}\n")
    output_box.see(tk.END)
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        output_box.insert(tk.END, f"\n[Speak Error]: {e}")

# ✅ Listen from microphone
def listen():
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        speak("listning...")
        audio = recognizer.listen(source)
        try:
            user_text = recognizer.recognize_google(audio)
            user_input.delete(0, tk.END)
            user_input.insert(0, user_text)
            handle_user_input(user_text)
        except:
            speak("Sorry, I didn’t catch that.")

# ✅ Translate
def translate_text(text, dest=selected_language):
    try:
        return translator.translate(text, dest=dest).text
    except:
        return text

# ✅ Handle user input (cleaned)
def handle_user_input(prompt):
    def task():
        output_box.insert(tk.END, f"\n🗣️ You: {prompt}")
        output_box.see(tk.END)

        translated_input = translate_text(prompt, 'hi' if selected_language == 'hi' else 'en')

        try:
            stream = model.generate_content(translated_input, stream=True)
            for chunk in stream:
                if hasattr(chunk, 'text') and chunk.text:
                    speak(chunk.text)  # Speak instantly per chunk
        except Exception as e:
            speak("Gemini API error.")
            output_box.insert(tk.END, f"\n[Gemini Error]: {e}")

    threading.Thread(target=task).start()


# ✅ TOI RSS
def get_news_from_toi():
    feed = feedparser.parse("https://timesofindia.indiatimes.com/rssfeedstopstories.cms")
    news = [f"{i+1}. {entry.title}" for i, entry in enumerate(feed.entries[:5])]
    return "\n".join(news)



def show_toi_news():
    speak("Top stories from Times of India:")
    speak(get_news_from_toi())

# ========== GUI ========== #
root = tk.Tk()
root.title("🧠 Jarvis - AI Assistant")
root.geometry("800x620")
root.configure(bg="#1f1f1f")
root.resizable(False, False)

FONT_TITLE = ("Segoe UI", 16, "bold")
FONT_NORMAL = ("Segoe UI", 12)

header = tk.Label(root, text="🤖 Jarvis - Your Smart Assistant", font=FONT_TITLE, bg="#1f1f1f", fg="#00ffd0")
header.pack(pady=10)

output_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, bg="#262626", fg="#ffffff", font=FONT_NORMAL,
                                       padx=10, pady=10, relief=tk.FLAT, height=20, borderwidth=0)
output_box.pack(padx=20, pady=(0, 10), fill=tk.BOTH, expand=True)

user_input = tk.Entry(root, font=FONT_NORMAL, bg="#333", fg="white", relief=tk.FLAT, insertbackground="white")
user_input.pack(padx=20, pady=10, ipady=8, fill=tk.X)

btn_frame = tk.Frame(root, bg="#1f1f1f")
btn_frame.pack(pady=5)

def threaded(fn):
    def wrapper(): threading.Thread(target=fn).start()
    return wrapper

def on_enter(event=None):
    text = user_input.get().strip()
    user_input.delete(0, tk.END)
    if text:
        threading.Thread(target=handle_user_input, args=(text,)).start()

@threaded
def on_listen(): listen()
@threaded
def on_toi(): show_toi_news()

def make_button(text, command, bg="#00cc88"):
    return tk.Button(btn_frame, text=text, command=command, font=FONT_NORMAL, bg=bg, fg="white",
                     relief=tk.FLAT, activebackground="#00b77a", padx=10, pady=5, width=14, bd=0)

# ✅ Stop speaking function
def stop_speaking():
    try:
        engine.stop()
        output_box.insert(tk.END, "\n🛑 Speech stopped.\n")
        output_box.see(tk.END)
    except Exception as e:
        output_box.insert(tk.END, f"\n[Stop Error]: {e}")
# Buttons
make_button("📝 Ask", on_enter).pack(side=tk.LEFT, padx=10)
make_button("🎤 Voice", on_listen, "#444").pack(side=tk.LEFT, padx=10)
make_button("🗞️ TOI RSS", on_toi, "#007acc").pack(side=tk.LEFT, padx=10)
make_button("🛑 Stop", stop_speaking, "#cc0000").pack(side=tk.LEFT, padx=10)


# Language Selector
lang_frame = tk.Frame(root, bg="#1f1f1f")
lang_frame.pack()

lang_label = tk.Label(lang_frame, text="🌐 Language:", font=FONT_NORMAL, bg="#1f1f1f", fg="white")
lang_label.pack(side=tk.LEFT, padx=5)

lang_var = tk.StringVar(root)
lang_options = {
    "English": "en",
    "Hindi": "hi",
    "Spanish": "es",
    "French": "fr",
    "Japanese": "ja",
    "Russian": "ru",
    "Chinese": "zh-cn"
}
lang_var.set("Chinese")

lang_menu = tk.OptionMenu(lang_frame, lang_var, *lang_options.keys())
lang_menu.config(bg="#222", fg="white", font=FONT_NORMAL, highlightthickness=0, relief=tk.FLAT)
lang_menu.pack(side=tk.LEFT)

def update_lang(*args):
    global selected_language
    selected_language = lang_options[lang_var.get()]

lang_var.trace("w", update_lang)
user_input.bind("<Return>", on_enter)
# Startup greeting
speak(" hellow this is jarvis. what can i do for you today ?")
root.mainloop()
