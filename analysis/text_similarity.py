from sentence_transformers import SentenceTransformer, util
import spacy

# Attempt to load the SentenceTransformer model for semantic similarity.
# This model provides a more sophisticated understanding of text meaning.
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception:
    # If the model fails to load (e.g., no internet connection, model not found),
    # we will fall back to a simpler similarity method using spaCy.
    model = None

# Load a blank English spaCy model. This will be used as a fallback
# for text similarity if the SentenceTransformer model is not available.
# We are using a blank model because we primarily need its tokenization
# and vector capabilities for similarity calculation.
nlp = spacy.blank('en')

def compute_text_similarity(text1, text2):
    """
    Computes the similarity between two text strings.

    It first attempts to use a SentenceTransformer model for semantic similarity.
    If the model is not available, it falls back to using spaCy's token vector
    similarity.

    Args:
        text1 (str): The first text string.
        text2 (str): The second text string.

    Returns:
        float: A similarity score between 0.0 and 1.0, where 1.0 indicates
               maximum similarity. Returns 0.5 as a default fallback
               if spaCy vectors are not available.
    """
    if model:
        # Use SentenceTransformer for semantic similarity
        emb1 = model.encode(text1, convert_to_tensor=True)
        emb2 = model.encode(text2, convert_to_tensor=True)
        sim = float(util.pytorch_cos_sim(emb1, emb2)[0][0])
        return sim

    # Fallback: Use spaCy's vector similarity
    doc1 = nlp(text1)
    doc2 = nlp(text2)
    # spaCy similarity relies on word vectors. If vectors are not present
    # (e.g., with a blank model or for very short texts), vector_norm will be 0.
    # We return 0.5 in this case as a neutral similarity score.
    return doc1.similarity(doc2) if doc1.vector_norm and doc2.vector_norm else 0.5