# Smart CLI Chatbot

A terminal-based chatbot with switchable personas, live token/cost tracking, and streaming replies — built on the OpenRouter API.

## Features

- **Multiple personas** — Professional Assistant, Casual Buddy, Socratic Tutor, or write your own custom system prompt
- **Streaming responses** — replies print token-by-token as they're generated
- **Session stats** — live tracking of input/output tokens, estimated cost, and session duration
- **Context usage bar** — visual warning as you approach the model's context limit
- **Save conversations** — export any session to a timestamped JSON file
- **Slash commands** — switch personas, inspect history, clear context, and more without restarting

## Demo

```
┌──────────────────────────────────────────┐
│  Smart CLI Chatbot                        │
│  Model: minimax/minimax-m2.5:free | Context: 10,000 tokens │
└──────────────────────────────────────────┘

Choose a persona
1. Professional Assistant
2. Casual Buddy
3. Socratic Tutor
4. Custom (write your own)

Persona set: Socratic Tutor

You: Why does recursion need a base case?
Bot: Good question — let's work through it together. What happens
     if a recursive function keeps calling itself with no condition
     that stops it?
 ↳ ████░░░░░░░░░░░░░░░░ 612/10,000 tokens (6%) | cost so far: $0.0000
```

## Installation

```bash
git clone https://github.com/shatyamsharma7416-oss/Project_1_Smart_CLI_Chatbot.git
cd Project_1_Smart_CLI_Chatbot
pip install openai python-dotenv rich
```

## Setup

This project uses [OpenRouter](https://openrouter.ai) as the API provider. Create a `.env` file in the project root:

```
OPENROUTER_API_KEY=your_api_key_here
```

## Usage

```bash
python chatbot.py
```

You'll be prompted to pick a persona, then the chat begins.

## Commands

| Command | Description |
|---|---|
| `/persona` | Switch persona (clears history) |
| `/system` | Show the current system prompt |
| `/history` | Print full message history |
| `/clear` | Clear history, keep current persona |
| `/save` | Save the conversation to a timestamped JSON file |
| `/stats` | Show token usage and estimated cost |
| `/help` | Show the command menu |
| `quit` | Exit and print a final session summary |

## Configuration

Model and cost settings are set at the top of `chatbot.py`:

```python
MODEL = "minimax/minimax-m2.5:free"
CONTEXT_LIMIT = 10000
COST_PER_1K_INPUT = 0
COST_PER_1K_OUTPUT = 0
```

Swap `MODEL` for any OpenRouter-supported model, and update the cost constants to match your plan's pricing for accurate `/stats` output.

## Project structure

```
.
├── chatbot.py    # main application
├── .gitignore
└── .vscode/
```

## What I learned

- Implementing token-by-token streaming with the OpenAI-compatible client while still capturing final usage stats from the stream
- Building a lightweight context-window warning system using character-based token estimation
- Structuring a command-driven CLI loop (`/help`, `/persona`, `/save`, etc.) that stays readable as commands are added

## Roadmap

- [ ] Add `requirements.txt`
- [ ] Support multiple model providers beyond OpenRouter
- [ ] Replace character-based token estimation with a proper tokenizer

## License

Not yet specified.
