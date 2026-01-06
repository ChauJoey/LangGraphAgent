import os
import json
from info_board.containerchain import update_containerchains
from info_board.vbs import update_vbs
import time
import redis
from redis.commands.json.path import Path

import os
from dotenv import load_dotenv
load_dotenv()

# Redis client
redis_client = redis.Redis(
    host=os.environ["REDIS_HOST"],
    port=os.environ["REDIS_PORT"],
    decode_responses=True,
    username=os.environ["REDIS_USER"],
    password=os.environ["REDIS_PASSWORD"]
)

def main():
    boards = update_vbs()
    boards.extend(update_containerchains())
    redis_client.json().set("information_board", Path.root_path(), boards)

if __name__ == "__main__":
    print("update begin")
    main()
    print("update completed")