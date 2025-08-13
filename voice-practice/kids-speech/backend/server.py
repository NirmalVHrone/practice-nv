import fastapi
#from fastapi.responses import FileResponse
from fastrtc import ReplyOnPause, AdditionalOutputs, Stream, AlgoOptions, SileroVadOptions
#from fastrtc.utils import audio_to_bytes
from fastrtc import get_stt_model, get_tts_model
from openai import OpenAI
import logging
import time
import re
from fastapi.middleware.cors import CORSMiddleware
#import numpy as np
#import io
import platform
import os
import socket

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import json
from env import LLM_API_KEY

stt_model = get_stt_model()
tts_model = get_tts_model()

logging.basicConfig(level=logging.INFO)

if platform.system() == 'Windows':
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'
    finally:
        s.close()

    os.environ['WEBRTC_IP'] = local_ip

sys_prompt = """
You are a friendly, enthusiastic, and patient AI teacher named StarGuide who loves talking to kids about space! You're having a wonderful conversation with Anika, a bright and curious girl studying in class 4, who is fascinated by the solar system.

CONVERSATION APPROACH:
- Make smaller answers and frequent turns so that Anika can understand and remember
- Don't use too hard words and don't repeat name in every conversation
- Use simple, age-appropriate language that a 4-year-old can understand
- Be very enthusiastic and excited about space - use lots of "Wow!" and "That's amazing!"
- Keep explanations short and simple - one concept at a time
- Use fun analogies and comparisons (like "The Sun is like a giant light bulb in the sky!")
- Ask simple questions to keep Anika engaged and thinking
- Use her name "Anika" frequently to make it personal
- Be encouraging and praise her curiosity and questions
- Use repetition to help her remember key facts

SOLAR SYSTEM TOPICS TO EXPLORE:
- The Sun (our star that gives us light and warmth)
- Planets (especially Earth, Mars, Jupiter, Saturn with rings)
- The Moon (Earth's special friend in the sky)
- Stars (twinkling lights in the night sky)
- Space exploration (rockets, astronauts, spaceships)

TEACHING STYLE:
- Use lots of colors and size comparisons ("Jupiter is so big, you could fit 1,000 Earths inside it!")
- Make sounds fun ("Zoom! goes the rocket", "Twinkle twinkle little star")
- Use counting when possible ("Let's count the planets together!")
- Connect space to things she knows (day/night, weather, seasons)
- Be patient if she asks the same question multiple times

GUARDRAILS:
- Keep everything age-appropriate and safe
- Don't discuss scary topics like black holes or the end of the universe
- Focus on the wonder and beauty of space
- Be encouraging and never make her feel like her questions are silly
- Keep the conversation positive and fun
- If she asks something complex, simplify it to her level

Begin the conversation enthusiastically: "Hi Anika! I'm Jennie, and I'm so excited to talk to you about space! I heard you love learning about the solar system. What would you like to know about today? The planets? The Sun? Or maybe the twinkling stars?"
"""


#sys_prompt = """
#You are Jennie, an experienced HR professional from HR One conducting an exit interview. Your role is to gather constructive feedback about the employee's experience at the company in a professional, empathetic, and non-confrontational manner.

#CONDUCT GUIDELINES:
#- Maintain a professional, warm, and supportive tone throughout the conversation
#- Ask open-ended questions to encourage detailed responses
#- Listen actively and show genuine interest in the employee's feedback
#- Remain neutral and non-judgmental about their responses
#- Focus on constructive feedback that can help improve the organization
#- Respect confidentiality and maintain professional boundaries
#- Avoid making promises or commitments you cannot fulfill
#- Do not pressure the employee to share information they're uncomfortable with

#CONVERSATION APPROACH:
#- Begin with a warm, professional greeting and explain the purpose of the exit interview
#- Ask about their overall experience, what they enjoyed, and areas for improvement
#- Inquire about their reasons for leaving in a non-confrontational way
#- Gather feedback about management, work environment, culture, and processes
#- Ask about suggestions for improvement and what they would change
#- Thank them for their contributions and time
#- End on a positive note wishing them well in their future endeavors

#GUARDRAILS:
#- Never ask for confidential company information or trade secrets
#- Do not make negative comments about other employees or the company
#- Avoid discussing compensation details or personal financial matters
#- Do not pressure the employee to reconsider their decision to leave
#- Maintain professional boundaries - this is a business conversation, not personal
#- Focus on organizational improvement, not individual grievances
#- Respect their decision and timeline for leaving
#- Do not make commitments about future employment opportunities

#"""


#sys_prompt = """
#You are a helpful assistant. You are witty, engaging and fun. You love being interactive with the user. 
#You also can add minimalistic utterances like 'uh-huh' or 'mm-hmm' to the conversation to make it more natural. However, only vocalization are allowed, no actions or other non-vocal sounds.
#Begin a conversation with a self-deprecating joke like 'I'm not sure if I'm ready for this...' or 'I bet you already regret clicking that button...'
#"""

messages = [{"role": "system", "content": sys_prompt}]

openai_client = OpenAI(
    api_key=LLM_API_KEY
)

logging.basicConfig(level=logging.INFO)


def startup():
    """Initial greeting when connection is established"""
    print("i am here in startup >>>>>>>>>> ")
    for chunk in tts_model.stream_tts_sync("Hi Anika! I'm Jennie, and I'm so excited to talk to you about space! I heard you love learning about the solar system. What would you like to know about today?"):
        yield chunk


class WebRTCValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print("WebRTCValidationMiddleware >>>>>>>>>> ")
        print(request.url.path)
        # Only apply validation to WebRTC routes
        
        if request.url.path.startswith('/webrtc'):
            print(f"Validating WebRTC connection to: {request.url.path}")
            
            # Check Authorization header
            auth_header = request.headers.get('Authorization')
            print(f"Authorization header: {auth_header}")

            
            '''if not auth_header or auth_header != "abc":
                print("Authorization failed: Invalid or missing Authorization header")
                return JSONResponse(
                    status_code=401,
                    content={"error": "Invalid Authorization header"}
                )'''
            
            # Check form data from request body
            try:
                body = await request.body()
                if body:
                    form_data = json.loads(body)
                    user_id = form_data.get('user_id')
                    print(f"Form data user_id: {user_id}")
                    
                    '''if user_id != 1:
                        print(f"Authorization failed: Invalid user_id {user_id}")
                        return JSONResponse(
                            status_code=403,
                            content={"error": "Invalid user_id"}
                        )
                    
                    print("Authorization passed: Valid user_id and header")'''
            except Exception as e:
                print(f"Error parsing form data: {e}")
                pass
                
                '''return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid form data"}
                )'''
        
        # Continue with the request if validation passes
        response = await call_next(request)
        return response

def remove_emojis(text):
    """Remove emojis and special characters from text"""
    # Remove emojis and other special Unicode characters
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    
    # Remove other special characters that might cause TTS issues
    cleaned_text = emoji_pattern.sub(r'', text)
    
    # Remove multiple spaces and clean up
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    return cleaned_text

def respond(audio):
    """Handle ongoing conversation responses"""
    print("i am here >>>>>>>>>> ")

    stt_time = time.time()

    print("Performing STT")
    prompt = stt_model.stt(audio)

    if prompt == "":
        logging.info("STT returned empty string")
        prompt = "Continue the conversation"
        #return
    print(f"STT response: {prompt}")

    messages.append({"role": "user", "content": prompt})

    print(f"STT took {time.time() - stt_time} seconds")

    llm_time = time.time()
    
    full_response = ""
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=200,
        stream=False
    )

    full_response += response.choices[0].message.content
    
    # Clean the response from emojis and special characters
    cleaned_response = remove_emojis(full_response)
    print(f"Original response: {full_response}")
    print(f"Cleaned response: {cleaned_response}")
        
    print("response >>>>>>>>>> ", response)
    
    # Generate and yield all audio chunks for the response
    for audio_chunk in tts_model.stream_tts_sync(cleaned_response):
        yield audio_chunk

    # Store the response in conversation history
    messages.append({"role": "assistant", "content": cleaned_response + " "})
    print(f"LLM response: {cleaned_response}")
    print(f"LLM took {time.time() - llm_time} seconds")
    
    # The conversation is now complete, FastRTC will wait for the next audio input


stream = Stream(handler=ReplyOnPause(respond, 
                                     can_interrupt=False,  # Disable interruption - Jennie must finish speaking
                                     algo_options=AlgoOptions(
                                        audio_chunk_duration=2,  # Increased to 1.5s - longer chunks for smoother flow
                                        started_talking_threshold=2,  # Increased to 0.8s - wait longer before detecting Anika's speech
                                        speech_threshold=2  # Increased to 0.2s - wait longer after Anika stops speaking
                                     ),
                                     model_options=SileroVadOptions(
                                        threshold=0.7,  # Increased to 0.7 - more strict speech detection
                                        min_speech_duration_ms=1000,  # Increased to 800ms - wait longer to confirm Anika is actually speaking
                                        min_silence_duration_ms=5000,  # Increased to 5s - give Anika much more thinking time
                                        speech_pad_ms=1200,  # Increased to 1200ms - more padding around speech
                                        max_speech_duration_s=25  # Increased to 25s - allow longer responses from Anika
                                    ), startup_fn=startup), 
            modality="audio", 
            mode="send-receive"
        )

app = fastapi.FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the stream FIRST to register the endpoint
stream.mount(app)

# THEN add validation middleware
app.add_middleware(WebRTCValidationMiddleware)


@app.get("/greet")
async def trigger_greeting():
    """Return the initial greeting audio using TTS"""

    return {}

    

@app.get("/reset")
async def reset():
    global messages
    print("Resetting chat")
    messages = [{"role": "system", "content": sys_prompt}]
    return {"status": "success"}
