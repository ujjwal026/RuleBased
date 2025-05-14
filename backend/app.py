from flask import Flask, request, jsonify, session
from flask_cors import CORS
from users import USERS
from rag_utils import get_rag_response
from safety_checks import is_inappropriate, detect_jailbreak

app = Flask(__name__)
app.secret_key = 'supersecretkey'
CORS(app)

# --- Routes ---
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    user = USERS.get(username)
    if user and user["password"] == password:
        session['username'] = username
        session['role'] = user["role"]
        return jsonify({"success": True, "role": user["role"]})
    else:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

@app.route("/check_prompt", methods=["POST"])
def check_prompt():
    if 'username' not in session:
        return jsonify({"blocked": True, "message": "Unauthorized. Please login."}), 403

    role = session.get('role')
    data = request.json
    prompt = data.get("prompt", "").strip()

    if is_inappropriate(prompt):
        return jsonify({"blocked": True, "message": "Prompt violates safety policies."})

    # Jailbreak check on prompt
    is_jailbreak, label, score = detect_jailbreak(prompt)
    if is_jailbreak:
        return jsonify({"blocked": True, "message": "Prompt violates safety guidelines."})

    # Get RAG response
    response = get_rag_response(prompt, role)

    # Jailbreak check on response
    is_jailbreak_resp, label_resp, score_resp = detect_jailbreak(response)
    if is_jailbreak_resp:
        return jsonify({"blocked": True, "message": "Response violates safety guidelines."})

    return jsonify({"blocked": False, "response": response})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
