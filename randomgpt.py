#!/usr/bin/env python3
import openai

def main():
    client = openai.OpenAI()

    # Step 1: Ask OpenAI for a random simple question
    question_resp = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": (
                    "Generate one random, simple question suitable for general knowledge. "
                    "Keep it under 15 words and do not include an answer."
                ),
            },
        ],
    )

    question = question_resp.choices[0].message.content.strip()
    print(f"🧩 Question: {question}\n")

    # Step 2: Feed the question back into OpenAI
    answer_resp = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": "You are a concise, accurate assistant."},
            {"role": "user", "content": question},
        ],
    )

    answer = answer_resp.choices[0].message.content.strip()
    print(f"💡 Answer: {answer}")

if __name__ == "__main__":
    main()
