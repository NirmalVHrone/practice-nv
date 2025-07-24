import os

from typing import Annotated
from typing_extensions import TypedDict
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

llm = init_chat_model("openai:gpt-4o-mini", temperature=0.2)

class Topic(TypedDict):
    topic: str
    explanation: str


def explain_topic(state: Topic):
    response = llm.invoke(
        [
            {
                "role": "system",
                "content": """You are a helpful assistant that explains topics. Give a 
             explanation of the topic in a way that is easy to understand.
             
             The explanation should be in the form of a story.
             Respond in Markdown format with title, subtitle, and body. Use emojis, bold, italic, and underline to make it more engaging.
             """
            },
            {"role": "user", "content": state["topic"]},
        ]
    )
    state["explanation"] = response.content
    return state
    

if __name__ == "__main__":
    graph = StateGraph(Topic)

    graph.add_node("explain_topic", explain_topic)
    graph.add_edge(START, "explain_topic")
    graph.add_edge("explain_topic", END)

    app = graph.compile()

    '''
    print("--------------------------------\n\n\n")
    print("2 digit numbers addition")
    print("--------------------------------\n\n\n")

    state = Topic(topic="2 digit numbers addition")
    result = app.invoke(state)
    print(result)

    print("--------------------------------\n\n\n")
    print(result["explanation"])
    '''

    #for event in app.stream({"topic": "2 digit numbers addition"}):
    #    for value in event.values():
    #         print("Assistant: ", value["explanation"])

    for message_chunk, metadata in app.stream( {"topic": "2 digit numbers addition"},stream_mode="messages",
    ):
        if message_chunk.content:
            print(metadata["langgraph_node"])
            #print(message_chunk.content, end="|", flush=True)
