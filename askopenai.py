#!/usr/bin/env python3
import sys
import argparse
import openai
import os
import time

def fetch_available_models():
    """Fetches the list of available models from the OpenAI API."""
    try:
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        models = client.models.list()
        model_names = [model.id for model in models]
        return model_names
    except Exception as e:
        print(f"Error fetching models: {e}")
        return []

def usage(model_names):
    """Displays the usage instructions with available models."""
    print(f"""
Usage: askopenai.py [options] <prompt>

Options:
  --model MODEL_NAME   Specify which model to use (default: gpt-5)
  -h, --help           Show this help message and exit

Available models:
  {', '.join(model_names)}

Example:
  ./askopenai.py "Summarize the advantages of ZFS over ext4."
  ./askopenai.py "Explain recursion in Python" --model gpt-3.5-turbo
""")
    sys.exit(1)

def main():
    # Fetch available models
    model_names = fetch_available_models()

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("prompt", nargs="*", help="Prompt to send to the model")
    parser.add_argument(
        "--model",
        default="gpt-5",
        help="Which model to use (default: gpt-5)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=None,
        help="Maximum tokens to generate for completions (optional)."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show debug information such as API call timings."
    )
    parser.add_argument("-h", "--help", action="store_true", help="Show usage")

    args = parser.parse_args()

    if args.help or not args.prompt:
        usage(model_names)

    prompt_text = " ".join(args.prompt)
    model_name = args.model
    max_tokens = args.max_tokens
    # default token budget when user doesn't specify
    default_max_tokens = 256
    debug = args.debug

    # Initialize OpenAI client
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    # Send request
    call_kwargs = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a concise, accurate assistant."},
            {"role": "user", "content": prompt_text}
        ]
    }
    # include max_tokens: user value if provided, otherwise use default
    call_kwargs["max_tokens"] = max_tokens if max_tokens is not None else default_max_tokens

    start = time.perf_counter()
    response = client.chat.completions.create(**call_kwargs)
    duration = time.perf_counter() - start

    # Print output
    print(response.choices[0].message.content)
    if debug:
        print(f"[debug] API call duration: {duration:.3f} seconds")

if __name__ == "__main__":
    main()
