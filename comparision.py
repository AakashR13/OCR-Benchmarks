import os
import nltk
import textstat
import string
from bs4 import BeautifulSoup
import markdown
from difflib import SequenceMatcher
from Levenshtein import ratio
from collections import Counter
from nltk.corpus import words, brown
from nltk.util import ngrams
from textblob import TextBlob

# Ensure required NLTK modules are available
nltk.download('punkt')
nltk.download('words')
nltk.download('brown')
nltk.download('punkt_tab')

def load_text(file_path):
    """Reads text from a given file and removes any HTML markup."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            raw_content = file.read()
            html_content = markdown.markdown(raw_content)  # Convert Markdown to HTML
            clean_text = BeautifulSoup(html_content, "html.parser").get_text()  # Remove HTML tags
            return clean_text.strip()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""

def word_count(text):
    return len(nltk.word_tokenize(text))

def avg_word_size(text):
    words = [w for w in nltk.word_tokenize(text) if w.isalpha()]
    return sum(len(word) for word in words) / max(len(words), 1) if words else 0

def readability_score(text):
    return textstat.flesch_kincaid_grade(text)

def coherence_score(text):
    sentences = nltk.sent_tokenize(text)
    words = nltk.word_tokenize(text)
    return len(words) / max(len(sentences), 1) if sentences else 0

def sentiment_analysis(text):
    analysis = TextBlob(text)
    return {"Polarity": analysis.sentiment.polarity, "Subjectivity": analysis.sentiment.subjectivity}

def dictionary_validity(text):
    english_vocab = set(words.words())
    words_in_text = [word.lower() for word in nltk.word_tokenize(text) if word.isalpha()]
    valid_words = sum(1 for word in words_in_text if word in english_vocab)
    return valid_words / max(len(words_in_text), 1) if words_in_text else 0

def n_gram_analysis(text, n=3):
    words_in_text = [word.lower() for word in nltk.word_tokenize(text) if word.isalpha()]
    text_ngrams = set(ngrams(words_in_text, n))
    brown_words = [word.lower() for word in brown.words() if word.isalpha()]
    brown_ngrams = set(ngrams(brown_words, n))
    matching_ngrams = text_ngrams.intersection(brown_ngrams)
    return len(matching_ngrams) / max(len(text_ngrams), 1) if text_ngrams else 0

def save_results(scores, comparisons, output_file):
    """Save individual results and comparison metrics to a file."""
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write("OCR Comparison & Statistics Report\n\n")
        
        # Save individual file statistics
        file.write("=== Individual File Statistics ===\n\n")
        for filename, data in scores.items():
            file.write(f"File: {filename}\n")
            for metric, value in data.items():
                file.write(f"  {metric}: {value}\n")
            file.write("\n")
        
        # Save comparison metrics
        file.write("=== Comparisons Between Files ===\n\n")
        for metric, result in comparisons.items():
            file.write(f"{metric}: {result}\n")

    print(f"\n✅ Results saved to {output_file}")

def compare_metrics(scores):
    """Compare metrics across all files and determine best/worst performers."""
    comparisons = {}
    
    # Extract all metric names
    metrics = list(next(iter(scores.values())).keys())

    for metric in metrics:
        values = {file: data[metric] for file, data in scores.items()}

        if isinstance(next(iter(values.values())), dict):  # If it's sentiment (dict)
            comparisons[metric] = {key: max(values, key=lambda f: values[f][key]) for key in ["Polarity", "Subjectivity"]}
        else:
            comparisons[f"Best {metric}"] = max(values, key=values.get)
            comparisons[f"Worst {metric}"] = min(values, key=values.get)

    return comparisons

def compare_ocr_results(directory=".", output_file="ocr_comparison_results.txt"):
    """Compare all OCR-generated text files in a directory."""
    files = [f for f in os.listdir(directory) if f.endswith('.txt')]
    
    if not files:
        print("No .txt files found in the directory.")
        return
    
    scores = {}

    for file in files:
        print(f"\n📄 Processing {file} ...")
        text = load_text(os.path.join(directory, file))
        if not text:
            print(f"⚠️ Skipping {file} (empty or unreadable)\n")
            continue
        
        scores[file] = {
            "Word Count": word_count(text),
            "Avg. Word Size": avg_word_size(text),
            "Readability": readability_score(text),
            "Coherence": coherence_score(text),
            "Dictionary Validity": dictionary_validity(text),
            "N-Gram Accuracy": n_gram_analysis(text, 3),
            "Sentiment": sentiment_analysis(text)
        }
    
    # Compare results across all files
    comparisons = compare_metrics(scores)

    # Save results to file
    save_results(scores, comparisons, output_file)

# Example Usage
if __name__ == "__main__":
    compare_ocr_results("./content")
