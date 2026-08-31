import math
import re

# Standard English stop words
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't", "as", "at",
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", "each", "few", "for",
    "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's",
    "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm",
    "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't",
    "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't",
    "so", "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't",
    "what", "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's",
    "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself",
    "yourselves"
}

def tokenize(text: str) -> list[str]:
    """Tokenize a string into words, converting to lowercase and stripping punctuation.
    Supports C++, C#, .NET, and typical acronyms.
    """
    text = text.lower()
    # Replace common formatting characters but preserve special tech prefixes/suffixes (+, #, ., -)
    # e.g., C++, C#, .NET, CI/CD, scikit-learn
    text = re.sub(r"[^a-z0-9\+\#\.\-\/]", " ", text)
    tokens = text.split()
    
    cleaned = []
    for token in tokens:
        # Strip trailing periods/dashes if they are not part of terms (like .net)
        token = token.strip(".-")
        if token and token not in STOP_WORDS and len(token) > 1:
            cleaned.append(token)
            
    return cleaned

def get_tf(tokens: list[str]) -> dict[str, float]:
    """Calculate term frequencies normalized by the length of document."""
    tf: dict[str, float] = {}
    if not tokens:
        return tf
        
    for token in tokens:
        tf[token] = tf.get(token, 0.0) + 1.0
        
    for token in tf:
        tf[token] = tf[token] / len(tokens)
        
    return tf

def calculate_cosine_similarity(text1: str, text2: str) -> float:
    """Compute cosine similarity of term frequency vectors between text1 and text2."""
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)
    
    if not tokens1 or not tokens2:
        return 0.0
        
    tf1 = get_tf(tokens1)
    tf2 = get_tf(tokens2)
    
    # Combined vocabulary of both texts
    vocab = set(tf1.keys()).union(set(tf2.keys()))
    
    dot_product = sum(tf1.get(word, 0.0) * tf2.get(word, 0.0) for word in vocab)
    magnitude1 = math.sqrt(sum(val ** 2 for val in tf1.values()))
    magnitude2 = math.sqrt(sum(val ** 2 for val in tf2.values()))
    
    if magnitude1 == 0.0 or magnitude2 == 0.0:
        return 0.0
        
    return dot_product / (magnitude1 * magnitude2)
