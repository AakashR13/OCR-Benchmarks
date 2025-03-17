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
    - OmniAi            - Verification Issue
    - Gemini 2.0 Flash  - Image Conversion
    - Azure             - Works
    - GPT-4o            - Image Conversion
    - AWS Textract      - Account Issue
    - Mistral OCR       - Works

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
