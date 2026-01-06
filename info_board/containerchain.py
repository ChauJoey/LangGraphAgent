from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import requests
from .htmlProcess import html_to_text
import json
import os

@dataclass
class CCMessage:
    id: str
    title: str
    content_html: str
    content_text: str
    source: str
    facility_id: Optional[int] = None
    facility_name: Optional[str] = None

def get_containerchain_message_board(
    date_str: Optional[str] = None,
    timeout_seconds: int = 60,
) -> Dict[str, List[CCMessage]]:
    """
    Fetch ContainerChain Message Board messages and group by facility_name.

    API (from your doc):
    - POST /bsb/messageBoard/containerchain
    - JSON body: {"dateStr": "YYYY-MM-DD"}  (optional; omit to use today's date)
    - success=false => raise RuntimeError
    - content is HTML; facility info included in each message
    """
    url = "http://67.219.102.137:8080/bsb/messageBoard/containerchain"
    payload: Dict[str, Any] = {}
    if date_str:
        payload["dateStr"] = date_str  # must be YYYY-MM-DD

    resp = requests.post(url, json=payload, timeout=timeout_seconds)
    resp.raise_for_status()
    print(resp.raise_for_status())
    result = resp.json()

    if not result.get("success"):
        raise RuntimeError(result.get("message") or "ContainerChain messageBoard failed")

    data = result.get("data", []) or []

    grouped: Dict[str, List[CCMessage]] = {}
    for item in data:
        facility_name = item.get("facility_name") or "Unknown"
        msg = CCMessage(
            id=str(item.get("id", "")),
            title=str(item.get("title", "")),
            content_html=str(item.get("content", "") or ""),
            content_text=html_to_text(str(item.get("content", "") or "")),
            source=str(item.get("source", "")),
            facility_id=item.get("facility_id"),
            facility_name=item.get("facility_name"),
        )
        grouped.setdefault(facility_name, []).append(msg)

    return [
        {
            "facility": name,
            "title": msg.title,
            "content": msg.content_text
        }
        for name, msgs in grouped.items()
        for msg in msgs
    ]



# Write down containerchain_message_board to somewhere
# def write_containerchain_message_board():

def update_containerchains():
    boards = get_containerchain_message_board()
    return boards
    # os.makedirs("./data", exist_ok=True)
    # with open("./data/information_board.json", "w+", encoding="utf-8") as f:
    #     json.dump(boards, f, ensure_ascii=False, indent=2)

    # print("write_containerchain_message_board is done.\n")
