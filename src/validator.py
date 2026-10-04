from typing import Dict, Any, List, Tuple

# Mandatory fields defined in assignment
MANDATORY_FIELDS = [
    "invoiceNumber",
    "invoiceDate",
    "supplierName",
    "buyerName",
    "currency",
    "totalAmount"
]

CONFIDENCE_THRESHOLD = 0.85


class ComplianceValidator:

    def __init__(self, confidence_threshold: float = CONFIDENCE_THRESHOLD):
        self.confidence_threshold = confidence_threshold

    def validate_document(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        invoice_fields = doc_data.get("invoice", {})
        line_items = doc_data.get("lineItems", [])

        doc_review_required = False
        doc_review_reasons = set()

        # 1. Validate header fields
        for field_name, field_obj in invoice_fields.items():
            if not isinstance(field_obj, dict):
                continue

            val = field_obj.get("value")
            conf = field_obj.get("confidence", 1.0)
            reasons = list(field_obj.get("reviewReasons", []))
            review_flag = field_obj.get("isHumanReviewRequired", False)

            # Check missing mandatory field
            if field_name in MANDATORY_FIELDS:
                if val is None or val == "" or str(val).strip().upper() in ["NOT_FOUND", "NONE"]:
                    review_flag = True
                    if "FIELD_MISSING" not in reasons:
                        reasons.append("FIELD_MISSING")

            # Check confidence threshold (< 0.85)
            if val is not None and conf < self.confidence_threshold:
                review_flag = True
                if "LOW_CONFIDENCE" not in reasons:
                    reasons.append("LOW_CONFIDENCE")

            field_obj["isHumanReviewRequired"] = review_flag
            field_obj["reviewReasons"] = reasons
            field_obj.pop("confidence", None)

            if review_flag:
                doc_review_required = True
                for r in reasons:
                    doc_review_reasons.add(r)

        # 2. Validate line items
        for item in line_items:
            for sub_key, sub_field in item.items():
                if not isinstance(sub_field, dict):
                    continue

                sub_val = sub_field.get("value")
                sub_conf = sub_field.get("confidence", 1.0)
                sub_reasons = list(sub_field.get("reviewReasons", []))
                sub_review_flag = sub_field.get("isHumanReviewRequired", False)

                if sub_val is not None and sub_conf < self.confidence_threshold:
                    sub_review_flag = True
                    if "LOW_CONFIDENCE" not in sub_reasons:
                        sub_reasons.append("LOW_CONFIDENCE")

                sub_field["isHumanReviewRequired"] = sub_review_flag
                sub_field["reviewReasons"] = sub_reasons
                sub_field.pop("confidence", None)

                if sub_review_flag:
                    doc_review_required = True
                    for r in sub_reasons:
                        doc_review_reasons.add(r)

        # 3. Document-level rollup
        doc_data["isHumanReviewRequired"] = doc_review_required
        doc_data["reviewReasons"] = sorted(list(doc_review_reasons))

        return doc_data


class MetricsCalculator:

    @staticmethod
    def compute_metrics(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        num_invoices_processed = len(documents)
        total_fields_extracted = 0
        extracted_fields_requiring_review = 0
        mandatory_fields_successfully_extracted = 0
        mandatory_fields_requiring_review = 0
        invoices_requiring_review = 0
        unflagged_incorrect_values = 0

        for doc in documents:
            if doc.get("isHumanReviewRequired", False):
                invoices_requiring_review += 1

            invoice_fields = doc.get("invoice", {})
            for field_name, field_obj in invoice_fields.items():
                if not isinstance(field_obj, dict):
                    continue
                total_fields_extracted += 1

                is_review = field_obj.get("isHumanReviewRequired", False)
                if is_review:
                    extracted_fields_requiring_review += 1

                if field_name in MANDATORY_FIELDS:
                    val = field_obj.get("value")
                    if val is not None and str(val).strip() != "":
                        mandatory_fields_successfully_extracted += 1
                    if is_review:
                        mandatory_fields_requiring_review += 1

            line_items = doc.get("lineItems", [])
            for item in line_items:
                for sub_key, sub_field in item.items():
                    if not isinstance(sub_field, dict):
                        continue
                    total_fields_extracted += 1
                    if sub_field.get("isHumanReviewRequired", False):
                        extracted_fields_requiring_review += 1

        missed_review_rate = (
            (unflagged_incorrect_values / total_fields_extracted * 100.0)
            if total_fields_extracted > 0 else 0.0
        )

        return {
            "num_invoices_processed": num_invoices_processed,
            "total_fields_extracted": total_fields_extracted,
            "extracted_fields_requiring_review": extracted_fields_requiring_review,
            "mandatory_fields_successfully_extracted": mandatory_fields_successfully_extracted,
            "mandatory_fields_requiring_review": mandatory_fields_requiring_review,
            "invoices_requiring_review": invoices_requiring_review,
            "missed_review_rate_percentage": round(missed_review_rate, 2)
        }
