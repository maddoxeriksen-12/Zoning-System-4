"""
Grok AI Service for document processing
"""

import logging
import requests
from typing import Optional, Dict, Any
from datetime import datetime

from ..core.config import settings

logger = logging.getLogger(__name__)


class GrokService:
    """Service for interacting with Grok AI API"""

    def __init__(self):
        self.api_key = settings.GROK_API_KEY
        self.base_url = settings.GROK_BASE_URL
        self.model = settings.GROK_MODEL
        self.max_tokens = settings.GROK_MAX_TOKENS
        self.temperature = settings.GROK_TEMPERATURE

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def process_zoning_document(self, text_content: str, municipality: str = None, state: str = "NJ") -> Dict[str, Any]:
        """
        Process zoning document text using Grok AI

        Args:
            text_content: Extracted text from the document
            municipality: Municipality name if available
            state: State code (default: NJ)

        Returns:
            Dict containing processed zoning information
        """
        try:
            location_info = f" for {municipality}, {state}" if municipality else f" for {state}"

            prompt = f"""
            You are an expert zoning and land use analyst. Analyze the following zoning document text{location_info} and extract key information.

            Document Text:
            {text_content[:10000]}  # Limit text length for API

            Please provide a structured analysis including:

            1. **Zoning Districts**: List all zoning districts mentioned and their primary uses
            2. **Key Regulations**: Important zoning regulations, setbacks, height limits, density requirements
            3. **Permitted Uses**: Main permitted uses by district
            4. **Special Provisions**: Any special zoning provisions, overlays, or exceptions
            5. **Summary**: Brief summary of the zoning ordinance

            Format your response as a JSON object with these keys: zoning_districts, key_regulations, permitted_uses, special_provisions, summary
            """

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
                timeout=settings.AI_PROCESSING_TIMEOUT
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

                logger.info(f"Successfully processed document with Grok AI")
                return {
                    "success": True,
                    "processed_at": datetime.utcnow().isoformat(),
                    "grok_response": content,
                    "model": self.model,
                    "tokens_used": result.get("usage", {}).get("total_tokens")
                }
            else:
                error_msg = f"Grok API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "processed_at": datetime.utcnow().isoformat()
                }

        except requests.exceptions.Timeout:
            error_msg = "Grok API request timed out"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "processed_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            error_msg = f"Error processing document with Grok: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "processed_at": datetime.utcnow().isoformat()
            }

    def extract_text_from_document(self, file_path: str) -> Optional[str]:
        """
        Extract text content from various document formats
        This is a basic implementation - you may want to enhance with better OCR/PDF parsing

        Args:
            file_path: Path to the document file

        Returns:
            Extracted text content or None if extraction fails
        """
        try:
            file_extension = file_path.lower().split('.')[-1]

            if file_extension == 'pdf':
                # Basic PDF text extraction (you may want to use PyPDF2 or pdfplumber)
                import PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages[:10]:  # Limit to first 10 pages
                        text += page.extract_text() + "\n"
                    return text

            elif file_extension in ['docx']:
                # Basic DOCX text extraction
                from docx import Document
                doc = Document(file_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text

            elif file_extension in ['txt']:
                # Plain text
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read()

            else:
                logger.warning(f"Unsupported file type: {file_extension}")
                return None

        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            return None
