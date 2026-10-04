# Invoice Extraction Pipeline

An automated invoice extraction pipeline designed to process and extract structured data from various invoice formats—including  digital PDFs, scanned documents, handwritten receipts, and multilingual invoices (English, Vietnamese, and Chinese).

The system uses a 3-stage modular pipeline: image preprocessing & deskewing, cloud/heuristic layout extraction, and a validation rule gate that flags low-confidence or missing fields for human review.

---

## 1. Tech Stack

- `google-cloud-documentai`: Primary cloud extraction engine for document OCR, entity recognition, and pixel bounding box extraction.
- `pdf2image`: Converts single and multi-page PDFs into standardized 300 DPI image buffers.
- `opencv-python`: Image deskewing using Otsu thresholding and contour-based min-area rectangle rotation.
- `os` & `json`: Python standard library modules for folder traversal across document categories and structured JSON serializations.

---

## 2. Directory Structure

```text
Neoflo.ai-Invoice-Pipeline/
│
├── data/
│   ├── digital/                    # Digital PDFs (clean vector text)
│   ├── scanned/                    # Scanned flatbed/photo PDFs
│   ├── handwritten/                # Handwritten service receipts
│   ├── multilingual/               # International invoices (Chinese, Vietnamese)
│   └── ground_truth_benchmark.json # Reference dataset used for testing & SLA audit
│
├── src/
│   ├── __init__.py
│   ├── preprocessor.py             # Stage 1: PDF to image conversion & deskewing
│   ├── extractor.py                # Stage 2: Document AI & dynamic layout extraction
│   └── validator.py                # Stage 3: Mandatory field validation & confidence checks
│
├── main.py                         # Pipeline runner script
├── requirements.txt                # Project dependencies
├── final_extracted_invoices.json   # Final extracted JSON output
└── README.md                       # Project documentation
```

## 3. Pipeline Architecture

Each invoice goes through three simple steps:

```text
     Invoice PDF
          │
          ▼
    Preprocessing (Deskew, DPI Normalization)
          │
          ▼
    Extraction (Document AI / Fallback OCR)
          │
          ▼
    Validation (Math cross-checks & Review flags)
          │
          ▼
     JSON Output
```


### Stage 1: Preprocessing

- Converts PDF pages into 300 DPI images.
- Detects tilted pages and corrects them using OpenCV.
- Prepares the pages for extraction.

### Stage 2: Extraction

- Uses Google Cloud Document AI for invoice extraction.
- Extracts invoice fields and their locations.
- Uses a local fallback parser when needed.

### Stage 3: Validation

- Checks the required invoice fields.
- Flags missing fields as `FIELD_MISSING`.
- Flags confidence below `0.85` as `LOW_CONFIDENCE`.
- Sends uncertain results for manual review.


## 4. Output JSON Schema

The extracted results are saved in `final_extracted_invoices.json`.

Each invoice contains the extracted fields along with their location and review status.

```json
{
  "documentId": "digital_01.pdf",
  "invoice": {
    "invoiceNumber": {
      "value": "CSOS 202602-931",
      "bbox": {
        "page": 1,
        "x1": 818,
        "y1": 135,
        "x2": 910,
        "y2": 147
      },
      "isHumanReviewRequired": false,
      "reviewReasons": []
    },
    "invoiceDate": {
      "value": "02ND FEB 2026",
      "bbox": {
        "page": 1,
        "x1": 850,
        "y1": 154,
        "x2": 975,
        "y2": 166
      },
      "isHumanReviewRequired": false,
      "reviewReasons": []
    },
    "supplierName": {
      "value": "CRESTLINE STAFFING AND OUTSOURCING SOLUTIONS SDN BHD"
    },
    "buyerName": {
      "value": "Jade Eservices Malaysia Sdn. Bhd."
    },
    "currency": {
      "value": "MYR"
    },
    "totalAmount": {
      "value": 13764.48
    }
  },
  "lineItems": [
    {
      "description": {
        "value": "Cost of Labor"
      },
      "lineAmount": {
        "value": 11733.10
      }
    }
  ],
  "isHumanReviewRequired": false,
  "reviewReasons": []
}

```



## 5. Evaluation Results

I tested the pipeline on 13 invoices covering different document types.

# Test Dataset

- Digital invoices: 3
- Scanned invoices: 3
- Handwritten invoices: 4
- Multilingual invoices: 3

# Results

- Total invoices processed: 13
- Total fields extracted: 487
- Fields flagged for review: 71
- Mandatory fields checked: 78
- Invoices sent for manual review: 4
- Missed-review rate: 0.00%

The four handwritten invoices were sent for manual review because some of their extracted fields had lower confidence scores.

The digital scanned and multilingual invoices generally had higher OCR confidence and passed the validation checks.

# Review Routing

Digital invoices scanned invoices and multilingual invoices had good OCR clarity and passed the validation checks.

The handwritten invoices had more variation in handwriting and lower confidence scores. These invoices were flagged with `LOW_CONFIDENCE` and sent for manual verification.

The pipeline does not automatically accept low-confidence results. Instead it flags them for review before the extracted data is used.


## 6. How to Run

Follow these quick steps on Windows:

### 1. Clone & Open the Project
```bash
git clone https://github.com/shubh5666/Neoflo.ai-Invoice-Pipeline.git
cd Neoflo.ai-Invoice-Pipeline
```

### 2. Set Up Virtual Environment (Optional / Recommended)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Pipeline
```bash
python main.py
```

The pipeline will process all test invoices and generate the final output in:
- `final_extracted_invoices.json`

---

### Optional: Google Cloud Document AI Setup

To route processing through Google Cloud Document AI (instead of the local layout engine), set your credentials in PowerShell:

```powershell
$env:GCP_PROJECT_ID="your-project-id"
$env:DOCUMENTAI_PROCESSOR_ID="your-processor-id"
$env:GOOGLE_APPLICATION_CREDENTIALS="path\to\service_account.json"
python main.py
```