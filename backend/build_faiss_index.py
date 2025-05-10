import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# Load data with enhanced validation
try:
    df = pd.read_csv("ecommerce_customers.csv")
    print("✅ Loaded CSV with", len(df), "rows")
    
    # Verify all required columns exist
    required_columns = ['Email', 'Address', 'Avatar', 'Time on App', 
                       'Time on Website', 'Length of Membership', 
                       'Yearly Amount Spent']
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        print(f"❌ Missing required columns: {', '.join(missing_cols)}")
        exit()

except FileNotFoundError:
    print("❌ Error: ecommerce_customers.csv not found")
    exit()

# Create comprehensive text representations
texts = df.apply(lambda row: (
    f"EMAIL: {row['Email']}\n"
    f"ADDRESS: {row['Address']}\n"
    f"AVATAR: {row['Avatar']}\n"
    f"TIME_ON_APP: {row['Time on App']:.2f} hours\n"
    f"TIME_ON_WEBSITE: {row['Time on Website']:.2f} hours\n"
    f"MEMBERSHIP_DURATION: {row['Length of Membership']:.1f} years\n"
    f"YEARLY_SPEND: ${row['Yearly Amount Spent']:.2f}"
), axis=1).tolist()

# Create and verify index
try:
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_db = FAISS.from_texts(texts, embeddings)
    print(f"✅ Index contains {vector_db.index.ntotal} entries")
    
    # Save index
    vector_db.save_local("rag_customer_faiss")
    print("Index saved successfully")

except Exception as e:
    print(f"❌ Error creating/saving index: {str(e)}")
    exit()
    