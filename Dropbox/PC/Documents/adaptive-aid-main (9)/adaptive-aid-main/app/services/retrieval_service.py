from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


# Free local embedding model
Settings.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Important: we are NOT using LlamaIndex to call the LLM
Settings.llm = None


def get_relevant_material_context(
    material_text: str,
    topic: str = "important course concepts for MCQ generation",
    top_k: int = 4
) -> str:
    """
    Takes extracted material text and returns the most relevant chunks.
    This is what you send to DeepSeek instead of sending the whole material.
    """

    if not material_text or not material_text.strip():
        return ""

    document = Document(text=material_text)

    index = VectorStoreIndex.from_documents([document])

    retriever = index.as_retriever(similarity_top_k=top_k)

    nodes = retriever.retrieve(topic)

    context_parts = []

    for node in nodes:
        context_parts.append(node.get_content())

    return "\n\n".join(context_parts)