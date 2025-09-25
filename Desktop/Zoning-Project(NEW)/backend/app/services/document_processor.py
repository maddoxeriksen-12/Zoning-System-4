"""
Document processing service for zoning documents
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import text

from .grok_service import GrokService
from ..models.document import Document
from ..core.config import settings

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Service for processing uploaded zoning documents"""

    def __init__(self):
        self.grok_service = GrokService()
        self.upload_dir = Path("/app/uploads")  # Container path
        self.processed_dir = Path("/app/processed")  # Container path

        # Ensure directories exist
        self.upload_dir.mkdir(exist_ok=True)
        self.processed_dir.mkdir(exist_ok=True)

    def process_document(self, document_id: str, db: Session) -> Dict[str, Any]:
        """
        Process a zoning document through the complete pipeline

        Args:
            document_id: UUID of the document to process
            db: Database session

        Returns:
            Processing result dictionary
        """
        try:
            # Get document from database
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return {
                    "success": False,
                    "error": f"Document {document_id} not found"
                }

            # Update status to processing
            db.execute(
                text("SELECT public.start_document_processing(:doc_id)"),
                {"doc_id": document_id}
            )
            db.commit()

            logger.info(f"Started processing document: {document.filename}")

            # Extract text from document
            if not document.file_path or not os.path.exists(document.file_path):
                error_msg = f"Document file not found: {document.file_path}"
                self._update_document_status(db, document_id, "failed", error_message=error_msg)
                return {"success": False, "error": error_msg}

            text_content = self.grok_service.extract_text_from_document(document.file_path)
            if not text_content:
                error_msg = "Failed to extract text from document"
                self._update_document_status(db, document_id, "failed", error_message=error_msg)
                return {"success": False, "error": error_msg}

            # Process with Grok AI
            grok_result = self.grok_service.process_zoning_document(
                text_content,
                municipality=document.municipality,
                state=document.state
            )

            if grok_result["success"]:
                # Update document with successful processing result
                self._update_document_status(
                    db,
                    document_id,
                    "completed",
                    grok_response=grok_result["grok_response"]
                )

                # Move file to processed directory
                self._move_to_processed(document.file_path)

                logger.info(f"Successfully processed document: {document.filename}")
                return {
                    "success": True,
                    "document_id": document_id,
                    "grok_response": grok_result["grok_response"],
                    "processed_at": grok_result["processed_at"]
                }
            else:
                # Update document with processing failure
                self._update_document_status(
                    db,
                    document_id,
                    "failed",
                    error_message=grok_result["error"]
                )

                logger.error(f"Failed to process document {document.filename}: {grok_result['error']}")
                return {
                    "success": False,
                    "error": grok_result["error"],
                    "document_id": document_id
                }

        except Exception as e:
            error_msg = f"Unexpected error processing document: {str(e)}"
            logger.error(error_msg)
            try:
                self._update_document_status(db, document_id, "failed", error_message=error_msg)
            except Exception:
                pass  # Ignore errors when updating status
            return {"success": False, "error": error_msg}

    def _update_document_status(
        self,
        db: Session,
        document_id: str,
        status: str,
        grok_response: str = None,
        error_message: str = None
    ):
        """Update document processing status"""
        try:
            db.execute(
                text("SELECT public.update_document_status(:doc_id, :status, :grok_response, :error_message)"),
                {
                    "doc_id": document_id,
                    "status": status,
                    "grok_response": grok_response,
                    "error_message": error_message
                }
            )
            db.commit()
        except Exception as e:
            logger.error(f"Failed to update document status: {str(e)}")
            db.rollback()

    def _move_to_processed(self, file_path: str):
        """Move processed file to processed directory"""
        try:
            file_path = Path(file_path)
            if file_path.exists():
                processed_path = self.processed_dir / file_path.name
                file_path.rename(processed_path)
                logger.info(f"Moved {file_path.name} to processed directory")
        except Exception as e:
            logger.error(f"Failed to move file to processed directory: {str(e)}")

    def get_processing_stats(self, db: Session) -> Dict[str, Any]:
        """Get document processing statistics"""
        try:
            # First try the database function
            result = db.execute(text("SELECT * FROM public.get_document_stats()")).fetchone()
            return {
                "total_documents": result.total_documents,
                "processed_documents": result.processed_documents,
                "failed_documents": result.failed_documents,
                "total_size": int(result.total_size or 0)
            }
        except Exception as e:
            logger.error(f"Failed to get processing stats from function: {str(e)}")
            # Fallback: count documents directly
            try:
                total = db.query(Document).count()
                completed = db.query(Document).filter(Document.processing_status == 'completed').count()
                failed = db.query(Document).filter(Document.processing_status == 'failed').count()
                total_size = db.query(Document.file_size).filter(Document.file_size.isnot(None)).all()
                size_sum = sum(size[0] for size in total_size) if total_size else 0

                return {
                    "total_documents": total,
                    "processed_documents": completed,
                    "failed_documents": failed,
                    "total_size": size_sum
                }
            except Exception as e2:
                logger.error(f"Failed to get processing stats directly: {str(e2)}")
                return {
                    "total_documents": 0,
                    "processed_documents": 0,
                    "failed_documents": 0,
                    "total_size": 0
                }
