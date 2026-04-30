from openai import OpenAI
from dotenv import load_dotenv
from rich.console import Console
import os

load_dotenv()       # reads .env file into environment variables
console = Console()

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.getenv("OPENROUTER_API_KEY"),
)


def send_message(user_text: str) -> str:

    stream = client.chat.completions.create(
    model="minimax/minimax-m2.5:free",
    messages=[
            {
                "role": "user",
                "content": user_text
            }
            ],
    extra_body={"reasoning": {"enabled": True}},
    stream=True
    )

    # Extract the assistant message with reasoning_details
    for chunk in stream:
        print(chunk.choices[0].delta, end="", flush=True)



def main():
    # ---- Normal Response ----
    console.print("[bold]Step 1: First API call[/bold]\n")
    user_input = console.input("[green]What's your query:[/]\n")
    reply = send_message(user_input)

    # console.print(f"\n[green]Bot:[/] {reply}\n")

    # ---- Detailed Response ----
    # response = client.chat.completions.create(
    # model="minimax/minimax-m2.5:free",
    # messages=[
    #         {
    #             "role": "user",
    #             "content": console.input("[green]What's your query:[/]\n")
    #         }
    #         ],
    # extra_body={"reasoning": {"enabled": True}}
    # )


    # console.print(f"  id:               {response.id}")
    # console.print(f"  model:            {response.model}")
    # console.print(f"  reasoning:        {response.choices[0].message.reasoning}")
    # console.print(f"  input_tokens:     {response.usage.prompt_tokens}")
    # console.print(f"  output_tokens:    {response.usage.completion_tokens}")
    # console.print(f"  content text:     {response.choices[0].message.content}")




if __name__ == "__main__":
    main()
