import os
import json
import glob
from pathlib import Path
from src.preprocessor import DocumentPreprocessor
from src.extractor import InvoiceExtractor
from src.validator import ComplianceValidator, MetricsCalculator
import sys

# UTF-8 encoding for Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_pipeline():
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"
    output_file = base_dir / "final_extracted_invoices.json"

    print("\n--- INVOICE EXTRACTION PIPELINE ---\n")

    preprocessor = DocumentPreprocessor(dpi=300)
    extractor = InvoiceExtractor()
    validator = ComplianceValidator(confidence_threshold=0.85)

    # Load invoices across all test categories
    categories = ["digital", "scanned", "handwritten", "multilingual"]
    all_files = []
    for cat in categories:
        cat_path = data_dir / cat
        if cat_path.exists():
            files = sorted(list(cat_path.glob("*.pdf")))
            all_files.extend(files)

    if not all_files:
        print("[Error] No PDF files found in data/ directories.")
        return

    print(f"Processing {len(all_files)} invoices across categories: {', '.join(categories)}\n")
    print(f"  #   {'Category':<13} {'Document File':<36} Status")
    print("  " + "-" * 76)

    processed_documents = []

    for idx, file_path in enumerate(all_files, 1):
        filename = file_path.name
        rel_cat = file_path.parent.name.capitalize()

        # 3-step pipeline: preprocess -> extract -> validate
        prep_meta = preprocessor.preprocess_document(str(file_path))
        extracted_doc = extractor.extract(str(file_path))
        validated_doc = validator.validate_document(extracted_doc)

        is_review = validated_doc["isHumanReviewRequired"]
        if is_review:
            status_tag = "REVIEW (Low Confidence)"
        else:
            status_tag = "PASSED"

        print(f" {idx:02d}   {rel_cat:<13} {filename:<36} {status_tag}")
        processed_documents.append(validated_doc)

    print("  " + "-" * 76)

    # Save extracted output
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(processed_documents, f, indent=2, ensure_ascii=False)

    print(f"\nOutput successfully written to: {output_file.name}")

    # Compute summary metrics
    metrics = MetricsCalculator.compute_metrics(processed_documents)

    print("\n--- QUANTITATIVE EVALUATION METRICS REPORT ---")
    print(f"Number of invoices processed: {metrics['num_invoices_processed']}")
    print(f"Total number of fields extracted: {metrics['total_fields_extracted']}")
    print(f"Number of extracted fields requiring human review: {metrics['extracted_fields_requiring_review']}")
    print(f"Number of mandatory fields successfully extracted: {metrics['mandatory_fields_successfully_extracted']}")
    print(f"Number of mandatory fields requiring human review: {metrics['mandatory_fields_requiring_review']}")
    print(f"Number of invoices requiring human review: {metrics['invoices_requiring_review']}")
    print(f"Percentage of extracted values that were incorrect but were not flagged for human review: {metrics['missed_review_rate_percentage']:.2f}%\n")

    return metrics


if __name__ == "__main__":
    run_pipeline()
