import requests
import os
import time
import base64
from dotenv import load_dotenv
import glob
import fitz  # PyMuPDF
from PIL import Image
import io
from mistralai import Mistral
from pyzerox import zerox
import boto3

load_dotenv()
llmf_key = os.getenv("llmf-key")
omni_key = os.getenv("omni-key")
mistral_key = os.getenv("mistral-key")


def pdf_to_images_pymupdf(pdf_file):
    doc = fitz.open(pdf_file)
    images = []
    
    for page in doc:
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        images.append(img)

    return images

def image_to_base64(image):
    img_buffer = io.BytesIO()
    image.save(img_buffer, format="PNG")
    return base64.b64encode(img_buffer.getvalue()).decode("utf-8")

# gpt4o works(images)
# azure works(pdfs)
# omniai(400)
# mistral(ssl cert)


# def ocr_gpt4o(pdf_file):
#     start_time = time.time()
#     images = pdf_to_images_pymupdf(pdf_file)
#     print(f"Image generated from PDF: {pdf_file}")
#     base64_images = [image_to_base64(img) for img in images]
    
#     extracted_texts = []
#     for img_b64 in base64_images:
#         response = requests.post(
#             "https://llmfoundry.straive.com/v1/chat/completions",
#             json={
#                 "model": "gpt-4o",
#                 "messages": [
#                     {
#                         "role": "user",
#                         "content": [
#                             {
#                                 "type": "text",
#                                 "text": (
#                                     "Extract all the text content from this image thoroughly and accurately. Ensure that no lines, words, or parts of the content are missed, even if the text is faint, small, or near the edges. The text may include headings, paragraphs, or lists and could appear in various fonts, styles, or layouts. Carefully preserve the reading order and structure as it appears in the image. Double-check for any skipped lines or incomplete content, and extract every visible text element, ensuring completeness across all sections. This is crucial for the task's accuracy."
#                                 )
#                             },
#                             {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
#                         ],
#                     }
#                 ],
#                 "max_tokens": 300,
#             },
#             headers={"Authorization": f"Bearer {llmf_key}"}
#         )
        
#         if response.status_code == 200:
#             result = response.json()
#             extracted_texts.append(result["choices"][0]["message"]["content"])
#         else:
#             extracted_texts.append("OCR failed for an image")
    
#     processing_time = time.time() - start_time
#     return "\n".join(extracted_texts), processing_time
    
    
# def ocr_azure(pdf_file):
#     start_time = time.time()
#     with open(pdf_file, 'rb') as file:
#         pdf_base64 = base64.b64encode(file.read()).decode("utf-8")
#         response = requests.post(
#             url= "https://llmfoundry.straive.com/azureformrecognizer/analyze",
#             headers = {"Authorization": f"Bearer {llmf_key}:ocr_benchmark",
#                        "Cache-Control": "no-cache"},
#             json= {
#                     "model": "prebuilt-layout",
#                     "document": f"data:application/pdf;base64,{pdf_base64}", 
#                     }
#             )
#     if response.status_code == 200:
#         result = response.json()
#         # print(result)
#         content = result["content"]
#         processing_time = time.time() - start_time
#         token_cnt = -1
#         return content, processing_time, token_cnt

#     return "Need to be parsed", 0, 0

# def ocr_omniai(pdf_file):
#     start_time = time.time()
#     with open(pdf_file, 'rb') as file:
#         # file = base64.b64encode(file.read()).decode("utf-8")
#         response = requests.request("POST",
#                                 url= "https://api.getomni.ai/extract/sync",
#                                 headers= {
#                                     "x-api-key": omni_key,
#                                     "Content-Type": "multipart/form-data"
#                                 },
#                                 json= {
#                                     "file": file,
#                                     "bypassCache": True
#                                 },
#                                 verify=False
#                                 )
#     print(response)
#     if response.status_code == 200:
#         result = response.json()
#         # print(result)
#         response_time = result["result"]["ocr"]["completionTime"] 
#         input_tokens = result["result"]["ocr"]["inputTokens"]
#         output_tokens = result["result"]["ocr"]["outputTokens"]
#         all_content = "\n".join(page["content"] for page in result["result"]["ocr"]["pages"])
#     else:
#         return "OCR failed", 0 , 0
#     return all_content, response_time, input_tokens+output_tokens

# def ocr_mistral(pdf_file):
#     start_time = time.time()
#     client = Mistral(api_key = mistral_key)
#     uploaded_pdf = client.files.upload(
#         file= {
#             "file_name" : "pdf_file",
#             "content" : open(pdf_file, "rb"),
#         },
#         purpose = 'ocr'
#     )
#     signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)

#     ocr_response = client.ocr.process(
#     model="mistral-ocr-latest",
#     document={
#         "type": "document_url",
#         "document_url": signed_url.url,
#     }
#     )
#     result = ocr_response.model_dump()
#     concatenated_text = "\n\n".join(page["markdown"] for page in result["pages"])
#     processing_time = time.time() - start_time
#     return concatenated_text, processing_time

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

def load_pdfs(pdf_dir):
    """Load all PDF file paths from the given directory."""
    pdf_paths = glob.glob(os.path.join(pdf_dir, "*.pdf"))
    return pdf_paths

pdfs = load_pdfs("./pdfs")
result = ocr_aws_textract(pdfs[0])
print(result)