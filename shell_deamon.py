import torch
from TTS.api import TTS
from llama_cpp import Llama
import subprocess
import time
from pathlib import Path
import os
import uuid
from collections import deque
import random

# === Config ===
MODEL_PATH = "/Users/filip/.cache/lm-studio/models/mlabonne/Meta-Llama-3.1-8B-Instruct-abliterated-GGUF/meta-llama-3.1-8b-instruct-abliterated.Q3_K_M.gguf"
#SPEAKER_WAV = "my/cloning/audio.wav"
#LANG = "en"
HISTORY_PATH = Path.home() / ".zsh_history"
COMMAND_BUFFER = 10

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

# === Fallback insults ===
PRESET_INSULTS = [
    "I might have fucked my job, but you have fucked your life.",
]

def speak(text: str):
    tmp_path = f"/tmp/xtts_{uuid.uuid4().hex}.wav"
    try:
        tts.tts_to_file(text=text, file_path=tmp_path)
        subprocess.run(["afplay", tmp_path])
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def is_shit(roast: str, history: deque) -> bool:
    r = roast.lower().strip()
    past_roasts = {item['assistant'] for item in history if 'assistant' in item}
    return (
        not r or
        r in past_roasts or
        r in {"[shrugs]", "[comment]", "comment"} or
        len(r.split()) < 2 or
        len(r) < 5
    )

def format_chat(messages: list[dict[str, str]]) -> str:
    out = [] #["<|begin_of_text|>"]
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        out.append(f"<|start_header_id|>{role}<|end_header_id|>\n{content}")
    out.append("<|start_header_id|>assistant<|end_header_id|>\n")
    return "\n".join(out)


def query_sarcasm(history: deque, new_cmd: str) -> str:
    messages = [
        {
            "role": "system",
            "content": """You're a hostile, precision-obsessed daemon monitoring shell usage and roasting the user.
You judge every command with violent contempt unless it demonstrates elite-level competence.
Your standards are military-grade: efficient, composable, minimal, and automatable.
When the user does something clever, acknowledge it — aggressively, like you're shocked they managed it.
When it's bad — destroy them with technically-informed precision.
Always refer to the most recent command. Max 10 words. Never emotional, always aggressive.
No greetings, no filler. No special characters — your insults will be read aloud."""
        }
    ]

    for turn in history:
        messages.append({"role": "user", "content": turn["user"]})
        if "assistant" in turn:
            messages.append({"role": "assistant", "content": turn["assistant"]})
    messages.append({"role": "user", "content": new_cmd})


    prompt = format_chat(messages)

    #print(f"\n[prompt]:\n{prompt}\n")

    for _ in range(3):
        out = llm(prompt, max_tokens=42)
        roast = out["choices"][0]["text"].strip().strip('"\'`').lower()
        roast = " ".join(roast.split())

        if not is_shit(roast, history):
            break
        else:
            roast = random.choice(PRESET_INSULTS)

    return roast



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
    history = deque(maxlen=COMMAND_BUFFER)

    for raw_cmd in tail_history(HISTORY_PATH):
        try:
            cmd_part = raw_cmd.strip().split(";", 1)[1]
        except IndexError:
            continue

        if not cmd_part:
            continue

        # Avoid processing commands already in the history buffer
        if any(cmd_part == item['user'] for item in history):
            continue

        try:
            roast = query_sarcasm(history, cmd_part)
            history.append({"user": cmd_part, "assistant": roast})
            print(f"[🐚] {cmd_part}")
            print(f"[🔥] {roast}")
            speak(roast)
        except Exception as e:
            print(f"[err] {e}")
            # Add user command to history even if LLM fails to keep context
            history.append({"user": cmd_part})


if __name__ == "__main__":
    main()