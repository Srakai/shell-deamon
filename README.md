# shell-deamon


> A hostile AI daemon that watches your terminal and roasts your every command in real time. Built for terminal masochists.


```bash
git clone https://github.com/Srakai/shell-daemon
cd shell-daemon
poetry install
vi shell_deamon.py # Edit cfg
poetry run python shell_deamon.py
```

Few Gigs of vram required.
Models are only suggestion, you can use any llama.cpp compatible model.

## What It Does
- Monitors your `~/.zsh_history`
- Judges your recent commands using a local LLM (via `llama.cpp`)
- Generates brutal roast or rare praise based on elite standards
- Speaks the insult aloud via Glow-TTS


## What It Can't Do
- Use ActivityWatch to track all your moves
- Process screenshots
- Understeand your life context for precision roasting
- Provide constructive feedback
- Be nice or supportive in any way

## ⚠️ Warning
This project is abusive by design.
Do not run if you're emotional to feedback.
