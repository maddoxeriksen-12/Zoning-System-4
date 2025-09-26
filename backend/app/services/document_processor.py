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
from .requirements_processor import RequirementsProcessor
from ..models.document import Document
from ..core.config import settings
from ..models.document import client, create_document, get_document, update_document_status, start_document_processing, get_processing_stats

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Service for processing uploaded zoning documents"""

    def __init__(self):
        self.grok_service = GrokService()
        self.requirements_processor = RequirementsProcessor(client) if client else None
        self.upload_dir = Path("/app/uploads")  # Container path
        self.processed_dir = Path("/app/processed")  # Container path

        # Ensure directories exist
        self.upload_dir.mkdir(exist_ok=True)
        self.processed_dir.mkdir(exist_ok=True)

    def process_document(self, document_id: str, db) -> Dict[str, Any]:
        """
        Process a zoning document through the complete pipeline

        Args:
            document_id: UUID of the document to process
            db: Supabase client or SQLAlchemy session

        Returns:
            Processing result dictionary
        """
        try:
            # Get document from database
            if hasattr(db, 'table'):  # Supabase client
                document = get_document(document_id)
            else:  # SQLAlchemy
                document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return {
                    "success": False,
                    "error": f"Document {document_id} not found"
                }

            # Update status to processing
            if hasattr(db, 'table'):
                start_document_processing(document_id)
            else:
                db.execute(
                    text("SELECT public.start_document_processing(:doc_id)"),
                    {"doc_id": document_id}
                )
                db.commit()

            logger.info(f"Started processing document: {document['filename'] if isinstance(document, dict) else document.filename}")

            # Extract text from document
            if not document['file_path'] if isinstance(document, dict) else document.file_path or not os.path.exists(document['file_path'] if isinstance(document, dict) else document.file_path):
                error_msg = f"Document file not found: {document['file_path'] if isinstance(document, dict) else document.file_path}"
                self._update_document_status(db, document_id, "failed", error_message=error_msg)
                return {"success": False, "error": error_msg}

            file_path = document['file_path'] if isinstance(document, dict) else document.file_path
            text_content = self.grok_service.extract_text_from_document(file_path)
            if not text_content:
                error_msg = "Failed to extract text from document"
                self._update_document_status(db, document_id, "failed", error_message=error_msg)
                return {"success": False, "error": error_msg}

            # Process with Grok AI
            municipality = document['municipality'] if isinstance(document, dict) else document.municipality
            state = document['state'] if isinstance(document, dict) else document.state
            county = document.get('county', '') if isinstance(document, dict) else getattr(document, 'county', '')
            
            grok_result = self.grok_service.process_zoning_document(
                text_content,
                municipality=municipality,
                state=state,
                county=county
            )

            if grok_result["success"]:
                # Create job and process requirements if we have a requirements processor
                job_id = None
                requirement_ids = []
                
                if self.requirements_processor:
                    try:
                        # Prepare document data for job creation
                        doc_data = {
                            'municipality': municipality,
                            'county': county,
                            'state': state,
                            'filename': document['filename'] if isinstance(document, dict) else document.filename,
                            'original_filename': document.get('original_filename', '') if isinstance(document, dict) else getattr(document, 'original_filename', ''),
                            'file_path': file_path,
                            'file_size': document.get('file_size', 0) if isinstance(document, dict) else getattr(document, 'file_size', 0)
                        }
                        
                        # Create job
                        job_id = self.requirements_processor.create_job(doc_data)
                        
                        if job_id:
                            # Update job status to processing
                            self.requirements_processor.update_job_status(job_id, 'processing', self.grok_service.model)
                            
                            # Process and store requirements
                            requirement_ids = self.requirements_processor.process_grok_response(
                                job_id,
                                grok_result.get('grok_response'),
                                doc_data
                            )
                            
                            # Update job status based on requirements creation
                            if requirement_ids:
                                self.requirements_processor.update_job_status(job_id, 'completed', self.grok_service.model)
                                logger.info(f"Created {len(requirement_ids)} requirements for job {job_id}")
                            else:
                                self.requirements_processor.update_job_status(job_id, 'completed', self.grok_service.model)
                                logger.warning(f"No requirements extracted for job {job_id}")
                    
                    except Exception as e:
                        logger.error(f"Error processing requirements: {str(e)}")
                        if job_id:
                            self.requirements_processor.update_job_status(job_id, 'failed', self.grok_service.model)
                
                # Update document with successful processing result
                self._update_document_status(
                    db,
                    document_id,
                    "completed",
                    grok_response=grok_result["grok_response"]
                )

                # Move file to processed directory
                self._move_to_processed(file_path)

                logger.info(f"Successfully processed document: {document['filename'] if isinstance(document, dict) else document.filename}")
                return {
                    "success": True,
                    "document_id": document_id,
                    "job_id": job_id,
                    "requirement_ids": requirement_ids,
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

                logger.error(f"Failed to process document {document['filename'] if isinstance(document, dict) else document.filename}: {grok_result['error']}")
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
        db,
        document_id: str,
        status: str,
        grok_response: str = None,
        error_message: str = None
    ):
        """Update document processing status"""
        try:
            if hasattr(db, 'table'):  # Supabase client
                update_document_status(document_id, status, grok_response, error_message)
            else:  # SQLAlchemy
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
            if hasattr(db, 'rollback'):
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

    def get_processing_stats(self, db) -> Dict[str, Any]:
        """Get document processing statistics"""
        try:
            if hasattr(db, 'rpc'):  # Supabase client
                return get_processing_stats()
            else:  # SQLAlchemy fallback
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
                if hasattr(db, 'table'):  # Supabase
                    return get_processing_stats()
                else:  # SQLAlchemy
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
