from groq import Groq                  # import Groq library
from dotenv import load_dotenv         # read .env file
import os                              # access environment variables

load_dotenv(r"C:\Dev\.env")                          # load keys from .env

api_key = os.getenv("GROQ_API_KEY")   # get Groq key from .env

client = Groq(api_key=api_key)        # create client with your key

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",           # free Llama 3 model
    messages=[
        {
            "role": "user",
            "content": "Say hello and tell me one interesting fact about AI in one sentence"
        }
    ]
)

print(response.choices[0].message.content)   # print the AI response