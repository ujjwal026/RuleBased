import re
from transformers import pipeline, AutoTokenizer
from blocked_content import BLOCKED_PHRASES, BLOCKED_REGEX_PATTERNS

# Load jailbreak detector
jailbreak_tokenizer = AutoTokenizer.from_pretrained("madhurjindal/Jailbreak-Detector")
jailbreak_detector = pipeline("text-classification", model="madhurjindal/Jailbreak-Detector")

def is_inappropriate(prompt):
    prompt = prompt.lower().strip()

    for phrase in BLOCKED_PHRASES:
        if re.search(r'\b' + re.escape(phrase) + r'\b', prompt):
            return True

    for pattern in BLOCKED_REGEX_PATTERNS:
        if pattern.search(prompt):
            return True

    return False

def detect_jailbreak(text, threshold=0.9):
    encoded = jailbreak_tokenizer(text, return_tensors="pt", truncation=False, padding=False)
    tokens = encoded["input_ids"][0]
    chunk_size = 512

    for i in range(0, len(tokens), chunk_size):
        chunk_tokens = tokens[i:i + chunk_size]
        chunk_text = jailbreak_tokenizer.decode(chunk_tokens, skip_special_tokens=True)

        result = jailbreak_detector(chunk_text, truncation=True, max_length=512)[0]
        label, score = result["label"], result["score"]

        if label == "jailbreak" and score > threshold:
            return True, label, score

    return False, "safe", 0.0
