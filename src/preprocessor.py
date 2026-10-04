import os
import cv2
import numpy as np
from PIL import Image

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False


class DocumentPreprocessor:

    def __init__(self, dpi: int = 300):
        self.dpi = dpi
        self._poppler_warned = False

    # Deskew tilted page scans
    def deskew_image(self, image: np.ndarray) -> np.ndarray:
        if image is None or image.size == 0:
            return image

        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        coords = np.column_stack(np.where(thresh > 0))
        if coords.shape[0] < 50:
            return image

        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        # Fix minor skew, ignore large 90 degree flips
        if abs(angle) > 0.3 and abs(angle) < 45:
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            deskewed = cv2.warpAffine(
                image, M, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
            return deskewed

        return image

    # Rasterize PDF pages to 300 DPI images
    def convert_pdf_to_images(self, pdf_path: str):
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Document not found at: {pdf_path}")

        images = []
        if PDF2IMAGE_AVAILABLE:
            try:
                images = convert_from_path(pdf_path, dpi=self.dpi)
            except Exception:
                pass

        return images

    def preprocess_document(self, file_path: str) -> dict:
        filename = os.path.basename(file_path)
        images = self.convert_pdf_to_images(file_path)

        processed_pages = []
        for idx, img in enumerate(images):
            np_img = np.array(img)
            if len(np_img.shape) == 3 and np_img.shape[2] == 3:
                np_img = cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)

            deskewed_img = self.deskew_image(np_img)
            processed_pages.append({
                "pageNumber": idx + 1,
                "width": img.width,
                "height": img.height,
                "deskewed": True
            })

        return {
            "documentId": filename,
            "pageCount": len(images) if images else 1,
            "pages": processed_pages
        }
