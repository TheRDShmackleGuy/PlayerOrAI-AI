from fastapi import FastAPI
from pydantic import BaseModel
import requests
import random
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Your existing RESPONSES dictionary (keeping it the same)
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

recent_replies = []

def detect_intent(message: str) -> str:
    msg = message.lower()
    for intent, words in KEYWORDS.items():
        for word in words:
            if word in msg:
                return intent
    return "default"

def is_human_response(text: str) -> bool:
    if not text or len(text.split()) > 8:
        return False
    
    # Much stricter formal detection
    formal_phrases = [
        "hello", "how can i", "assist", "help you", "today", "certainly", 
        "i am", "i will", "please", "thank you", "of course", "i'd be happy"
    ]
    
    text_lower = text.lower()
    for phrase in formal_phrases:
        if phrase in text_lower:
            return False
    
    # Must have slang or be very short
    slang = ["bruh", "lol", "fr", "omg", "gg", "ngl", "bro", "ez", "ong", "bet", "yo", "sup", "yep", "nah"]
    has_slang = any(word in text_lower for word in slang)
    
    return has_slang or len(text.split()) <= 3

def clean_reply(text: str) -> str:
    if not text:
        return ""
    
    text = text.strip().strip('"').strip("'")
    text = re.sub(r'\*.*?\*', '', text)
    
    # Take only first part before separators
    for separator in ["\n", "Player:", "->", "Message:", "Reply:", "!", "?"]:
        text = text.split(separator)[0]
    
    # Remove punctuation at the end
    text = re.sub(r'[.!?]+$', '', text.strip())
    
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

class Message(BaseModel):
    player_name: str
    message: str

@app.post("/chat")
async def chat(data: Message):
    intent = detect_intent(data.message)
    
    try:
        logger.info(f"Attempting AI generation for: '{data.message}' (intent: {intent})")
        
        # Much more aggressive prompt
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2:0.5b",
                "prompt": (
                    f"You are a 12 year old roblox player. Reply with only slang, no formal words ever. "
                    f"Examples: 'yo', 'bruh', 'fr fr', 'lol ok', 'nah bro', 'gg ez', 'omg lol'. "
                    f"Message: {data.message}\n"
                    f"Roblox kid says:"
                ),
                "stream": False,
                "options": {
                    "temperature": 1.2,
                    "num_predict": 6,
                    "num_ctx": 32,
                    "stop": ["\n", ".", "!", "?", "Message", "Player", "says"]
                }
            },
            timeout=8  # Longer timeout
        )
        
        if response.status_code == 200:
            raw_response = response.json().get("response", "")
            logger.info(f"Raw AI response: '{raw_response}'")
            
            ai_reply = clean_reply(raw_response)
            logger.info(f"Cleaned AI response: '{ai_reply}'")
            
            if ai_reply and is_human_response(ai_reply):
                logger.info(f"Using AI response: '{ai_reply}'")
                return {"reply": ai_reply, "source": "ai"}
            else:
                logger.info(f"AI response filtered out - too formal")
                
    except Exception as e:
        logger.error(f"AI generation failed: {str(e)}")

    # Fallback
    curated_reply = get_curated(intent)
    logger.info(f"Using curated response: '{curated_reply}' (intent: {intent})")
    return {"reply": curated_reply, "source": "curated"}

@app.get("/health")
async def health():
    return {"status": "ok"}
