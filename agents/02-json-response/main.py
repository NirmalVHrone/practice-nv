import os
import json
from typing import Annotated
from typing_extensions import TypedDict
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from openai import OpenAI

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Topic(TypedDict):
    topic: str
    json_response: list[dict]


def explain_topic(state: Topic):
    json_example = """
    {
        "flashcards": [
            {
                "title": "critical word or concept name in max 4-5 words",
                "explanation_meaning": "meaning of the critical word or concept in 1-2 sentences",
            }
        ]
    }
    """

    response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f'''You are a helpful teaching assistant. You take a topic as input and return contents for flash cards.
                 
                 1. Flash cards could have a word with their meaning as well as concepts with their explanations.
                 2. The concept explanation can be in 1-2 sentences maximum.
                 3. You should generate minimum 5 or maximum 10 flash cards from the topic.
                 4. You always respond in valid JSON.
                 5. The text of title and explanation_meaning should be in English language
                 6. Generated data must be in markdown format with emojis, bold, italic, and underline, etc to make it more beautiful and engaging.
                 7. In case of concepts add examples to make it more engaging.
                 8. You can generate 5-10 word meanings and 5-10 concept explanations.

                 
                 The json should be in the following format:
                 {json_example}

                 '''},
                {"role": "user", "content": f'Generate flash cards for the topic: {state["topic"]}'},
            ],
            response_format={"type": "json_object"}
        )

    json_str = response.choices[0].message.content
    data = json.loads(json_str)
    state["json_response"] = data
    return state
    

if __name__ == "__main__":
    graph = StateGraph(Topic)

    graph.add_node("explain_topic", explain_topic)
    graph.add_edge(START, "explain_topic")
    graph.add_edge("explain_topic", END)

    app = graph.compile()


    state = Topic(topic="2 digit numbers addition")
    result = app.invoke(state)

    output = result["json_response"]['flashcards']
    for item in output:
        print(item["title"])
        print(item["explanation_meaning"])
        print("--------------------------------\n\n\n")
    

    