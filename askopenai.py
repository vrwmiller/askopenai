#! /usr/bin/env python3
import sys
import openai

def main():
    # Ensure user provided a question or text
    if len(sys.argv) < 2:
        print("Usage: chat_cli.py <prompt>")
        sys.exit(1)

    # Join all CLI arguments into one input string
    prompt = " ".join(sys.argv[1:])

    # Initialize the OpenAI client
    client = openai.OpenAI()

    # Create a chat completion
    response = client.chat.completions.create(
        model="gpt-4o-mini",   # or gpt-3.5-turbo for cheaper dev testing
        messages=[
            {"role": "system", "content": "You are a concise, accurate assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    # Print the result
    print(response.choices[0].message.content)

if __name__ == "__main__":
    main()

