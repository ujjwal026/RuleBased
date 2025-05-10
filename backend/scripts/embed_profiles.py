from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_core.documents import Document
import re

PROFILE_PATH = "D:/rag-2.0/data/customer_profiles.txt"
EMBED_DIR = "D:/rag-2.0/embeddings/rag_customer_faiss"

def extract_metadata(profile_content):
    """Extract metadata from the profile content"""
    metadata = {}
    # Extract email from metadata section
    email_match = re.search(r"--- METADATA ---\nEmail: (.+?)\n", profile_content)
    if email_match:
        metadata["email"] = email_match.group(1).strip()
    return metadata

def process_profiles():
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Load and verify the profiles file
    try:
        loader = TextLoader(PROFILE_PATH, encoding="utf-8")
        docs = loader.load()
        print(f"✅ Loaded {len(docs)} documents from {PROFILE_PATH}")
    except Exception as e:
        print(f"❌ Failed to load profiles: {str(e)}")
        return

    # Improved splitting that respects profile boundaries
    splitter = CharacterTextSplitter(
        separator="--- METADATA ---",  # Now splitting on metadata markers
        chunk_size=1000,
        chunk_overlap=200,  # Some overlap for context
        is_separator_regex=False,
        keep_separator=True  # Keep the metadata marker
    )
    
    try:
        split_docs = splitter.split_documents(docs)
        print(f"🔨 Split into {len(split_docs)} profile chunks")
    except Exception as e:
        print(f"❌ Failed to split documents: {str(e)}")
        return

    # Process each document to extract metadata
    processed_docs = []
    for doc in split_docs:
        try:
            metadata = extract_metadata(doc.page_content)
            if not metadata.get("email"):
                print(f"⚠️ Missing email in document: {doc.page_content[:100]}...")
                continue
                
            processed_docs.append(Document(
                page_content=doc.page_content,
                metadata=metadata
            ))
        except Exception as e:
            print(f"⚠️ Error processing document: {str(e)}")
            continue

    print(f"📊 Processed {len(processed_docs)} valid profiles with metadata")

    # Create and save FAISS index
    try:
        db = FAISS.from_documents(processed_docs, embeddings)
        db.save_local(EMBED_DIR)
        print(f"💾 Successfully saved FAISS index to {EMBED_DIR}")
        print(f"📊 Index stats: {db.index.ntotal} vectors indexed")
    except Exception as e:
        print(f"❌ Failed to create/save FAISS index: {str(e)}")

if __name__ == "__main__":
    process_profiles()