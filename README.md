# OCR Benchmark
- No ground truth is available
- Metrics:
    - Internal Consistency:
        - Run same OCR model 3 times and do cross comparision.
        - Higher Similarity -> Higher Consistency
        - Take result closest to average for next step
    - Multi-OCR:
        - Take mean result and compare between each model
        - Not completely sure how to get a numerical metric for this(TO DO)
    - Speed:
        - Simply take avg speed for each model and compare
    - Token Count:
        - Take avg token count for each model and compare
        - Calculate cost from that as well
    - Semantics:
        - Compare with a dictionary and/or language model to score based off of fluency and coherency

- Models:
    - OmniAi
    - Gemini 2.0 Flash
    - Azure
    - GPT-4o
    - AWS Textract
    - Mistral OCR

- Extra:
    - Try OmniParser to test bounding boxes for pdfs

- Workflow:
    1. Load pdfs
    2. Run OCR for each model n=3 times
    3. Compare and get details of avg
    4. Calculate speed, token count, total cost
    5. Compare with other llms

- Doubts:
    - Concentrate on financial Data
    - Drop Image Testing
    - Convert to Images then pdfs?




# Model Setup
# 2
    # uploaded_pdf = client.files.upload(
    # file={
    #     "file_name": "Extracted_data/647222_UK_03899913_02-2022.pdf",
    #     "content": open("Extracted_data/647222_UK_03899913_02-2022.pdff", "rb"),
    # },
    # purpose="ocr"
    # )  
    # client.files.retrieve(file_id=uploaded_pdf.id)
#------------------------------------------------------------------------#
# MISTRAL-OCR
# api_key = os.environ["MISTRAL_API_KEY"]
# client = Mistral(api_key=api_key)

# uploaded_pdf = client.files.upload(
#     file={
#         "file_name": "uploaded_file.pdf",
#         "content": open("uploaded_file.pdf", "rb"),
#     },
#     purpose="ocr"
# )  

# client.files.retrieve(file_id=uploaded_pdf.id)
#------------------------------------------------------------------------#
# OMNIAI-OCR
# url = "https://api.getomni.ai/extract"
# headers = {
#     "x-api-key": "<your-api-key>",
#     "Content-Type": "application/json"
# }
# payload = {
#     "url": "<file-url>",
#     "templateId": "<template-id>",
# }

# response = requests.request("POST", url, json=payload, headers=headers)
#------------------------------------------------------------------------#
# Gemini 2.0 Flash
# response = requests.post(
#     "https://llmfoundry.straive.com/gemini/v1beta/openai/chat/completions",
#     headers={"Authorization": f"Bearer {os.environ['LLMFOUNDRY_TOKEN']}:my-test-project"},
#     json={"model": "gemini-1.5-flash-8b", "messages": [{"role": "user", "content": "What is 2 + 2"}]}
# )
# print(response.json())
#------------------------------------------------------------------------#
# gpt-4o
