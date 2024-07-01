import requests


def handle_res(params):
    url = "https://v2.jokeapi.dev/joke/Any?safe-mode"
    response = requests.get(url).json()
    if response.get("error"):
        return {"error": "Error fetching joke."}

    if response["type"] == "single":
        joke = response["joke"]
    else:
        joke = f"{response['setup']} ... {response['delivery']}"

    return {"content": joke}
