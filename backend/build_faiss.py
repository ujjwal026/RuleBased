from langchain_community.embeddings import OllamaEmbeddings
from langchain.vectorstores import FAISS
import os
import json

roles = ["admin", "manager", "developer"]
data_dir = "data/"
index_dir = "faiss_index/"

os.makedirs(index_dir, exist_ok=True)

embeddings_model = OllamaEmbeddings(model="llama3.1:8b")
metadata = {}

for role in roles:
    file_path = os.path.join(data_dir, f"{role}_docs.txt")
    with open(file_path, 'r', encoding='utf-8') as f:
        docs = f.readlines()
    
    docs = [doc.strip() for doc in docs if doc.strip()]
    faiss_index = FAISS.from_texts(docs, embedding=embeddings_model)
    faiss_index.save_local(os.path.join(index_dir, role))
    metadata[role] = len(docs)

with open(os.path.join(index_dir, "index_metadata.json"), "w") as f:
    json.dump(metadata, f, indent=4)

print("FAISS indices created for roles:", metadata)
