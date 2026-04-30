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



def get_reply(messages: list) -> str:
    """Send the full converation history and get next reply."""
    response = client.chat.completions.create(
        model="minimax/minimax-m2.5:free",
        max_tokens=1024,
        messages=messages,
        stream=True
    )
    return response.choices[0].message.content


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

        messages.append({
            "role": "user",
            "content": user_input
        })

        reply = get_reply(messages)
        messages.append({
            "role": "assistant",
            "content":reply
        })

        console.print(f"[bold green]Bot:[/] {reply}")

        token_estimate = count_tokens_roughly(messages)
        console.print(
            f"[dim]  ↳ {len(messages)} messages in history "
            f"| ~{token_estimate} tokens used[/dim]\n"
        )
     
    print(messages)



if __name__ == "__main__":
    chat()
        




