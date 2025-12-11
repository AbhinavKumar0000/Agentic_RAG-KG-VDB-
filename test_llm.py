import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ GOOGLE_API_KEY not found in environment variables.")
    exit(1)
else:
    print("✅ GOOGLE_API_KEY found.")

print("Testing Gemini LLM connection...")
try:
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
    response = llm.invoke("Hello, are you working?")
    print(f"✅ LLM Response: {response.content}")
except Exception as e:
    print(f"❌ LLM Connection failed: {e}")
