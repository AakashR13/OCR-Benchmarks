import os
import glob
import time
import random
import difflib
import statistics
import requests
from pdf2image import convert_from_path
import base64
from dotenv import load_dotenv
import io
import boto3
from mistralai import Mistral

# Configuration for cost calculation per token (example: $0.00001 per token)
# COST_PER_TOKEN = 0.00001

# Directory containing PDFs to benchmark
PDF_DIR = "pdfs"  # adjust as needed
load_dotenv()
mistral_key = os.getenv("mistral-key")
omni_key = os.getenv("omni-key")
llmf_key = os.getenv("llmf-key")

# OmniAI    - Only 100 pages
# Gemini    - Uses images
# Azure     - Need to test response
# gpt4o     - uses images
# aws-text  - No clue
# mistral   - 

def image_to_base64(image):
    img_buffer = io.BytesIO()
    image.save(img_buffer, format="PNG")
    return base64.b64encode(img_buffer.getvalue()).decode("utf-8")

def ocr_omniai(pdf_file):
    start_time = time.time()
    response = requests.request("POST",
                                url= "https://api.getomni.ai/extract/sync",
                                json= {
                                    "file": pdf_file,
                                    "bypassCache": True
                                },
                                headers= {
                                    "x-api-key": omni_key,
                                    "Content-Type": "multipart/form-data"
                                })
    if response.status_code == 200:
        result = response.json()
        response_time = result["result"]["ocr"]["completionTime"] 
        input_tokens = result["result"]["ocr"]["inputTokens"]
        output_tokens = result["result"]["ocr"]["outputTokens"]
        all_content = "\n".join(page["content"] for page in result["result"]["ocr"]["pages"])
    else:
        return "OCR failed", 0 , 0
    return all_content, response_time, input_tokens+output_tokens


def ocr_gemini(pdf_file):
    # Seems to use images
    return dummy_ocr("Gemini 2.0 Flash", pdf_file)

def ocr_azure(pdf_file):
    start_time = time.time()
    with open(pdf_file, 'rb') as file:
        pdf_base64 = base64.b64encode(file.read()).decode("utf-8")
        response = requests.post(
            url= "https://llmfoundry.straive.com/azureformrecognizer/analyze",
            headers = {"Authorization": f"Bearer {llmf_key}:ocr_benchmark"},
            json= {
                    "model": "prebuilt-layout",
                    "document": f"data:application/pdf;base64,{pdf_base64}", 
                    }
            )
    if response.status_code == 200:
        result = response.json()
        # print(result)
        content = result["content"]
        processing_time = time.time() - start_time
        token_cnt = -1
        return content, processing_time, token_cnt

    return "Need to be parsed", 0, 0

def ocr_gpt4o(pdf_file):
    start_time = time.time()
    images = convert_from_path(pdf_file, dpi = 200)
    print(f"Image generated from PDF: {pdf_file}")
    base64_images = [image_to_base64(img) for img in images]
    messages = [{"role": "system", "content": "Extract text from these document images."}]
    for img_b64 in base64_images:
        messages.append({"role": "user", "content": [{"type": "image", "image": img_b64}]})

    # Send request to OpenAI GPT-4o
    response = requests.post(
        "https://llmfoundry.straive.com/v1/chat/completions",
        json={"model": "gpt-4o", "messages": messages},
        headers={"Authorization": f"Bearer {llmf_key}"}
    )
    if response.status_code == 200:
        result = response.json()
        extracted_text = result["choices"][0]["message"]["content"]
        processing_time = time.time() - start_time
        token_count = result["usage"]["prompt_tokens"] + result["usage"]["total_tokens"]
        return extracted_text, processing_time, token_count
    else:
        return "OCR failed", 0, 0
    # return dummy_ocr("GPT-4o", pdf_file)

def ocr_aws_textract(pdf_file):
    start_time = time.time()
    textract = boto3.client(
        "textract",
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name="us-east-1"  # Change based on your AWS region
    )
    
    with open(pdf_file, "rb") as file:
        response = textract.analyze_document(
            Document={"Bytes": file.read()},
            FeatureTypes=["TABLES", "FORMS"]
        )
    
    extracted_text = "\n".join([block["Text"] for block in response["Blocks"] if block["BlockType"] == "LINE"])
    processing_time = time.time() - start_time
    return extracted_text, processing_time, 0   

def ocr_mistral(pdf_file):
    client = Mistral(api_key = mistral_key)
    uploaded_pdf = client.files.upload(
        file= {
            "file_name" : "uploaded_pdf",
            "content" : open("uploaded_file.pdf", "rb"),
        },
        purpose = 'ocr'
    )
    signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)

    ocr_response = client.ocr.process(
    model="mistral-ocr-latest",
    document={
        "type": "document_url",
        "document_url": signed_url.url,
    }
    )
    result = ocr_response.json()
    print(result)
    # return dummy_ocr("Mistral OCR", pdf_file)

# Dictionary mapping model names to their OCR function
OCR_MODELS = {
    "OmniAi": ocr_omniai,
    "Gemini 2.0 Flash": ocr_gemini,
    "Azure": ocr_azure,
    "GPT-4o": ocr_gpt4o,
    # "AWS Textract": ocr_aws_textract,
    "Mistral OCR": ocr_mistral
}


def count_tokens(text):
    """Simple token count using whitespace splitting."""
    return len(text.split())

# def calculate_cost(token_count, cost_per_token=COST_PER_TOKEN):
#     """Calculate the cost from token count."""
#     return token_count * cost_per_token

def similarity_ratio(text1, text2):
    """
    Calculate a similarity ratio between two texts.
    Using difflib.SequenceMatcher for simplicity.
    """
    return difflib.SequenceMatcher(None, text1, text2).ratio()

def select_best_run(runs):
    """
    Given a list of runs (each a dict with a 'text' key), compute pairwise
    similarity and return the run whose text is closest to the others.
    """
    n = len(runs)
    if n < 2:
        return runs[0]
    
    avg_similarities = []
    for i in range(n):
        sims = []
        for j in range(n):
            if i != j:
                sims.append(similarity_ratio(runs[i]['text'], runs[j]['text']))
        avg_sim = statistics.mean(sims)
        avg_similarities.append(avg_sim)
    
    # Choose the run with the highest average similarity
    best_index = avg_similarities.index(max(avg_similarities))
    return runs[best_index]

def score_semantics(text):
    """
    Dummy semantics scoring function.
    In practice, you might use a dictionary check or a language model
    to assess fluency and coherence.
    For now, we use a simple heuristic: average word length.
    """
    words = text.split()
    if not words:
        return 0
    avg_word_length = sum(len(word) for word in words) / len(words)
    # Normalize or scale score as needed; here, higher average word length gets a higher score.
    return avg_word_length

def load_pdfs(pdf_dir):
    """Load all PDF file paths from the given directory."""
    pdf_paths = glob.glob(os.path.join(pdf_dir, "*.pdf"))
    return pdf_paths

def benchmark_model_on_pdf(model_func, pdf_file, runs=3):
    """
    Runs the OCR model on a single PDF file multiple times.
    Returns a list of dictionaries with the results from each run.
    """
    run_results = []
    for i in range(runs):
        text, proc_time = model_func(pdf_file)
        tokens = count_tokens(text)
        # cost = calculate_cost(tokens)
        run_results.append({
            "text": text,
            "time": proc_time,
            "token_count": tokens,
            # "cost": cost
        })
    return run_results

def benchmark_all_models():
    """
    Main function to benchmark all OCR models.
    For each PDF and each model, run OCR 3 times, compute internal consistency,
    choose the best run, and aggregate metrics.
    """
    pdf_files = load_pdfs(PDF_DIR)
    if not pdf_files:
        print("No PDF files found in the directory.")
        return
    
    # Dictionary to hold aggregated results per model
    model_metrics = {model: {"times": [], "token_counts": [], "costs": [], "semantics": [], "results": []}
                     for model in OCR_MODELS.keys()}

    for pdf_file in pdf_files:
        print(f"\nProcessing PDF: {pdf_file}")
        for model_name, model_func in OCR_MODELS.items():
            print(f"  Running model: {model_name}")
            runs = benchmark_model_on_pdf(model_func, pdf_file, runs=3)
            best_run = select_best_run(runs)
            
            # Score semantics of the chosen result
            semantics_score = score_semantics(best_run["text"])
            
            # Store metrics for later aggregation
            model_metrics[model_name]["times"].append(best_run["time"])
            model_metrics[model_name]["token_counts"].append(best_run["token_count"])
            model_metrics[model_name]["costs"].append(best_run["cost"])
            model_metrics[model_name]["semantics"].append(semantics_score)
            model_metrics[model_name]["results"].append(best_run["text"])
            
            print(f"    Best run: time={best_run['time']:.3f}s, tokens={best_run['token_count']}, cost=${best_run['cost']:.5f}, semantics score={semantics_score:.2f}")
    
    # Calculate aggregated metrics and print summary
    print("\n--- Aggregated Model Metrics ---")
    for model_name, metrics in model_metrics.items():
        avg_time = statistics.mean(metrics["times"]) if metrics["times"] else 0
        avg_tokens = statistics.mean(metrics["token_counts"]) if metrics["token_counts"] else 0
        total_cost = sum(metrics["costs"])
        avg_semantics = statistics.mean(metrics["semantics"]) if metrics["semantics"] else 0
        
        print(f"\nModel: {model_name}")
        print(f"  Average Processing Time: {avg_time:.3f} seconds")
        print(f"  Average Token Count: {avg_tokens:.1f}")
        print(f"  Total Cost: ${total_cost:.5f}")
        print(f"  Average Semantics Score: {avg_semantics:.2f}")

    # TODO: Multi-OCR comparison
    # Here, you could compute a metric that compares the chosen OCR texts across different models.
    # For example, you could compute pairwise similarities between models' outputs per PDF and average them.
    print("\nTODO: Compute multi-OCR comparison metric across models.")

if __name__ == "__main__":
    benchmark_all_models()
