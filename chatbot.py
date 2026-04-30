from openai import OpenAI
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt
import os


load_dotenv()
console = Console()

SYSTEM_PROMPT = "You are a helpful assistant."

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)



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
    messages = [
        {'role': "system", "content":SYSTEM_PROMPT}
    ]

    console.print("[bold green]Chatbot ready![/] Type [bold]quit[/] to exit.\n")

    while True:
        user_input = console.input("[bold blue]You[/bold blue]: ")

        if not user_input:
            continue

        if user_input.lower()=="quit":
            console.print("[dim]Goodbye![/dim]")
            break
        
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
        