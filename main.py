import os
import re

import google.generativeai as genai
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google.generativeai.types.generation_types import json
from markdown import markdown

from modules import jokes, weather

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
    try:
        ext_json = ext_json.replace("'", '"')
        json_res = json.loads(ext_json)
        api_res = handle_api(json_res)
        if isinstance(api_res, dict):
            return api_res["content"]
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
            return markdown_to_text(response.text)
    except json.JSONDecodeError:
        print("Invalid JSON")


def handle_api(json_res):
    module = json_res.get("module")
    params = json_res.get("parameters")
    if module == "Weather":
        return weather.handle_res(params)
    elif module == "Jokes":
        return jokes.handle_res(params)

    else:
        return None


def markdown_to_text(markdown_string):
    """Converts a markdown string to plaintext"""

    # md -> html -> text since BeautifulSoup can extract text cleanly
    html = markdown(markdown_string)

    # remove code snippets
    html = re.sub(r"<pre>(.*?)</pre>", " ", html)
    html = re.sub(r"<code>(.*?)</code >", " ", html)

    # extract text
    soup = BeautifulSoup(html, "html.parser")
    text = "".join(soup.findAll(string=True))

    return text


def main():
    print(header)
    print("Welcome To ZBot")
    model = setup_ai()
    while True:
        user_input = input("Give Query: ")
        if user_input:
            ext_json = response(user_input, model)
            if ext_json:
                res = handle_response(ext_json, model)
                print()
                print(res)
                print()
            else:
                print("Unknown Error")
                exit(1)


main()
