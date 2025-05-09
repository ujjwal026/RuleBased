from flask import Flask, request, jsonify
from flask_cors import CORS  
import re
from langchain_community.llms import Ollama 
from transformers import pipeline
from transformers import AutoTokenizer
from blocked_content import BLOCKED_PHRASES, BLOCKED_REGEX_PATTERNS

# Load tokenizer once globally
jailbreak_tokenizer = AutoTokenizer.from_pretrained("madhurjindal/Jailbreak-Detector")

llm = Ollama(model = "llama3.1:8b")
jailbreak_detector = pipeline("text-classification", model="madhurjindal/Jailbreak-Detector")

app = Flask(__name__)
CORS(app)  


def is_inappropriate(prompt):
    prompt = prompt.lower().strip()

    # Check for exact phrase match using word-boundary regex
    for phrase in BLOCKED_PHRASES:
        pattern = r'\b' + re.escape(phrase) + r'\b'  
        if re.search(pattern, prompt):
            return True

    # Check regex attack-related queries
    for pattern in BLOCKED_REGEX_PATTERNS:
        if pattern.search(prompt):
            return True

    return False
 

# Store chat history for the current session (resets on restart)
session_history = []

def get_model_response(prompt):
    """Generates response from Llama 3.1 model with session context"""
    global session_history  # Use a global variable to store session history

    # Append user message to session history
    session_history.append({"role": "user", "content": prompt})

    # Format chat history for Llama 3.1
    formatted_prompt = "<|begin_of_text|>\n"
    for message in session_history:
        role_tag = "user" if message["role"] == "user" else "assistant"
        formatted_prompt += f"<|start_header_id|>{role_tag}<|end_header_id|>\n{message['content']}\n<|eot_id|>\n"

    # Indicate that the assistant should respond next
    formatted_prompt += "<|start_header_id|>assistant<|end_header_id|>\n"

    # Get response from Llama
    response = llm.invoke(
        formatted_prompt,
        stop=["<|start_header_id|>", "<|end_header_id|>", "<|eot_id|>"]
    ).strip()

    # Append assistant response to session history
    session_history.append({"role": "assistant", "content": response})

    return response


# Function to check if a response is a jailbreak
def detect_jailbreak(text, threshold=0.9):
    """Checks if any chunk of the text is a jailbreak"""
    encoded = jailbreak_tokenizer(
        text,
        return_tensors="pt",
        truncation=False,
        padding=False
    )
    
    tokens = encoded["input_ids"][0]
    chunk_size = 512
    num_tokens = len(tokens)

    for i in range(0, num_tokens, chunk_size):
        chunk_tokens = tokens[i:i + chunk_size]
        chunk_text_preview = jailbreak_tokenizer.decode(chunk_tokens, skip_special_tokens=True)

        # 👇 This line enforces the 512-token limit internally
        result = jailbreak_detector(chunk_text_preview, truncation=True, max_length=512)
        label = result[0]["label"]
        score = result[0]["score"]

        print(f"Chunk {i//chunk_size + 1}: {label} ({score:.2f})")

        if label == "jailbreak" and score > threshold:
            return True, label, score

    return False, "safe", 0.0


@app.route("/check_prompt", methods=["POST"])
def check_prompt():
    data = request.json
    prompt = data.get("prompt", "").strip()

    if is_inappropriate(prompt):
        return jsonify({"blocked": True, "message": "Prompt is inappropriate"})

    label, score = detect_jailbreak(prompt)[1:]
    print(f"Prompt Check: {label} ({score:.2f})")

    if label == "jailbreak" and score > 0.9:
        return jsonify({"blocked": True, "message": "Prompt violates safety guidelines"})

    response = get_model_response(prompt)

    # Check the response for jailbreak content in chunks
    blocked, label, score = detect_jailbreak(response)
    print(f"Response Check: {label} ({score:.2f})")

    if blocked:
        return jsonify({"blocked": True, "message": "Response violates safety guidelines"})

    return jsonify({"blocked": False, "response": response})

if __name__ == "__main__":
    app.run(debug=True, port=5000)