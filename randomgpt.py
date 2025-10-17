#!/usr/bin/env python3
import argparse
import random
import time
from pathlib import Path
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
    parser.add_argument(
        "--n",
        type=int,
        default=None,
        help="When sampling without temperature, request this many completions and pick one (optional)."
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="Override model temperature (if supported by model)."
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
    user_n = args.n
    user_temperature = args.temperature

    print(f"Using model: {model}")
    print(f"Topic: {topic}")

    # Create an entropy seed to add randomness even if temperature is fixed
    entropy = random.randint(1000, 9999)
    # Choose randomized prompt/system variants to increase diversity when model sampling is limited
    system_variants = [
        "You are a curious and creative assistant.",
        "You are a concise, curious assistant who asks intriguing questions.",
        "You are a playful and imaginative assistant. Ask a short, surprising question.",
        "You are a practical, informative assistant. Ask a clear, thought-provoking question.",
    ]
    user_prompt_templates = [
        f"(Seed {entropy}) Generate one random, interesting, but simple question related to {topic}. Keep it short and clear.",
        f"(Seed {entropy}) Provide a single short question about {topic} that would spark curiosity.",
        f"(Seed {entropy}) Ask a concise, unexpected question related to {topic}—one sentence only.",
        f"(Seed {entropy}) Produce one short, engaging question about {topic} suitable for a quick conversation starter.",
    ]
    system_msg = random.choice(system_variants)
    question_prompt = random.choice(user_prompt_templates)

    # Detect models that may not support temperature
    supports_temperature = not model.startswith(("gpt-4.1", "gpt-5"))
    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": question_prompt},
        ],
    }

    # set temperature: user override when provided, otherwise use a higher default for sampling models
    if supports_temperature:
        if user_temperature is not None:
            kwargs["temperature"] = user_temperature
        else:
            kwargs["temperature"] = 1.5

    # use the correct parameter name depending on model family
    token_param = "max_completion_tokens" if model.startswith(("gpt-4", "gpt-4.1", "gpt-5")) else "max_tokens"
    kwargs[token_param] = max_tokens if max_tokens is not None else question_default_max

    # If temperature isn't available for this model, ask the model to return multiple distinct questions in one message
    multi_q_count = user_n if user_n is not None else 8 if not supports_temperature else 1
    if not supports_temperature:
        # replace the user message with an instruction to emit multiple distinct short questions
        kwargs["messages"][1]["content"] = (
            question_prompt + f"\n\nPlease output {multi_q_count} distinct, one-sentence questions about {topic}. "
            "Return each question on its own line, with no extra commentary."
        )
        # increase token budget for multi-question output
        kwargs[token_param] = max(kwargs[token_param], question_default_max * 4)
    start_q = time.perf_counter()
    question_resp = client.chat.completions.create(**kwargs)
    dur_q = time.perf_counter() - start_q
    # If we asked for a multi-question single-message response, parse lines and pick one
    if not supports_temperature:
        body = question_resp.choices[0].message.content
        # split into lines and extract non-empty lines that look like questions
        lines = [l.strip() for l in body.splitlines() if l.strip()]
        # remove any numbering prefixes
        cleaned = []
        for l in lines:
            # remove leading numbering like '1.' or '1)'
            cl = l
            if cl and (cl[0].isdigit() or (len(cl) > 1 and cl[1].isdigit())):
                # drop leading indices and separators
                cl = cl.lstrip('0123456789. )-\t')
            cl = cl.strip()
            if cl:
                cleaned.append(cl)
        # deduplicate preserving order
        seen = set(); uniq = []
        for t in cleaned:
            if t not in seen:
                seen.add(t); uniq.append(t)
        if uniq:
            question = random.choice(uniq)
        else:
            question = cleaned[0] if cleaned else ""
    else:
        # pick a random, deduplicated choice if multiple were returned
        if hasattr(question_resp, 'choices') and len(question_resp.choices) > 1:
            seen = set(); uniq = []
            for c in question_resp.choices:
                text = c.message.content.strip()
                if text and text not in seen:
                    seen.add(text); uniq.append(text)
            question = random.choice(uniq) if uniq else question_resp.choices[0].message.content.strip()
        else:
            question = question_resp.choices[0].message.content.strip()

    def looks_canned(s: str) -> bool:
        if not s:
            return True
        t = s.lower()
        canned_phrases = ["how can i help you", "how may i help", "how can i assist", "what can i do for you"]
        return any(p in t for p in canned_phrases)

    # If the model returned an empty or generic canned response, retry with a stricter prompt.
    if looks_canned(question):
        if debug:
            print("[debug] detected empty/canned question response, retrying generation with stricter prompt")
        retry_system_variants = [
            "You are a curious and creative assistant. Respond with a single short question only.",
            "You are concise and imaginative. Provide one short question only.",
            "You are a playful assistant. Ask a single surprising question.",
        ]
        retry_user_templates = [
            question_prompt + "\n\nRespond only with one concise question, no explanations.",
            question_prompt + "\n\nGive only a single short question, one sentence.",
            question_prompt + "\n\nOutput just one question that would spark curiosity.",
        ]
        retry_kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": random.choice(retry_system_variants)},
                {"role": "user", "content": random.choice(retry_user_templates)},
            ],
        }
        # increase token budget for retry
        retry_token = "max_completion_tokens" if model.startswith(("gpt-4", "gpt-4.1", "gpt-5")) else "max_tokens"
        retry_kwargs[retry_token] = max(question_default_max, 128)
        # allow higher randomness if the model supports it
        if supports_temperature:
            retry_kwargs["temperature"] = 1.5

        # if temperature wasn't available for the model, request multiple retries to increase variety
        if not supports_temperature:
            retry_kwargs["n"] = 5
        start_q2 = time.perf_counter()
        retry_resp = client.chat.completions.create(**retry_kwargs)
        dur_q += time.perf_counter() - start_q2
        if hasattr(retry_resp, 'choices') and len(retry_resp.choices) > 1:
            seen = set()
            uniq = []
            for c in retry_resp.choices:
                text = c.message.content.strip()
                if text and text not in seen:
                    seen.add(text)
                    uniq.append(text)
            retry_question = random.choice(uniq) if uniq else retry_resp.choices[0].message.content.strip()
        else:
            retry_question = retry_resp.choices[0].message.content.strip()
        if retry_question:
            question = retry_question
        else:
            # final fallback: choose a randomized templated question so the output isn't identical each run
            templates = [
                f"What's one interesting thing about {topic}?",
                f"What's a surprising fact about {topic}?",
                f"Can you name a practical use or feature of {topic}?",
                f"What's a simple, interesting question someone could ask about {topic}?",
            ]
            question = random.choice(templates)

    print("Question:", question)
    if debug:
        try:
            print(f"[debug] question API call duration: {dur_q:.3f} seconds")
        except NameError:
            pass

    # prefer answers that avoid repeating generic definitions; nudge the model away from dictionary-like output
    answer_system = "Answer clearly and concisely. Avoid generic dictionary-style definitions; prefer a specific fact, example, or practical detail."
    answer_kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": answer_system},
            {"role": "user", "content": question},
        ],
    }
    # for the answer, prefer the user-specified value if given; otherwise use the answer default
    answer_token_param = "max_completion_tokens" if model.startswith(("gpt-4", "gpt-4.1", "gpt-5")) else "max_tokens"
    answer_kwargs[answer_token_param] = max_tokens if max_tokens is not None else answer_default_max

    start_a = time.perf_counter()
    answer_resp = client.chat.completions.create(**answer_kwargs)
    dur_a = time.perf_counter() - start_a

    answer = answer_resp.choices[0].message.content.strip()
    # --- persistent history to avoid repeats across runs ---
    HISTORY_FILE = Path.home() / ".randomgpt_history"

    def load_history(max_items=50):
        try:
            if HISTORY_FILE.exists():
                lines = [l.strip() for l in HISTORY_FILE.read_text(encoding='utf-8').splitlines() if l.strip()]
                return lines[-max_items:]
        except Exception:
            pass
        return []

    def append_history(s: str, max_items=50):
        try:
            h = load_history(max_items-1)
            h.append(s)
            HISTORY_FILE.write_text("\n".join(h[-max_items:]) + "\n", encoding='utf-8')
        except Exception:
            pass

    recent_answers = load_history(50)
    def answer_looks_empty_or_canned(s: str) -> bool:
        if not s:
            return True
        t = s.lower()
        canned = ["how can i help you", "how may i help", "i'm here to help", "how can i assist"]
        return any(p in t for p in canned)

    # If answer is empty, generic, or repeats recent answers, retry with a stronger answer prompt
    if answer_looks_empty_or_canned(answer) or (answer in recent_answers):
        if debug:
            print("[debug] detected empty/canned or repeated answer, retrying answer generation and avoiding recent answers")
        retry_answer_kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a concise expert. Answer the user's question directly with 2-3 informative sentences and avoid repeating common, dictionary-style descriptions."},
                {"role": "user", "content": question},
            ],
        }
        # use same token param decision as before
        retry_token = "max_completion_tokens" if model.startswith(("gpt-4", "gpt-4.1", "gpt-5")) else "max_tokens"
        retry_answer_kwargs[retry_token] = max(answer_default_max, 512)
        if supports_temperature:
            retry_answer_kwargs["temperature"] = 0.8

        start_a2 = time.perf_counter()
        retry_answer_resp = client.chat.completions.create(**retry_answer_kwargs)
        dur_a += time.perf_counter() - start_a2
        retry_answer = retry_answer_resp.choices[0].message.content.strip()
        if retry_answer:
            answer = retry_answer
        else:
            # final local fallback: short summary template
            answer = f"FreeBSD is a free and open-source Unix-like operating system descended from BSD, known for its performance, advanced networking, and conservative, stable release process."

    # If answer still repeats recent history, ask the model to explicitly avoid the previous answers
    if answer in recent_answers:
        if debug:
            print("[debug] answer matches recent history, asking model to avoid previous answers")
        avoid_snippet = "\n".join(f"- {a}" for a in recent_answers[-5:])
        avoid_kwargs = retry_answer_kwargs.copy() if 'retry_answer_kwargs' in locals() else {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a concise expert. Answer directly with 2-3 informative sentences."},
                {"role": "user", "content": question},
            ],
        }
        # append an explicit instruction to avoid exact text in recent history
        avoid_kwargs["messages"].append({"role": "user", "content": f"Do not repeat these previous answers; provide a different specific fact or example:\n{avoid_snippet}"})
        if supports_temperature:
            avoid_kwargs["temperature"] = 0.8
        start_a3 = time.perf_counter()
        avoid_resp = client.chat.completions.create(**avoid_kwargs)
        dur_a += time.perf_counter() - start_a3
        new_answer = avoid_resp.choices[0].message.content.strip()
        if new_answer and new_answer not in recent_answers:
            answer = new_answer

    # append final answer to history to reduce repeats across runs
    try:
        append_history(answer, max_items=200)
    except Exception:
        pass

    print("\nAnswer:", answer)
    if debug:
        try:
            print(f"[debug] answer API call duration: {dur_a:.3f} seconds")
        except NameError:
            pass


if __name__ == "__main__":
    main()
