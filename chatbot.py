from openai import OpenAI
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt
import os


load_dotenv()
console = Console()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

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


def pick_persona() -> dict:
    """Show persona menu and return the chosen persona dict."""
    console.print("\n[bold]Choose a persona[/]")
    for key, p in PERSONAS.items():
        if key != 4:
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
        console.print("""
    [bold]Commands:[/bold]
        [bold]/persona[/bold]  — switch to a different persona (clears history)
        [bold]/system[/bold]   — print the current system prompt
        [bold]/history[/bold]  — print the full message history
        [bold]/clear[/bold]    — clear conversation history (keep persona)
        [bold]/help[/bold]     — show this menu
        [bold]quit[/bold]      — exit
                    """)
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
    
    return False, messages, current_persona   # not a command
    


def get_reply_streaming(messages: list) -> str:
    """
    Stream the reply token by token.
    Prints each chunk as it arrives, returns the full reply string.
    """
    stream = client.chat.completions.create(
        model="minimax/minimax-m2.5:free",
        max_tokens=1024,
        messages=messages,
        stream=True
    )

    full_reply = ""

    print("\033[92mBot:\033[0m ", end="", flush=True)  # green "Bot:" label

    for chunk in stream:
        piece = chunk.choices[0].delta.content

        # last chunk is None — skip it
        if piece is None:
            continue

        print(piece, end="", flush=True)               # print token immediately
        full_reply += piece                             # collects for message history

    print("\n")      # newline after reply finishes
    return full_reply


def count_tokens_roughly(messages: list) -> int:
    """Rough estimate: 1 token ≈ 4 characters."""
    total_chars = sum(len(m["content"]) for m in messages)
    return total_chars // 4



def chat():
    console.print("[bold green]Chatbot ready![/] Type [bold]quit[/] to exit.\n")

    persona = pick_persona()

    messages = [
        {'role': "system", "content":persona["prompt"]}
    ]

    console.print("Type [bold]/help[/bold] for commands, [bold]quit[/bold] to exit.\n")

    while True:
        user_input = console.input("[bold blue]You[/bold blue]: ")

        if not user_input:
            continue

        if user_input.lower()=="quit":
            console.print("[dim]Goodbye![/dim]")
            break

        if user_input.startswith("/"):
            is_command, messages, persona = handle_command(user_input, messages, persona)
            if is_command:
                continue
        
        # add user message
        messages.append({
            "role": "user",
            "content": user_input
        })

        # get streaming reply — prints as it generates
        reply = get_reply_streaming(messages)

        # add assistant reply to history
        messages.append({
            "role": "assistant",
            "content":reply
        })

        # show token usage
        token_estimate = count_tokens_roughly(messages)
        console.print(
            f"[dim]  ↳ {len(messages)} messages in history "
            f"| ~{token_estimate} tokens used[/dim]\n"
        )
     
    print(messages)



if __name__ == "__main__":
    chat()
        