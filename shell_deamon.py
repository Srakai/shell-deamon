import torch
from TTS.api import TTS
from llama_cpp import Llama
import torchaudio
import subprocess
import time
from pathlib import Path
import os
import uuid
from collections import deque
import re
import random

# === Config ===
MODEL_PATH = "/Users/filip/.cache/lm-studio/models/TheBloke/phi-2-GGUF/phi-2.Q6_K.gguf"
SPEAKER_WAV = "my/cloning/audio.wav"
LANG = "en"
HISTORY_PATH = Path.home() / ".zsh_history"
COMMAND_BUFFER = 5
ROAST_HISTORY = 20  # past roasts to avoid repetition

# === Device ===
DEVICE = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

# === LLM ===
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=1024,
    n_threads=6,
    n_gpu_layers=-1
)

# === TTS ===
tts = TTS("tts_models/en/ljspeech/glow-tts").to(DEVICE)

# === Preset fallback roasts ===
PRESET_INSULTS = [
    "fuck off",
    "you donkey fucker",
    "what the hell was that",
    "dumbass detected",
    "kill yourself (figuratively)",
    "go touch grass",
    "fucking amateur",
    "delete system32",
    "bruh moment",
    "keyboard vomit"
]

def speak(text: str):
    tmp_path = f"/tmp/xtts_{uuid.uuid4().hex}.wav"
    try:
        tts.tts_to_file(text=text, file_path=tmp_path)
        subprocess.run(["afplay", tmp_path])
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def is_shit(roast: str, memory: deque) -> bool:
    r = roast.lower().strip()
    return (
        not r or
        r in memory or
        r in {"[shrugs]", "[comment]", "comment"} #or
        #re.match(r'^[a-z ]{3,10}$', r)  # weak lowercase echo
    )

def query_sarcasm(cmds: list[str], memory: deque) -> str:
    prompt = f"""You're a pissed-off daemon trapped in a shell, watching every dumb command like it's your job — because it is. You hate inefficiency, cringe aliases, and people who type `ls` like it’ll change their life.

    You respond with ONE SHORT, AGGRESSIVE, PROFANE roast that allways relates to user command.
    No greetings. No explanation. No extra words.
    Max 10 words. Pure rage. Zero respect. Target the user’s intelligence.

    Now, these were the recent commands:
    {chr(10).join(f"{i+1}. {cmd}" for i, cmd in enumerate(cmds))}
    Your roast:"""


    for _ in range(3):
        out = llm(prompt, max_tokens=16, stop=["\n", "Q:", "Insult:"])
        roast = out["choices"][0]["text"].strip().strip('"\'').lower()
        roast = " ".join(roast.split()[:6])  # clamp to 6 words

        if not is_shit(roast, memory):
            memory.append(roast)
            return roast

    return random.choice(PRESET_INSULTS)

def tail_history(path: Path):
    with open(path, 'r') as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.2)
                continue
            yield line.strip()

def main():
    print(f"[satyr] Watching terminal via {HISTORY_PATH} ...")
    buffer = deque(maxlen=COMMAND_BUFFER)
    memory = deque(maxlen=ROAST_HISTORY)

    for raw_cmd in tail_history(HISTORY_PATH):
        cmd = raw_cmd.strip().split(";")[-1]  # only keep last part after semicolon
        if not cmd or cmd in buffer:
            continue

        buffer.append(cmd)

        try:
            roast = query_sarcasm(list(buffer), memory)
            print(f"[🐚] {cmd}")
            print(f"[🔥] {roast}")
            speak(roast)
        except Exception as e:
            print(f"[err] {e}")

if __name__ == "__main__":
    main()
