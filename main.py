import os

import google.generativeai as genai
import pyttsx3
import requests
import speech_recognition as sr
from dotenv import load_dotenv
from google.generativeai.types.generation_types import json

from modules import weather

load_dotenv()

RED = "\033[0;31m"
NC = "\033[0m"

header = """
███████╗██████╗  ██████╗ ████████╗
╚══███╔╝██╔══██╗██╔═══██╗╚══██╔══╝
  ███╔╝ ██████╔╝██║   ██║   ██║   
 ███╔╝  ██╔══██╗██║   ██║   ██║   
███████╗██████╔╝╚██████╔╝   ██║   
╚══════╝╚═════╝  ╚═════╝    ╚═╝   
"""


class Mode:
    _mode = None

    def get_mode(self):
        return self._mode

    def set_mode(self, mode):
        self._mode = mode


mode = Mode()
engine = pyttsx3.init()


def get_mode():
    while True:
        print("Modes:\n1. Speech\n2. Text")
        try:
            inp = int(input("Enter Mode: "))
        except Exception:
            continue
        if inp == 1:
            mode.set_mode("speech")
            break
        elif inp == 2:
            mode.set_mode("text")
            break
        else:
            print(f"{RED}Error: Enter Correct Value{NC}\n")
    return mode


def output(text):
    if mode.get_mode() == "speech":
        engine.say(text)
        engine.runAndWait()
    else:
        print(text)


def inp(text):
    if mode.get_mode() == "speech":
        output(text)
        inp = recognize_speech()
        return inp
    else:
        return input(text)


def recognize_speech():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    output("Please Say Something..")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5)
        except sr.WaitTimeoutError:
            output("Timeout. No Speech Detected")
            return " "

    try:
        output("Recognizing speech...")
        text = recognizer.recognize_google(audio)
        output(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Sorry, I did not understand that.")
        return ""
    except sr.RequestError:
        print("Sorry, the speech recognition service is unavailable.")
        return ""


def setup_ai():
    genai.configure(api_key=os.getenv("AI_API"))
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }
    safety_settings = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
        },
    ]
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-latest",
        safety_settings=safety_settings,
        generation_config=generation_config,
    )
    return model


def response(user_input, model):
    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [user_input],
            }
        ]
    )
    inst_file = open("./instruction.txt", "r")
    inst = inst_file.read()
    res = chat_session.send_message(inst + user_input).text
    start_index = res.find("{")
    end_index = res.rfind("}")
    extracted_json_string = (
        res[start_index : end_index + 1]
        if start_index != -1 and end_index != -1
        else None
    )
    return extracted_json_string


def handle_response(ext_json, model):
    ext_json_data = json.loads(ext_json)
    try:
        ext_json = ext_json.replace("'", '"')
        json_res = json.loads(ext_json)
        api_res = handle_api(json_res, model)
        if isinstance(api_res, dict):
            if "weather_info" in api_res:
                return api_res["weather_info"]
        else:
            user_input = json_res.get("query")
            chat_session = model.start_chat(
                history=[
                    {
                        "role": "user",
                        "parts": [user_input],
                    }
                ]
            )

            # Send a message to the chat session and get the response
            response = chat_session.send_message(user_input)
            return response.text
    except json.JSONDecodeError:
        print("Invalid JSON")


def handle_api(json_res, model):
    module = json_res.get("module")
    params = json_res.get("parameters")
    modules = os.listdir("./modules/")
    if module == "Weather":
        return weather.handle_res(params)


def main():
    print(header)
    print("Welcome To ZBot")
    print("Please Select The Mode")
    get_mode()
    output("Welcome To ZBot")
    model = setup_ai()
    while True:
        user_input = inp("Give Query: ")
        if user_input:
            ext_json = response(user_input, model)
            if ext_json:
                res = handle_response(ext_json, model)
                output(res)
            else:
                print("Unknown Error")
                exit(1)


main()
