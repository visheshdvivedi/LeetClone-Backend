import requests

url = "https://judge0-ce.p.rapidapi.com/"
response = requests.post(
    url + "/submissions?wait=true",
    data={
        "source_code": "print('hello world')",
        "language_id": 92,
        "stdin": ""
    },
    headers={
        "x-rapidapi-host": "judge0-ce.p.rapidapi.com",
        "x-rapidapi-key": "cc002ff584mshbd0a3c2b1df0f2ap1eb393jsn4bf263f9a775"
    }
)
print(response)