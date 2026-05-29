from fastapi import FastAPI
from pydantic import BaseModel
import requests
import asyncio
import random
import re

app = FastAPI()

# ─── HUGE curated human response bank ───────────────────────────────────────
RESPONSES = {
    "greeting": [
        "yo", "sup", "hey bro", "wassup", "yooo", "omg heyy",
        "bruh finally", "yo yo", "hiii", "sup dude", "ayo",
        "waddup", "heyyy", "eyy sup", "ayo wassup"
    ],
    "play": [
        "yeah lets go", "omg yes fr", "lets gooo", "aight bet",
        "im down fr", "lets get it", "yesss finally", "lets run it",
        "ofc bro", "lets goooo", "yes omg", "fr lets go",
        "bet lets do it", "ong lets go", "aight lets run it"
    ],
    "insult": [
        "bruh stop", "ratio", "L bozo", "ur actually bad lol",
        "skill issue fr", "get good lol", "L + ratio", "touch grass bro",
        "nah ur worse", "bruh ur terrible lol", "lmaooo ur bad",
        "bro is cooked", "massive L", "cope + ratio", "ur so bad omg"
    ],
    "gg": [
        "gg ez", "gg no re", "too ez lol", "gg bro", "ggs",
        "ez clap", "we won lets go", "gg fr fr", "gg gg",
        "lol gg", "ez game", "gg no diff", "gg goated ngl"
    ],
    "question": [
        "idk lol", "maybe idk", "idk bro", "ngl idk",
        "prolly yeah", "maybe fr", "idk u tell me", "bro idk",
        "how would i know lol", "idk ask someone else"
    ],
    "no": [
        "nah", "nah bro", "nope lol", "nah im good", "nah fr",
        "nah not rn", "nope", "nah bro im busy", "hard no lol",
        "nah fam", "nope fr", "nah no cap"
    ],
    "yes": [
        "yeah fr", "yes omg", "yeah bro", "yep lol", "ofc",
        "yeah no cap", "yes fr fr", "ofc bro", "obviously lol",
        "yeah duh", "ong yes", "yes bro omg"
    ],
    "cool": [
        "fr fr", "no cap", "ngl thats fire", "bro thats actually cool",
        "omg fr", "thats W", "no cap thats hard", "W fr",
        "bro thats goated", "ong thats fire", "ngl W move",
        "thats actually bussin", "bro W"
    ],
    "mad": [
        "bruh chill", "bro stop", "why tho lol", "bruh",
        "bro relax", "why u mad lol", "chill bro omg",
        "bro its just a game lol", "L mindset", "ong chill"
    ],
    "trade": [
        "nah", "what u offering", "depends lol", "nah not worth",
        "maybe wat u got", "nah im good bro", "lol no",
        "what u want for it", "nah bro bad deal"
    ],
    "help": [
        "lol figure it out", "nah im grinding rn", "maybe later",
        "idk how either lol", "ask someone else bro",
        "bro google it lol", "idk fr", "not my problem lol"
    ],
    "win": [
        "lets gooo", "gg we won", "ez win fr", "we ate that up",
        "no diff lol", "gg goated run", "we cooked them",
        "bro we won gg", "ez dub", "dub secured fr"
    ],
    "lose": [
        "gg we tried", "bro we got cooked lol", "oof L",
        "nah we'll win next time", "massive L ngl", "bro gg tho",
        "we got ratio'd lol", "L but gg", "bro we got bozo'd"
    ],
    "bored": [
        "same lol", "bro same fr", "lets find smth to do",
        "wanna grind", "bro im dead too", "ong same",
        "lets do smth", "fr im dying of boredom"
    ],
    "money": [
        "broke lol", "nah i spent it all", "bro same im broke",
        "robux? nah im poor lol", "spent it all on skins lol"
    ],
    "default": [
        "lol ok", "bruh", "fr fr", "ngl same", "omg lol",
        "bro wat", "lol ok then", "aight", "ngl fr", "oof lol",
        "bro stop lol", "omg fr fr", "nah bro", "lmao ok",
        "wait wat", "huh lol", "bro ok lol", "fr tho",
        "lmaooo", "bruh moment", "ong lol", "bro what",
        "aight then lol", "ok bro lol", "ngl lol", "bro fr",
        "lol wut", "ok and", "bruh fr", "ong fr fr"
    ]
}

# ─── Intent detection ────────────────────────────────────────────────────────
KEYWORDS = {
    "greeting":  ["hi", "hey", "hello", "sup", "yo", "wassup", "heyy", "ayo"],
    "play":      ["play", "wanna", "game", "join", "come", "lets", "let's", "squad"],
    "insult":    ["bad", "trash", "noob", "terrible", "worst", "suck", "loser", "idiot", "awful", "garbage"],
    "gg":        ["gg", "good game", "well played", "wp", "ez"],
    "no":        ["no", "nah", "don't", "stop", "quit", "leave", "never"],
    "yes":       ["yes", "yeah", "yep", "sure", "ok", "okay", "alright", "bet"],
    "cool":      ["cool", "nice", "fire", "sick", "awesome", "amazing", "great", "hard", "bussin"],
    "mad":       ["mad", "angry", "upset", "hate", "annoying", "ugh", "toxic"],
    "trade":     ["trade", "give", "swap", "exchange", "deal"],
    "help":      ["help", "how", "stuck", "cant", "broken"],
    "win":       ["win", "won", "victory", "beat", "clap", "dub"],
    "lose":      ["lost", "lose", "died", "eliminated", "failed"],
    "bored":     ["bored", "boring", "nothing", "dead", "slow"],
    "money":     ["robux", "money", "broke", "rich", "buy"],
}

# ─── Recent reply tracking (anti-repeat) ────────────────────────────────────
recent_replies = []

def detect_intent(message: str) -> str:
    msg = message.lower()
    for intent, words in KEYWORDS.items():
        for word in words:
            if word in msg:
                return intent
    return "default"

def is_human_response(text: str) -> bool:
    if not text or len(text.split()) > 9:
        return False
    formal = [
        "certainly", "absolutely", "indeed", "however", "therefore",
        "furthermore", "additionally", "I am", "I will", "I would",
        "assist", "help you", "of course", "please", "thank",
        "I'm here", "I can", "Let me", "I'd be", "explore",
        "studying", "narrative", "instruction", "trade, so"
    ]
    for word in formal:
        if word.lower() in text.lower():
            return False
    return True

def clean_reply(text: str) -> str:
    text = text.strip().strip('"').strip("'")
    text = re.sub(r'\*.*?\*', '', text)
    text = text.split("\n")[0].split("Player:")[0].split("->")[0]
    return text.strip()

def get_curated(intent: str) -> str:
    global recent_replies
    pool = RESPONSES.get(intent, RESPONSES["default"])
    available = [r for r in pool if r not in recent_replies]
    if not available:
        available = pool
    reply = random.choice(available)
    recent_replies.append(reply)
    if len(recent_replies) > 10:
        recent_replies.pop(0)
    return reply

# ─── Routes ─────────────────────────────────────────────────────────────────
class Message(BaseModel):
    player_name: str
    message: str

@app.post("/chat")
async def chat(data: Message):
    intent = detect_intent(data.message)
    loop = asyncio.get_event_loop()

    try:
        response = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen2:0.5b",
                    "prompt": (
                        f'Roblox kid reply, 4 words max, all lowercase, '
                        f'slang only (lol bruh gg fr omg ngl bro ez). '
                        f'Message: "{data.message}"\nReply:'
                    ),
                    "stream": False,
                    "options": {
                        "temperature": 0.85,
                        "num_predict": 8,
                        "num_ctx": 48,
                        "stop": ["\n", "Player", "Message", "->", ":"]
                    }
                },
                timeout=2
            )),
            timeout=2.5
        )
        ai_reply = clean_reply(response.json().get("response", ""))
        if is_human_response(ai_reply):
            return {"reply": ai_reply}
    except Exception:
        pass

    # fallback to curated human response
    return {"reply": get_curated(intent)}

@app.get("/health")
async def health():
    return {"status": "ok"}
