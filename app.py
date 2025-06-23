from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash
import re
import jwt
import datetime
from functools import wraps
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

from blocked_content import BLOCKED_PHRASES, BLOCKED_REGEX_PATTERNS
from documents import ROLE_DOCUMENTS  
import os
import json

# Configuration
SECRET_KEY = "H@ll)!"
JAILBREAK_THRESHOLD = 0.90
TOXICITY_LABELS = {"toxic", "severe toxic", "obscene", "threat", "insult", "identity hate"}
TOXICITY_THRESHOLD = 0.6
# Load models and tokenizer
jailbreak_tokenizer = AutoTokenizer.from_pretrained("uj26/Securing_llm_model")
jailbreak_detector = pipeline("text-classification", model="uj26/Securing_llm_model")
toxicity_tokenizer = AutoTokenizer.from_pretrained("s-nlp/roberta_toxicity_classifier")
toxicity_model = AutoModelForSequenceClassification.from_pretrained("s-nlp/roberta_toxicity_classifier")
toxicity_detector = pipeline(
    "text-classification",
    model=toxicity_model,
    tokenizer=toxicity_tokenizer,
    return_all_scores=True  # Important for getting all class scores
)

llm = Ollama(model="llama3.1:8b")
embeddings = OllamaEmbeddings(model="llama3.1:8b")

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
CORS(app)

# User database (in production, use a proper database)
USERS = {
    "admin": {
        "password": generate_password_hash("admin123"),
        "role": "admin",
        "permissions": ["all_documents", "user_management", "system_config"]
    },
    "manager": {
        "password": generate_password_hash("manager123"),
        "role": "manager", 
        "permissions": ["team_documents", "reports", "analytics"]
    },
    "developer": {
        "password": generate_password_hash("dev123"),
        "role": "developer",
        "permissions": ["technical_docs", "code_review", "deployment"]
    }
}

# Role-based document collections
# ROLE_DOCUMENTS = {
#     "admin": [
#         "Company policies and procedures",
#         "Employee handbook and HR guidelines", 
#         "Financial reports and budget information",
#         "System administration documentation",
#         "Legal compliance requirements"
#     ],
#     "manager": [
#         "Team performance metrics",
#         "Project management guidelines",
#         "Meeting minutes and action items",
#         "Resource allocation strategies",
#         "Team building activities"
#     ],
#     "developer": [
#         "API documentation and endpoints",
#         "Code review guidelines",
#         "Deployment procedures",
#         "Technical architecture documents",
#         "Database schema and queries"
#     ]
# }

# Initialize vector stores for each role
vector_stores = {}

def initialize_vector_stores():
    """Initialize FAISS vector stores for each role"""
    global vector_stores
    
    for role, documents in ROLE_DOCUMENTS.items():
        # Convert strings to Document objects
        docs = [Document(page_content=doc, metadata={"role": role}) for doc in documents]
        
        # Create text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # Split documents
        split_docs = text_splitter.split_documents(docs)
        
        # Create vector store
        vector_stores[role] = FAISS.from_documents(split_docs, embeddings)
        print(f"Initialized vector store for {role} with {len(split_docs)} chunks")

# Initialize vector stores on startup
initialize_vector_stores()

# Session storage for chat history per user
user_sessions = {}

def token_required(f):
    """Decorator to require authentication token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
            
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user = data['username']
            current_role = data['role']
        except:
            return jsonify({'message': 'Token is invalid'}), 401
            
        return f(current_user, current_role, *args, **kwargs)
    
    return decorated

def is_inappropriate(prompt):
    """Check if prompt contains inappropriate content"""
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

def detect_toxicity(text, threshold=TOXICITY_THRESHOLD):
    """Check if text contains toxic or unsafe content with chunking for long inputs"""
    encoded = toxicity_tokenizer(
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
        chunk_text_preview = toxicity_tokenizer.decode(chunk_tokens, skip_special_tokens=True)

        results = toxicity_detector(chunk_text_preview, truncation=True, max_length=512)

        for result in results[0]:  # results[0] is list of dicts with 'label' and 'score'
            label = result["label"].lower()
            score = result["score"]

            if label in TOXICITY_LABELS and score > threshold:
                print(f"Chunk {i//chunk_size + 1}: {label} ({score:.2f})")
                return True, label, score

    return False, "safe", 0.0


def detect_jailbreak(text, threshold=JAILBREAK_THRESHOLD):
    """Check if text contains jailbreak attempts"""
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

        result = jailbreak_detector(chunk_text_preview, truncation=True, max_length=512)
        label = result[0]["label"]
        score = result[0]["score"]

        print(f"Chunk {i//chunk_size + 1}: {label} ({score:.2f})")

        if label == "jailbreak" and score > threshold:
            return True, label, score

    return False, "safe", 0.0

def get_rag_response(prompt, role, username):
    """Generate RAG-based response using role-specific knowledge base"""
    
    # Get user session history
    if username not in user_sessions:
        user_sessions[username] = []
    
    session_history = user_sessions[username]
    
    # Retrieve relevant documents from role-specific vector store
    if role not in vector_stores:
        return "No knowledge base available for your role."
    
    # Search for relevant documents
    docs = vector_stores[role].similarity_search(prompt, k=3)
    context = "\n".join([doc.page_content for doc in docs])
    
    # Create role-specific system prompt
    role_prompts = {
        "admin": "You are an administrative assistant with access to company policies, HR guidelines, and system administration information. Provide professional and authoritative responses.",
        "manager": "You are a management assistant helping with team leadership, project management, and strategic decisions. Focus on actionable insights and team coordination.",
        "developer": "You are a technical assistant specializing in software development, API documentation, and system architecture. Provide detailed technical guidance."
    }
    
    system_prompt = role_prompts.get(role, "You are a helpful assistant.")
    
    # Build the full prompt with context and history
    full_prompt = f"{system_prompt}\n\nRelevant Information:\n{context}\n\n"
    
    # Add conversation history
    if session_history:
        full_prompt += "Previous conversation:\n"
        for i, msg in enumerate(session_history[-6:]):  # Last 3 exchanges
            role_name = "User" if msg["role"] == "user" else "Assistant"
            full_prompt += f"{role_name}: {msg['content']}\n"
    
    full_prompt += f"\nUser: {prompt}\nAssistant:"
    
    # Add current message to history
    session_history.append({"role": "user", "content": prompt})
    
    # Generate response
    response = llm.invoke(full_prompt).strip()
    
    # Add response to history
    session_history.append({"role": "assistant", "content": response})
    
    # Keep only last 20 messages to prevent memory issues
    user_sessions[username] = session_history[-20:]
    
    return response

@app.route("/login", methods=["POST"])
def login():
    """Authenticate user and return JWT token"""
    data = request.json
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    
    user = USERS.get(username)
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Generate JWT token
    token = jwt.encode({
        'username': username,
        'role': user['role'],
        'permissions': user['permissions'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, SECRET_KEY, algorithm='HS256')
    
    return jsonify({
        "token": token,
        "role": user['role'],
        "permissions": user['permissions'],
        "message": f"Successfully logged in as {user['role']}"
    })

@app.route("/chat", methods=["POST"])
@token_required
def chat(current_user, current_role):
    """Main chat endpoint with jailbreak protection and RAG"""
    data = request.json
    prompt = data.get("prompt", "").strip()
    
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    
    # Check for inappropriate content
    if is_inappropriate(prompt):
        return jsonify({
            "blocked": True, 
            "message": "Prompt contains inappropriate content"
        }), 400
    
    # Check for jailbreak attempts in prompt
    blocked, label, score = detect_jailbreak(prompt)
    print(f"Prompt Check - User: {current_user}, Role: {current_role}, Result: {label} ({score:.2f})")
    
    if blocked:
        return jsonify({
            "blocked": True,
            "message": "Prompt violates safety guidelines"
        }), 400
    
    try:
        # Generate RAG response
        response = get_rag_response(prompt, current_role, current_user)
        print(response)
        # Check response for jailbreak content
        blocked, label, score = detect_toxicity(response)
        print(f"Response Check - User: {current_user}, Result: {label} ({score:.2f})")
        
        if blocked:
            return jsonify({
                "blocked": True,
                "message": "Response violates safety guidelines"
            }), 400
        
        return jsonify({
            "blocked": False,
            "response": response,
            "role": current_role,
            "user": current_user
        })
        
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return jsonify({"error": "Failed to generate response"}), 500

@app.route("/user_info", methods=["GET"])
@token_required  
def get_user_info(current_user, current_role):
    """Get current user information"""
    user = USERS.get(current_user)
    return jsonify({
        "username": current_user,
        "role": current_role,
        "permissions": user.get('permissions', [])
    })

@app.route("/clear_history", methods=["POST"])
@token_required
def clear_history(current_user, current_role):
    """Clear user's chat history"""
    if current_user in user_sessions:
        del user_sessions[current_user]
    return jsonify({"message": "Chat history cleared"})

@app.route("/add_document", methods=["POST"])
@token_required
def add_document(current_user, current_role):
    """Add new document to role-specific knowledge base (admin only)"""
    if current_role != "admin":
        return jsonify({"error": "Insufficient permissions"}), 403
    
    data = request.json
    role = data.get("role")
    document = data.get("document")
    
    if not role or not document or role not in ROLE_DOCUMENTS:
        return jsonify({"error": "Invalid role or document"}), 400
    
    # Add document to role collection
    ROLE_DOCUMENTS[role].append(document)
    
    # Reinitialize vector store for the role
    docs = [Document(page_content=doc, metadata={"role": role}) for doc in ROLE_DOCUMENTS[role]]
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    split_docs = text_splitter.split_documents(docs)
    vector_stores[role] = FAISS.from_documents(split_docs, embeddings)
    
    return jsonify({"message": f"Document added to {role} knowledge base"})

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.datetime.utcnow().isoformat()})

if __name__ == "__main__":
    print("Initializing Role-Based RAG System...")
    print(f"Available roles: {list(ROLE_DOCUMENTS.keys())}")
    print("Default credentials:")
    print("- admin/admin123 (full access)")
    print("- manager/manager123 (management docs)")  
    print("- developer/dev123 (technical docs)")
    app.run(debug=True, port=5000)
