from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain.vectorstores import FAISS

# Load LLaMa model & embedding model once
llm = Ollama(model="llama3.1:8b")
embedding_model = OllamaEmbeddings(model="llama3.1:8b")

# Load FAISS Indices for roles
faiss_indices = {}
roles = ["admin", "manager", "developer"]
for role in roles:
    faiss_indices[role] = FAISS.load_local(f"faiss_index/{role}", embedding_model, allow_dangerous_deserialization=True)


def get_rag_response(prompt, role):
    index = faiss_indices.get(role)
    if not index:
        return "No relevant data found for your role."

    # Retrieve top-k docs
    docs_and_scores = index.similarity_search_with_score(prompt, k=3)
    context = "\n".join([doc.page_content for doc, _ in docs_and_scores])

    final_prompt = f"""You are a helpful assistant. Based on the following context, answer the user's question.

Context:
{context}

Question: {prompt}
Answer:"""

    response = llm.invoke(final_prompt)
    return response.strip()
