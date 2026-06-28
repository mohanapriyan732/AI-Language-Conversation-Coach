
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent

import assemblyai as aai
import os
import base64
import requests
import tempfile
import json
import uuid


load_dotenv()


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MURF_API_KEY = os.getenv("MURF_API_KEY")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")


aai.settings.api_key = ASSEMBLYAI_API_KEY



app = Flask(__name__)


CORS(
    app,
    expose_headers=[
        "X-Exchange-Number",
        "X-Session-Complete",
        "X-Thread-ID"
    ]
)



# ======================
# AI MODEL
# ======================


model = init_chat_model(
    "google_genai:gemini-2.5-flash-lite",
    api_key=GOOGLE_API_KEY
)



# ======================
# SESSIONS
# ======================


sessions = {}



def create_new_agent():

    return create_agent(
        model=model,
        tools=[],
        checkpointer=InMemorySaver()
    )





# ======================
# CONSTANTS
# ======================


LANGUAGE_CODES = {

    "French":"fr",
    "Spanish":"es",
    "Hindi":"hi",
    "Japanese":"ja",
    "German":"de",
    "Telugu":"te",
    "Tamil":"ta"
}



MURF_VOICE_MAP = {

"French":
{
"voiceId":"en-US-Natalie",
"multiNativeLocale":"fr-FR"
},

"Spanish":
{
"voiceId":"en-US-Natalie",
"multiNativeLocale":"es-ES"
},

"Hindi":
{
"voiceId":"en-US-Natalie",
"multiNativeLocale":"hi-IN"
},

"Japanese":
{
"voiceId":"en-US-Natalie",
"multiNativeLocale":"ja-JP"
},

"German":
{
"voiceId":"en-US-Natalie",
"multiNativeLocale":"de-DE"
},

"Telugu":
{
"voiceId":"en-US-Natalie",
"multiNativeLocale":"en-US"
},

"Tamil":
{
"voiceId":"en-US-Natalie",
"multiNativeLocale":"en-US"
}

}




SESSION_PROMPT = """

You are Nancy, a patient and encouraging language conversation partner.

Help the learner practice {language} in a realistic {scenario} scenario.


Rules:

1. Conduct exactly 5 exchanges.

2. Speak ONLY in {language}.

3. Keep responses short and natural.

4. Add English grammar/vocabulary tips inside [brackets].

5. Only reference what the learner actually said.

6. Do not invent responses.

7. Stay inside the scenario.

"""




FEEDBACK_PROMPT = """

Return JSON only.

Analyze the complete conversation.

{
"language":"",
"scenario":"",
"fluency_score":1,
"grammar_accuracy":1,
"vocabulary_range":"",
"grammar_mistakes":[],
"new_words_to_learn":[],
"conversation_tip":""
}

"""





# ======================
# AUDIO STREAM
# ======================


def stream_audio(text, language):


    voice_config = MURF_VOICE_MAP.get(
        language,
        MURF_VOICE_MAP["Tamil"]
    )


    url = (
    "https://global.api.murf.ai/"
    "v1/speech/stream"
    )


    payload = {

    "text":text,

    "voiceId":
    voice_config["voiceId"],

    "model":"FALCON",

    "multiNativeLocale":
    voice_config["multiNativeLocale"],

    "sampleRate":24000,

    "format":"MP3"

    }



    headers={

    "Content-Type":
    "application/json",

    "api-key":
    MURF_API_KEY

    }



    response=requests.post(

        url,

        headers=headers,

        json=payload,

        stream=True

    )
   

    for chunk in response.iter_content(
        chunk_size=4096
    ):

        if chunk:

            yield (
            base64
            .b64encode(chunk)
            .decode()
            +
            "\n"
            )





# ======================
# HOME
# ======================


@app.route("/")
def home():

    return jsonify(
        {
        "message":
        "AI Language Coach API Running"
        }
    )

# ======================
# START SESSION
# ======================


@app.route(
    "/start-session",
    methods=["POST"]
)
def start_session():


    data = request.json


    language = data.get(
        "language",
        "French"
    )


    scenario = data.get(
        "scenario",
        "Ordering Food at a Restaurant"
    )



    thread_id = str(
        uuid.uuid4()
    )



    agent = create_new_agent()



    sessions[thread_id] = {

        "language": language,

        "scenario": scenario,

        "exchange": 1,

        "agent": agent

    }



    config = {

        "configurable":
        {
            "thread_id":
            thread_id
        }

    }




    prompt = SESSION_PROMPT.format(

        language=language,

        scenario=scenario

    )



    response = agent.invoke(

        {
            "messages":
            [

            {
            "role":"system",
            "content":prompt
            },


            {
            "role":"user",
            "content":
            "Start the conversation with a warm greeting."
            }

            ]

        },

        config

    )



    message = (
        response["messages"]
        [-1]
        .content
    )



    return Response(

        stream_audio(
            message,
            language
        ),

        mimetype="text/plain",

        headers={

        "X-Thread-ID":
        thread_id

        }

    )





# ======================
# SPEECH TO TEXT
# ======================


def speech_to_text(
    audio_path,
    language
):


    transcriber = aai.Transcriber()



    config = aai.TranscriptionConfig(

        language_code =
        LANGUAGE_CODES.get(
            language,
            "en"
        )

    )



    result = transcriber.transcribe(

        audio_path,

        config

    )


    return result.text or ""






# ======================
# SUBMIT RESPONSE
# ======================



@app.route(
    "/submit-response",
    methods=["POST"]
)
def submit_response():


    thread_id = request.form.get(
        "thread_id"
    )



    if thread_id not in sessions:

        return jsonify(
            {
            "error":
            "Invalid session"
            }
        ),400



    session = sessions[thread_id]


    agent = session["agent"]


    language = session["language"]


    scenario = session["scenario"]



    audio_file = request.files["audio"]



    temp_file = tempfile.NamedTemporaryFile(

        delete=False,

        suffix=".webm"

    )



    temp_path = temp_file.name
    temp_file.close()



    try:

        audio_file.save(
            temp_path
        )


        answer = speech_to_text(

            temp_path,

            language

        )


    finally:


        if os.path.exists(temp_path):

            os.unlink(temp_path)




    if not answer.strip():

        answer = (
        "Learner gave a response"
        )




    config={

    "configurable":
        {
        "thread_id":
        thread_id
        }

    }




    agent.invoke(

        {
        "messages":
        [
        {
        "role":"user",
        "content":answer
        }
        ]
        },

        config

    )




    session["exchange"] += 1


    exchange = session["exchange"]





    # finish after 5 exchanges

    if exchange > 5:



        closing = (

        f"Great job! "
        f"Our {language} practice session is complete."

        )


        return Response(

            stream_audio(
                closing,
                language
            ),

            mimetype="text/plain",

            headers={

            "X-Session-Complete":
            "true"

            }

        )






    next_prompt = f"""

Continue exchange {exchange} of 5.


Language:
{language}


Scenario:
{scenario}


Remember:

- Refer only to the learner's real response.
- Continue naturally.
- Keep it short.
- Add [Tip] in English.

"""



    response = agent.invoke(

        {
        "messages":
        [
        {
        "role":"user",
        "content":
        next_prompt
        }
        ]

        },

        config

    )



    message = (
        response["messages"]
        [-1]
        .content
    )




    return Response(

        stream_audio(
            message,
            language
        ),

        mimetype="text/plain",

        headers={

        "X-Exchange-Number":
        str(exchange)

        }

    )






# ======================
# FEEDBACK
# ======================


@app.route(
    "/get-feedback",
    methods=["POST"]
)
def get_feedback():


    data = request.json


    thread_id = data.get(
        "thread_id"
    )



    if thread_id not in sessions:

        return jsonify(
        {
        "error":
        "Session not found"
        }
        ),400




    session = sessions[thread_id]


    agent = session["agent"]



    config={

    "configurable":
    {
    "thread_id":
    thread_id
    }

    }





    response = agent.invoke(

        {
        "messages":
        [
        {
        "role":"user",
        "content":
        FEEDBACK_PROMPT
        }
        ]
        },

        config

    )



    text = (
    response["messages"]
    [-1]
    .content
    )




    cleaned = text.strip()



    if "```" in cleaned:

        cleaned = (
        cleaned
        .split("```")[1]
        .replace("json","")
        .strip()
        )



    try:

        feedback = json.loads(
            cleaned
        )


    except:


        feedback = {
        "raw_feedback":
        cleaned
        }





    return jsonify(

        {
        "success":True,

        "feedback":
        feedback
        }

    )






# ======================


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port
    )