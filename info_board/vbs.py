from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import requests
from .htmlProcess import html_to_text
import json
import os


@dataclass
class VBSMessage:
    id: str
    title: str
    content_html: str
    content_text: str
    source: str
    facility_name: Optional[str] = None


portCode = {
    "dpWorldNSW": "CTLPB",
    "dpWorldVIC": "CONWS",
    "patrickNSW": "ASLPB",
    "patrickVIC": "ASES1",
    "victVIC": "VICTM",
    "ACFS eDepot": "ACFS",
    "ACFS Elink": "Acfs",
    "ClinkSydneyPark": "CLINK",
    "ContainerSpace": "MAES1",
    "PatrickPortRail": "Clink",
    "TyneAcfsPortBotany": "Acfs",
    "TyneMtMovements": "TYNE",
    "VictInternational": "VICTM"
}

def get_vbs_message_board(
    operation: str,
    timeout_seconds: int = 60,
) -> Dict[str, List[VBSMessage]]:
    """
    Fetch VBS Message Board messages and group by facility_name.

    API (assumed / from your usage):
    - POST /bsb/messageBoard/vbs
    - JSON body: {"operation": "..."}
    - success=false => raise RuntimeError
    - content is HTML
    """
    url = "http://67.219.102.137:8080/bsb/messageBoard/vbs"
    payload: Dict[str, Any] = {"operation": operation}

    resp = requests.post(url, json=payload, timeout=timeout_seconds)
    resp.raise_for_status()
    print(resp.raise_for_status())
    result = resp.json()

    # 和 containerchain 一样：success 检查
    if "success" in result and not result.get("success"):
        raise RuntimeError(result.get("message") or "VBS messageBoard failed")

    data = (
        result.get("data", []) or []
    )
    if data is None:
        data = []
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected VBS response data type: {type(data)}")

    grouped: Dict[str, List[VBSMessage]] = {}

    for item in data:
        if not isinstance(item, dict):
            continue

        facility_name = operation

        content_html = (
            item.get("content")
            or item.get("content_html")
            or item.get("body")
            or item.get("message")
            or ""
        )
        content_html = str(content_html or "")

        msg = VBSMessage(
            id=str(item.get("id", "") or item.get("_id", "") or ""),
            title=str(item.get("title", "") or ""),
            content_html=content_html,
            content_text=html_to_text(content_html),
            source=str(item.get("source", "") or "vbs"),
            facility_name=facility_name,
        )

        grouped.setdefault(facility_name, []).append(msg)

    return [
        {
            "facility": name,
            "title": msg.title,
            "content": msg.content_text,
        }
        for name, msgs in grouped.items()
        for msg in msgs
    ]

# Test script
def update_vbs():
    boards = []
    for f in portCode:
        try:
            boards.extend(get_vbs_message_board(f))
        except Exception as exc:
            print("vbs fetch failed for {}: {}".format(f, exc))
    return boards
    # os.makedirs("./data", exist_ok=True)
    # with open("./data/information_board.json", "w", encoding="utf-8") as f:
    #     json.dump(boards, f, ensure_ascii=False, indent=2)

    # print("write_vbs_message_board is done.\n")
