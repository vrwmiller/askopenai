#!/usr/bin/env python3
"""
askgpt.py

Combines functionality of askopenai.py (prompt -> assistant) and randomgpt.py (--random mode).

Usage:
  ./askgpt.py [--model MODEL] [--max-tokens N] [--debug] <prompt>
  ./askgpt.py --random [--model MODEL] [--topic TOPIC] [--max-tokens N] [--debug]

"""
import argparse
import os
import random
import time
from openai import OpenAI


def choose_token_param(model_name: str) -> str:
    return "max_completion_tokens" if model_name.startswith(("gpt-4", "gpt-4.1", "gpt-5")) else "max_tokens"


def run_prompt_mode(client, model, prompt_text, max_tokens, debug):
    token_param = choose_token_param(model)
    call_kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a concise, accurate assistant."},
            {"role": "user", "content": prompt_text},
        ],
    }
    call_kwargs[token_param] = max_tokens if max_tokens is not None else 256

    start = time.perf_counter()
    resp = client.chat.completions.create(**call_kwargs)
    dur = time.perf_counter() - start

    output = resp.choices[0].message.content
    print(output)
    if debug:
        print(f"[debug] API call duration: {dur:.3f} seconds")


def run_random_mode(client, model, topic, max_tokens, debug):
    # adopt the more feature-rich randomgpt behavior but simplified and merged here
    question_default_max = 64
    answer_default_max = 256

    print(f"Using model: {model}")
    print(f"Topic: {topic}")

    # entropy seed and prompt
    entropy = random.randint(1000, 9999)
    question_prompt = f"(Seed {entropy}) Generate one short, interesting question related to {topic}. Keep it concise."

    supports_temperature = not model.startswith(("gpt-4.1", "gpt-5"))
    token_param = choose_token_param(model)

    q_kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a curious and creative assistant."},
            {"role": "user", "content": question_prompt},
        ],
    }
    if supports_temperature:
        q_kwargs["temperature"] = 1.5
    q_kwargs[token_param] = max_tokens if max_tokens is not None else question_default_max

    start_q = time.perf_counter()
    q_resp = client.chat.completions.create(**q_kwargs)
    dur_q = time.perf_counter() - start_q
    question = q_resp.choices[0].message.content.strip()

    print("Question:", question)
    if debug:
        print(f"[debug] question API call duration: {dur_q:.3f} seconds")

    a_kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Answer clearly and concisely."},
            {"role": "user", "content": question},
        ],
    }
    a_kwargs[token_param] = max_tokens if max_tokens is not None else answer_default_max

    start_a = time.perf_counter()
    a_resp = client.chat.completions.create(**a_kwargs)
    dur_a = time.perf_counter() - start_a
    answer = a_resp.choices[0].message.content.strip()

    print("\nAnswer:", answer)
    if debug:
        print(f"[debug] answer API call duration: {dur_a:.3f} seconds")


def main():
    parser = argparse.ArgumentParser(prog="askgpt")
    parser.add_argument("--model", "-m", default="gpt-5", help="Model to use")
    parser.add_argument("--max-tokens", type=int, default=None, help="Maximum tokens for completions")
    parser.add_argument("--debug", action="store_true", help="Show debug info")
    parser.add_argument("--random", action="store_true", help="Run random question/answer flow (randomgpt)")
    parser.add_argument("--topic", "-t", default="anything at all", help="Topic for random mode")
    parser.add_argument("prompt", nargs="*", help="Prompt for normal mode")

    args = parser.parse_args()

    # Initialize client
    client = OpenAI()

    if args.random:
        run_random_mode(client, args.model, args.topic, args.max_tokens, args.debug)
    else:
        if not args.prompt:
            print("Error: prompt required when not using --random")
            parser.print_help()
            return
        prompt_text = " ".join(args.prompt)
        run_prompt_mode(client, args.model, prompt_text, args.max_tokens, args.debug)


if __name__ == "__main__":
    main()
