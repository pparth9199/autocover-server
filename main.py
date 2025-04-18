from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging
import os
import requests
import json

logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.DEBUG)

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    logger.debug("Hi")
    return {"message": "Hello from Python!"}

@app.post("/generate")
async def generate(request: Request):
    body = await request.json()
    resume = body.get("resume")
    jobPost = body.get("jobPost")
    tone = body.get("tone")

    prompt = f"""
You are a helpful assistant that generates cover letters.

Based on the resume and job description below, do the following:
1. Write a personalized cover letter in a {tone} tone.
2. Extract the company name from the job description.
3. Return only a valid JSON object with two keys:
   - "letter": the cover letter
   - "company": the company name

Do NOT include markdown, explanations, or code blocks — return only the raw JSON.

Resume:
{resume}

Job Description:
{jobPost}

Start the letter with “Dear Hiring Manager,” unless a name is specified. Be concise but strictly 250 to 300 words.
"""


    try:
        gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        response = requests.post(
            f"{gemini_url}?key={os.getenv('GEMINI_API_KEY')}",
            headers={"Content-Type": "application/json"},
            json={ "contents": [{ "parts": [{ "text": prompt }] }] },
        )

        data = response.json()
        result = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        logger.debug(data)
        try:
            result = result.strip().strip("```json").strip("```").strip()
            parsed = json.loads(result)
            letter = parsed.get("letter", "")
            company = parsed.get("company", "company")
        except json.JSONDecodeError as err:
            logger.error(f"JSON parsing failed: {err}")
            letter = result  # fallback to raw letter
            company = "company"

        return { "letter": letter, "company": company }

    except Exception as e:
        print("Gemini error:", e)
        return { "letter": "Error generating letter", "company": "company" }
