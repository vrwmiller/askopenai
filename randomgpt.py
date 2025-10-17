#!/usr/bin/env python3
import argparse
import random
import time
from openai import OpenAI

def main():
    parser = argparse.ArgumentParser(
        description="Generate a random question and answer using OpenAI's API."
    )
    parser.add_argument(
        "--model", "-m",
        default="gpt-5",
        help="Model to use (default: gpt-5)"
    )
    parser.add_argument(
        "--topic", "-t",
        default="anything at all",
        help="Topic to guide question generation (default: anything at all)"
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
    args = parser.parse_args()

    client = OpenAI()
    model = args.model
    topic = args.topic
    max_tokens = args.max_tokens
    # default token budgets
    question_default_max = 64
    answer_default_max = 256
    debug = args.debug

    print(f"Using model: {model}")
    print(f"Topic: {topic}")

    # Create an entropy seed to add randomness even if temperature is fixed
    entropy = random.randint(1000, 9999)
    question_prompt = (
        f"(Seed {entropy}) Generate one random, interesting, but simple question "
        f"related to {topic}. Keep it short and clear."
    )

    # Detect models that may not support temperature
    supports_temperature = not model.startswith(("gpt-4.1", "gpt-5"))

    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a curious and creative assistant."},
            {"role": "user", "content": question_prompt},
        ],
    }

    if supports_temperature:
        kwargs["temperature"] = 1.5  # increase randomness if supported
    # only include max_tokens when provided by user
    # use user-specified max_tokens if provided, otherwise use question default
    kwargs["max_tokens"] = max_tokens if max_tokens is not None else question_default_max
    start_q = time.perf_counter()
    question_resp = client.chat.completions.create(**kwargs)
    dur_q = time.perf_counter() - start_q
    question = question_resp.choices[0].message.content.strip()

    print("Question:", question)
    if debug:
        try:
            print(f"[debug] question API call duration: {dur_q:.3f} seconds")
        except NameError:
            pass

    answer_kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Answer clearly and concisely."},
            {"role": "user", "content": question},
        ],
    }
    # for the answer, prefer the user-specified value if given; otherwise use the answer default
    answer_kwargs["max_tokens"] = max_tokens if max_tokens is not None else answer_default_max

    start_a = time.perf_counter()
    answer_resp = client.chat.completions.create(**answer_kwargs)
    dur_a = time.perf_counter() - start_a

    answer = answer_resp.choices[0].message.content.strip()
    print("\nAnswer:", answer)
    if debug:
        try:
            print(f"[debug] answer API call duration: {dur_a:.3f} seconds")
        except NameError:
            pass


if __name__ == "__main__":
    main()
