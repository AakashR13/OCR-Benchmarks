import nltk
import textstat
from difflib import SequenceMatcher
from Levenshtein import ratio

# Ensure required NLTK modules are available
nltk.download('punkt')

def load_text(file_path):
    """Reads text from a given file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""

def readability_score(text):
    """Calculate readability score using Flesch-Kincaid grade level."""
    return textstat.flesch_kincaid_grade(text)

def lexical_similarity(text1, text2):
    """Calculate similarity between two texts using Levenshtein ratio."""
    return ratio(text1, text2)

def structure_similarity(text1, text2):
    """Compare structural similarity (line breaks and spaces)."""
    return SequenceMatcher(None, text1, text2).ratio()

def coherence_score(text):
    """Check if the text forms coherent sentences based on average sentence length."""
    sentences = nltk.sent_tokenize(text)
    words = nltk.word_tokenize(text)
    avg_sentence_length = len(words) / max(len(sentences), 1)
    return avg_sentence_length  # Longer, structured sentences suggest better OCR

def save_results(scores, output_file):
    """Saves the comparison metrics to a text file."""
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write("OCR Comparison Results:\n\n")
        for metric, value in scores.items():
            file.write(f"{metric}: {value}\n")
        file.write(f"\nBased on readability and coherence, {scores['Better Text']} is likely more accurate.\n")
    print(f"Results saved to {output_file}")

def compare_ocr_results(file1, file2, output_file="ocr_comparison_results.txt"):
    """Compare two OCR results and determine which one is likely more accurate."""
    
    text1 = load_text(file1)
    text2 = load_text(file2)

    if not text1 or not text2:
        print("Error: One or both files are empty or could not be read.")
        return

    scores = {
        "Readability": (readability_score(text1), readability_score(text2)),
        "Lexical Similarity": lexical_similarity(text1, text2),
        "Structural Similarity": structure_similarity(text1, text2),
        "Coherence": (coherence_score(text1), coherence_score(text2))
    }

    # Determine which text has better readability and coherence
    better_text = "File 1" if scores["Readability"][0] < scores["Readability"][1] else "File 2"
    scores["Better Text"] = better_text

    print("\nComparison Scores:")
    for metric, value in scores.items():
        print(f"{metric}: {value}")
    
    print(f"\nBased on readability and coherence, {better_text} is likely more accurate.")

    save_results(scores, output_file)

# Example Usage
if __name__ == "__main__":
    file1 = "gpt4_content.txt"  # Replace with your actual file path
    file2 = "azure_content.txt"  # Replace with your actual file path
    output_file = "ocr_comparison_results.txt"
    
    compare_ocr_results(file1, file2, output_file)
