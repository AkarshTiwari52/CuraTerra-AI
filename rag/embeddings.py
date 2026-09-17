from langchain.embeddings.base import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings

model_name  = "BAAI/bge-m3"

def get_embeddings() -> Embeddings:
    """
    Create and return the multilingual embedding model.
    """

    embeddings =  HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"} ,
        encode_kwargs={"normalize_embeddings": True}
    )

    return embeddings