#!/usr/bin/env python3
import argparse
import openai
import random

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
    args = parser.parse_args()

    client = OpenAI()
    model = args.model
    topic = args.topic

    print(f"🔍 Using model: {model}")
    print(f"🎯 Topic: {topic}")

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

    question_resp = client.chat.completions.create(**kwargs)
    question = question_resp.choices[0].message.content.strip()

    print("🤔 Question:", question)

    answer_resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Answer clearly and concisely."},
            {"role": "user", "content": question},
        ],
    )

    answer = answer_resp.choices[0].message.content.strip()
    print("\n💡 Answer:", answer)


if __name__ == "__main__":
    main()
