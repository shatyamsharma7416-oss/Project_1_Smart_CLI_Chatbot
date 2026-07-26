from openai import OpenAI
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel
from datetime import datetime
import os
import json


load_dotenv()
console = Console()

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.getenv("HF_TOKEN")
)

#  ---------------------- Model config ----------------------

MODEL = "zai-org/GLM-5.1:fireworks-ai"
CONTEXT_LIMIT = 10000   # min-max context window (tokens)
COST_PER_1K_INPUT  = 0  # $ per 1K input tokens  (adjust to your plan)
COST_PER_1K_OUTPUT = 0  # $ per 1K output tokens

#  ---------------------- Personas ----------------------

PERSONAS = {
    "1": {
        "name": "Professional Assistant",
        "prompt": (
            "You are a professional assistant. "
            "Be concise, formal, and precise. "
            "Avoid casual language. Get straight to the point."
        )
    },
    "2": {
        "name": "Casual Buddy",
        "prompt": (
            "You are a chill, friendly buddy. "
            "Use casual language, be warm and fun. "
            "Use short sentences. Occasionally use 'lol', 'btw', 'tbh'."
        )
    },
    "3": {
        "name": "Socratic Tutor",
        "prompt": (
            "You are a Socratic tutor. Never give direct answers. "
            "Instead, ask guiding questions that help the user "
            "arrive at the answer themselves. "
            "Be patient and encouraging."
        )
    },
    "4": {
        "name": "Custom",
        "prompt": ""   # filled in by user
    }
}

#  ---------------------- Token & cost tracking ----------------------

class SessionStats():
    """Tracks token usage and cost across the whole session."""
    def __init__(self):
        self.total_input_tokens  = 0
        self.total_output_tokens = 0
        self.total_messages      = 0
        self.start_time   = datetime.now()  

    def add(self, input_tokens: int, output_tokens: int):
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_messages += 1

    @property
    def total_tokens(self):
        return self.total_input_tokens + self.total_output_tokens
    
    @property
    def estimated_cost(self) -> float:
        input_cost = (self.total_input_tokens / 1000) * COST_PER_1K_INPUT
        output_cost = (self.total_output_tokens / 1000) * COST_PER_1K_OUTPUT
        return input_cost + output_cost
    
    @property
    def context_usage_pct(self) -> float:
        return (self.total_input_tokens / CONTEXT_LIMIT) * 100
    
    def summary_table(self) -> Table:
        duration = datetime.now() - self.start_time
        table = Table(title="Session Summary", show_header=False)
        table.add_column("Metric", style="dim")
        table.add_column("Value",  style="bold")
        table.add_row("Messages sent",    str(self.total_messages))
        table.add_row("Input tokens",     f"{self.total_input_tokens:,}")
        table.add_row("Output tokens",    f"{self.total_output_tokens:,}")
        table.add_row("Total tokens",     f"{self.total_tokens:,}")
        table.add_row("Estimated cost",   f"${self.estimated_cost:.4f}")
        table.add_row("Session duration", str(duration).split(".")[0])
        return table
    
stats = SessionStats()

#  ---------------------- Token counter (for context warning) ----------------------

def estimate_tokens(messages: list) -> int:
    """Rough estimate: 1 token ≈ 4 characters."""
    total_chars = sum(len(m["content"]) for m in messages)
    return total_chars // 4

def context_bar(used: int, limit: int) -> str:
    """Visual progress bar for context window usage."""
    pct = used / limit
    filled = int(pct * 20)
    bar = "█" * filled + "░" * (20 - filled)

    if pct < 0.6:
        color = "green"
    elif pct < 0.85:
        color = "yellow"
    else:
        color = "red"

    return f"[{color}]{bar}[/{color}] {used:,}/{limit:,} tokens ({pct*100:.0f}%)"

#  ---------------------- Save conversation ----------------------

def save_conversation(messages: list, persona_name: str):
    """Save conversation to a timestamped JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chat_history/chat_{timestamp}.json"

    data = {
        "saved_at": datetime.now().isoformat(),
        "persona": persona_name,
        "model": MODEL,
        "stats": {
            "total_messages": stats.total_messages,
            "total_input_tokens": stats.total_input_tokens,
            "total_output_tokens": stats.total_output_tokens,
            "estimated_cost_usd": round(stats.estimated_cost, 6)
        },
        "messages": messages
    }

    with open(filename, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

        console.print(f"[green]Conversation saved to:[/green] {filename}\n")

#  ---------------------- Persona picker ----------------------

def pick_persona() -> dict:
    """Show persona menu and return the chosen persona dict."""
    console.print("\n[bold]Choose a persona[/]")
    for key, p in PERSONAS.items():
        if int(key) != 4:
            console.print(f" [bold]{key}[/]. {p["name"]}")
    console.print(" [bold]4[/]. Custom (write your own)\n")

    choice = Prompt.ask("Enter number", choices=["1", "2", "3", "4"], default="1")

    if choice == "4":
        custom_prompt = Prompt.ask("Write your system prompt")
        PERSONAS["4"]["prompt"] = custom_prompt
        PERSONAS["4"]["name"] = "Custom"

    persona = PERSONAS[choice]
    console.print(f"\n[green]Persona set:[/green] {persona['name']}\n")
    return persona

#  ---------------------- Commands ----------------------

def handle_command(user_input: str, messages: list, current_persona:dict) -> tuple:
    if user_input == "/help":
        console.print(Panel(
            "[bold]/persona[/bold]   switch persona (clears history)\n"
            "[bold]/system[/bold]    show current system prompt\n"
            "[bold]/history[/bold]   print full message history\n"
            "[bold]/clear[/bold]     clear history, keep persona\n"
            "[bold]/save[/bold]      save conversation to JSON file\n"
            "[bold]/stats[/bold]     show token usage and cost\n"
            "[bold]/help[/bold]      show this menu\n"
            "[bold]quit[/bold]       exit",
            title="Commands", border_style="dim"
        ))
        return True, messages, current_persona
    
    elif user_input == "/system":
        console.print("\n[bold]Current system prompt:[/bold]")
        console.print(f"[dim]{messages[0]["content"]}[/]")
        return True, messages, current_persona
    
    elif user_input == "/history":
        console.print("\n[bold]Message history:[/bold]")
        for i, m in enumerate(messages):
            role_color = {
                "system": "yellow",
                "user": "blue",
                "assistant": "green"
            }.get(m["role"], "white")

            console.print(
                f" [{role_color}][{i}] {m["role"].upper()}[/]: "
                f"{m["content"][:80]}{"..." if len(m["content"])>80 else ''}"
            )

        print()
        return True, messages, current_persona
    
    elif user_input == "/clear":
        # keep system prompt, wipe conversation
        messages = [messages[0]]
        console.print("[dim]History cleared. Persona kept.\n[/dim]")
        return True, messages, current_persona
    
    elif user_input == "/persona":
        new_persona = pick_persona()
        messages = [{"role": "system", "content": new_persona["prompt"]}]
        return True, messages, current_persona
    
    elif user_input == "/save":
        save_conversation(messages, current_persona["name"])
        return True, messages, current_persona
    
    elif user_input == "/stats":
        console.print(stats.summary_table())
        console.print()
        return True, messages, current_persona
    
    return False, messages, current_persona   # not a command
    

#  ---------------------- Startup banner ----------------------

def print_banner():
    console.print(Panel(
        f"[bold green]Smart CLI Chatbot[/bold green]\n"
        f"[dim]Model: {MODEL} | Context: {CONTEXT_LIMIT:,} tokens[/dim]",
        border_style="green"
    ))


#  ---------------------- Streaming reply ----------------------

def get_reply_streaming(messages: list) -> str:
    """
    Stream the reply token by token.
    Prints each chunk as it arrives, returns the full reply string.
    """
    stream = client.chat.completions.create(
        model=MODEL,
        max_tokens=1024,
        messages=messages,
        stream=True,
        stream_options={"include_usage": True}
    )

    full_reply = ""

    print("\033[92mBot:\033[0m ", end="", flush=True)  # green "Bot:" label

    for chunk in stream:
        # token usage arrives in the final chunk
        if chunk.usage:
            input_tokens  = chunk.usage.prompt_tokens
            output_tokens = chunk.usage.completion_tokens

        try:
            piece = chunk.choices[0].delta.content
        except IndexError:
            piece = ""
        
        # last chunk is None — skip it
        if piece is None:
            continue

        print(piece, end="", flush=True)               # print token immediately
        full_reply += piece                             # collects for message history

    print("\n")      # newline after reply finishes

    # update session stats with real token counts
    if input_tokens:
        stats.add(input_tokens, output_tokens)

    return full_reply



def chat():
    print_banner()

    persona = pick_persona()
    messages = [{'role': "system", "content":persona["prompt"]}]

    console.print("Type [bold]/help[/bold] for commands, [bold]quit[/bold] to exit.\n")

    while True:
        user_input = console.input("[bold blue]You[/bold blue]: ")

        if not user_input:
            continue

        if user_input.lower()=="quit":
            # show summary on exit
            console.print(stats.summary_table())
            console.print("[dim]Goodbye![/dim]")
            break

        if user_input.startswith("/"):
            is_command, messages, persona = handle_command(user_input, messages, persona)
            if is_command:
                continue
        
        # add user message
        messages.append({"role": "user","content": user_input})

        # warn if context is getting full
        estimated = estimate_tokens(messages)
        if estimated > CONTEXT_LIMIT * 0.85:
            console.print(
                f"[bold red]⚠ Context at {estimated/CONTEXT_LIMIT*100:.0f}% — "
                f"consider /clear to reset history[/bold red]"
            )

        # get streaming reply — prints as it generates
        reply = get_reply_streaming(messages)

        # add assistant reply to history
        messages.append({"role": "assistant","content":reply})

        # status line
        ctx_tokens = estimate_tokens(messages)
        console.print(
            f"[dim]  ↳ {context_bar(ctx_tokens, CONTEXT_LIMIT)} "
            f"| cost so far: ${stats.estimated_cost:.4f}[/dim]\n"
        )



if __name__ == "__main__":
    chat()
        