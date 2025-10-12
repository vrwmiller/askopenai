#!/usr/bin/env python3
import openai
import random
import time

def main():
    client = openai.OpenAI()

    # Create some entropy: random seed words
    random_topics = [
        "science", "history", "art", "technology", "music",
        "nature", "space", "mythology", "sports", "literature",
        "geography", "food", "philosophy", "operating systems",
        "programming", "FreeBSD", "Linux"
    ]
    topic = random.choice(random_topics)

    # Step 1: Ask OpenAI for a random, simple question with extra variety
    question_prompt = (
        f"Generate one truly random, interesting, but simple question related to {topic}. "
        "Avoid repeating common trivia. The question should be concise (under 15 words) "
        "and not include an answer. Use your creativity to vary style and topic phrasing each time."
    )

    question_resp = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": "You are a curious and creative assistant."},
            {"role": "user", "content": question_prompt},
        ],
    )

    question = question_resp.choices[0].message.content.strip()
    print(f"\n🎲 Topic hint: {topic}")
    print(f"🧩 Question: {question}")

    # Step 2: Feed the question back into OpenAI
    answer_resp = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": "You are a concise and accurate assistant."},
            {"role": "user", "content": question},
        ],
    )

    answer = answer_resp.choices[0].message.content.strip()
    print(f"💡 Answer: {answer}\n")

if __name__ == "__main__":
    main()
