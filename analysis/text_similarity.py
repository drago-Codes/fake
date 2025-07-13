from sentence_transformers import SentenceTransformer, util
import spacy

try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception:
    model = None
nlp = spacy.blank('en')

def compute_text_similarity(text1, text2):
    if model:
        emb1 = model.encode(text1, convert_to_tensor=True)
        emb2 = model.encode(text2, convert_to_tensor=True)
        sim = float(util.pytorch_cos_sim(emb1, emb2)[0][0])
        return sim
    # Fallback: spaCy
    doc1 = nlp(text1)
    doc2 = nlp(text2)
    return doc1.similarity(doc2) if doc1.vector_norm and doc2.vector_norm else 0.5 