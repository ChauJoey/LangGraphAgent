from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain.tools import tool
from dataclasses import dataclass
from typing import TypedDict, List, Literal, Optional, Dict, Any
from langgraph.graph import StateGraph
from langgraph.types import Command
from googlesheet.worker import get_records_by_ctn_numbers
import re
import json
from rapidfuzz import fuzz
import redis

import os
from dotenv import load_dotenv
load_dotenv()

llm = HuggingFaceEndpoint(
    endpoint_url="openai/gpt-oss-120b",
    provider="scaleway",
    temperature=0,
    max_new_tokens=2000,
    huggingfacehub_api_token=os.environ["HUGGINFACE_INFERENCE_TOKEN"]
)

model = ChatHuggingFace(llm=llm)



def load_message_board_json() -> List[Dict]:
    info = redis.Redis(
        host=os.environ["REDIS_HOST"],
        port=os.environ["REDIS_PORT"],
        decode_responses=True,
        username=os.environ["REDIS_USER"],
        password=os.environ["REDIS_PASSWORD"]
    ).json().get("information_board") or []

    return info

# compare similar
def facility_similarity(a: str, b: str) -> float:
    """
    a: empty park
    b: board["facility"]
    """
    a = a.lower()
    b = b.lower()
    if not a or not b:
        return 0.0
    return fuzz.partial_ratio(a,b) / 100.0

@dataclass
class State(TypedDict):
    user_input: str

    ctn_records: Optional[List[Dict[str, Any]]]

    empty_parks: Optional[Dict[str, str]]          # CTN -> Empty Park
    related_notices: Optional[List[Dict[str, Any]]]
    final_return_depots: Optional[Dict[str, List[str]]]


def classification(state: State) -> Command[Literal["dehire", "query"]]:
    user_input = state.get("user_input")
    # print(f"user: {user_input}")
    classification_prompt = f"""
        You are a container task classifier.

        Allowed outputs:
        Dehire
        Query

        Rules:
        - Output exactly ONE word from the allowed outputs.
        - Any extra text is invalid.
        - keyword: dehire, return to or 还柜 all belong to dehire task

        User message:
        {user_input}
    """

    task_type = model.invoke(classification_prompt).content
    if task_type == "Dehire":
        goto = "dehire"
    elif task_type == "Query":
        goto = "query"

    # print(goto)
    return Command(
        goto=goto
    )

def dehire(state: State):
    print("goto Dehire")
    user_input = state.get("user_input")

    pattern = re.compile(r"\b[A-Z]{4}\d{7}\b")

    containers = [m.group().upper() for m in pattern.finditer(user_input)]

    # print(containers)

    # ["CTN NUMBER", "Shipping Line", "Empty Park", "Last Dention"]
    ctn_records = get_records_by_ctn_numbers(containers)

    return {"ctn_records": ctn_records}

def resolve_empty_park(state: State):
    records = state["ctn_records"]

    empty_parks = {}
    for r in records:
        ctn = r.get("CTN NUMBER")
        park = r.get("Empty Park")
        if ctn and park:
            empty_parks[ctn] = park
    # print(empty_parks)
    return {"empty_parks": empty_parks}


def search_information_board(state: State):
    empty_parks = state["empty_parks"]
    boards = load_message_board_json()  # load information board

    related = []

    # find empty park information board
    for info in boards:
        facility = info["facility"].lower()
        title = info["title"].lower()
        # print(f"search_information_board: {facility} {title}")
        # accept information
        if "accept" in title:
            related.append(info)
            continue
        if "redirect" in title:
            for park in set(empty_parks.values()):
                if facility_similarity(park, facility) > 0.5:
                    related.append(info)
                    break
    
    related = json.dumps(related, ensure_ascii=False, indent=2)
    # print("related: ", related)
    return {"related_notices": related}

def analyze_return_depot(state: State):
    records = state["ctn_records"]
    notices = state["related_notices"]

    dehire_prompt = f"""
        You are a container logistics assistant.

        Your task is to determine the FINAL empty return depot (dehire depot)
        for each container based on:

        1. Container records (facts)
        2. Related depot notices (evidence)

        You must strictly follow the rules below.

        ========================
        Container Records
        ========================
        Each record includes:
        - CTN NUMBER
        - Shipping Line
        - Container Type (e.g. 20GP, 40HC, Reefer)
        - Default Empty Park (system record)

        Records:
        {records}

        ========================
        Depot Notices
        ========================
        Each notice includes:
        - facility (depot name)
        - title
        - content

        Notices:
        {notices}

        ========================
        Decision Rules (IMPORTANT)
        ========================

        1. Redirect notices have the HIGHEST priority.
        - If a notice explicitly says containers of a specific shipping line
            or container type are redirected to another depot,
            you MUST use the redirected depot.

        2. Accept notices are the SECOND priority.
        - If a notice says a depot ACCEPTS containers of a specific shipping line
            or container type, that depot is VALID for return,
            even if it is different from the default empty park.

        3. Accept notices may NOT apply to all containers.
        - You MUST check:
            - Shipping line match
            - Container type match

        4. Informational notices (e.g. "no current redirections")
        do NOT change the return depot.

        5. If multiple depots are valid:
        - List ALL valid depots.

        6. If NO notice applies to a container:
        - Use the Default Empty Park from the container record.

        ========================
        Output Format (STRICT)
        ========================

        Return ONLY valid JSON.
        Do NOT include explanations.

        Example Format:
        {{
        "<CTN NUMBER>": ["<DEPOT NAME1>", "<DEPOT NAME2>"]
        }}

        ========================
        Now determine the final return depot(s).
        """
    # print(records)
    result = model.invoke(dehire_prompt).content
    # print(f"final: {result}")
    return {
        "final_return_depots": result
    }


def query(state: State):
    print("goto Query")
    return {}

workflow = StateGraph(State)
workflow.add_node("classification", classification)
workflow.add_node("dehire", dehire)
workflow.add_node("query", query)
workflow.add_node("resolve_empty_park", resolve_empty_park)
workflow.add_node("search_information_board", search_information_board)
workflow.add_node("analyze_return_depot", analyze_return_depot)

workflow.add_edge("__start__", "classification")
workflow.add_edge("dehire", "resolve_empty_park")
workflow.add_edge("resolve_empty_park", "search_information_board")
workflow.add_edge("search_information_board", "analyze_return_depot")
workflow.compile(name="New Graph")

agent = workflow.compile()

# # Invoke

# # result = agent.invoke({"user_input": "where to dehire OOLU9933088 TEMU5943297"})
# user_input = {"user_input": "where to dehire OOLU9933088 TEMU5943297"}
# # print(user_input)
# result = agent.invoke({"user_input": "where to dehire OOLU9933088 TEMU5943297"})
# print(result["final_return_depots"])
