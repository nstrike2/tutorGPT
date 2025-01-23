#!/usr/bin/env python3

import json
import re
import sys


def convert_to_chat_format(prompt: str, completion: str, system_prompt: str = None):
    """
    Converts a single prompt-completion pair (old style) into the new ChatCompletion format.
    - Strips trailing <END>.
    - Removes .txt\\n\\n###\\n\\n from the prompt.
    - Optionally includes a system-level role if system_prompt is given.
    """
    # 1. Remove known suffix from prompt
    #    The old code often used '.txt\\n\\n###\\n\\n'. Let's do a simple re.sub
    #    that removes "any filename .txt" plus newline + ### + newline
    #    If your suffix is exactly `.txt\n\n###\n\n`, you can do a simpler replace.
    cleaned_prompt = re.sub(r"\.txt\s*\n*\s*###\s*\n*\s*",
                            "", prompt, flags=re.IGNORECASE)

    # 2. Remove trailing "<END>" from completion
    cleaned_completion = completion
    if cleaned_completion.endswith("<END>"):
        cleaned_completion = cleaned_completion[:-5].rstrip()

    # Build the chat messages array
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    # user prompt
    messages.append({"role": "user", "content": cleaned_prompt.strip()})
    # assistant output
    messages.append(
        {"role": "assistant", "content": cleaned_completion.strip()})

    return {"messages": messages}


def main(input_path, output_path, system_prompt=None):
    """
    Reads the old prompt-completion JSONL from `input_path`,
    writes chat-formatted JSONL to `output_path`.
    Optionally pass a `system_prompt` to each example.
    """
    with open(input_path, "r", encoding="utf-8") as in_f, \
            open(output_path, "w", encoding="utf-8") as out_f:

        for line in in_f:
            line = line.strip()
            if not line:
                continue

            # each line has { "prompt": ..., "completion": ... }
            data = json.loads(line)
            old_prompt = data.get("prompt", "")
            old_completion = data.get("completion", "")

            new_obj = convert_to_chat_format(
                old_prompt, old_completion, system_prompt=system_prompt)
            out_f.write(json.dumps(new_obj, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    """
    Usage: python convert_to_chat.py old_dataset.jsonl new_dataset_chat.jsonl [system_prompt]

    Example:
      python convert_to_chat.py dataset_prepared.jsonl dataset_chat_prepared.jsonl "You are a helpful TA..."
    """
    if len(sys.argv) < 3:
        print(
            "Usage: python convert_to_chat.py <input.jsonl> <output.jsonl> [optional system prompt]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    if len(sys.argv) > 3:
        # Combine all extra args as system prompt, or just take sys.argv[3] if single string
        system_msg = " ".join(sys.argv[3:])
    else:
        system_msg = None

    main(input_file, output_file, system_msg)
