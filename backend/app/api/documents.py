"""
Documents API endpoints for zoning document processing
"""

import logging
import os
import uuid
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..core.database import get_db
from ..core.config import settings
from ..models.document import Document
from ..services.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

try:
    from ..models.document import create_document, get_documents, get_document
except Exception as e:
    logger.warning(f"Could not import document functions: {e}")
    create_document = None
    get_documents = None
    get_document = None

router = APIRouter()

# Lazy load processor to avoid import issues
def get_processor():
    from ..services.document_processor import DocumentProcessor
    return DocumentProcessor()

processor = None


@router.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "Documents API is working!"}

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    municipality: Optional[str] = Form(None),
    county: Optional[str] = Form(None),
    state: str = Form("NJ"),
    db = Depends(get_db)
):
    """
    Upload a zoning document for processing

    - **file**: The document file to upload (PDF, DOC, DOCX, TXT, etc.)
    - **municipality**: Municipality name (optional)
    - **state**: State code (default: NJ)
    """
    try:
        # Validate file type
        allowed_extensions = [ext.lstrip('.') for ext in settings.ALLOWED_FILE_TYPES]
        file_extension = Path(file.filename).suffix.lower().lstrip('.')

        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{file_extension}' not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )

        # Validate file size
        file_content = await file.read()
        file_size = len(file_content)

        if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB"
            )

        # Generate unique filename
        original_filename = file.filename
        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
        file_path = Path("/app/uploads") / unique_filename

        # Ensure upload directory exists
        file_path.parent.mkdir(exist_ok=True)

        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)

            # Create document record in database
            document_data = {
                'filename': unique_filename,
                'original_filename': original_filename,
                'file_path': str(file_path),
                'file_size': file_size,
                'mime_type': file.content_type,
                'municipality': municipality,
                'county': county,
                'state': state,
                'processing_status': 'uploaded'
            }

        if hasattr(db, 'table'):  # Supabase client
            document = create_document(document_data)
            document_id = document['id']
        else:  # SQLAlchemy
            document = Document(**document_data)
            db.add(document)
            db.commit()
            db.refresh(document)
            document_id = str(document.id)

        # Start background processing
        background_tasks.add_task(process_document_background, document_id, db)

        logger.info(f"Document uploaded successfully: {original_filename} (ID: {document_id})")

        return {
            "success": True,
            "document_id": document_id,
            "message": f"Document '{original_filename}' uploaded successfully. Processing started.",
            "filename": unique_filename,
            "size": file_size,
            "municipality": municipality,
            "county": county,
            "state": state,
            "status": "uploaded"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


async def process_document_background(document_id: str, db):
    """Background task to process uploaded document"""
    try:
        logger.info(f"Starting background processing for document: {document_id}")

        # Get processor instance
        processor = get_processor()
        result = processor.process_document(document_id, db)

        if result["success"]:
            logger.info(f"Background processing completed for document: {document_id}")
        else:
            logger.error(f"Background processing failed for document {document_id}: {result.get('error')}")

    except Exception as e:
        logger.error(f"Background processing error for document {document_id}: {str(e)}")


@router.get("/")
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    municipality: Optional[str] = None,
    db = Depends(get_db)
):
    """List uploaded documents with optional filtering"""
    try:
        if hasattr(db, 'table'):  # Supabase client
            documents = get_documents(limit=limit, offset=skip, status=status, municipality=municipality)
            total = client.table('documents').select('count', count='exact').execute().count
        else:  # SQLAlchemy
            query = db.query(Document)

            if status:
                query = query.filter(Document.processing_status == status)
            if municipality:
                query = query.filter(Document.municipality.ilike(f"%{municipality}%"))

            documents = query.offset(skip).limit(limit).all()
            total = query.count()

        return {
            "documents": [
                {
                    "id": str(doc['id']) if isinstance(doc, dict) else str(doc.id),
                    "filename": doc['filename'] if isinstance(doc, dict) else doc.filename,
                    "original_filename": doc['original_filename'] if isinstance(doc, dict) else doc.original_filename,
                    "municipality": doc['municipality'] if isinstance(doc, dict) else doc.municipality,
                    "state": doc['state'] if isinstance(doc, dict) else doc.state,
                    "file_size": doc['file_size'] if isinstance(doc, dict) else doc.file_size,
                    "processing_status": doc['processing_status'] if isinstance(doc, dict) else doc.processing_status,
                    "upload_date": doc['upload_date'].isoformat() if isinstance(doc, dict) and doc['upload_date'] else (doc.upload_date.isoformat() if doc.upload_date else None),
                    "processing_started_at": doc['processing_started_at'].isoformat() if isinstance(doc, dict) and doc['processing_started_at'] else (doc.processing_started_at.isoformat() if doc.processing_started_at else None),
                    "processing_completed_at": doc['processing_completed_at'].isoformat() if isinstance(doc, dict) and doc['processing_completed_at'] else (doc.processing_completed_at.isoformat() if doc.processing_completed_at else None),
                }
                for doc in documents
            ],
            "total": total,
            "skip": skip,
            "limit": limit
        }

    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.get("/{document_id}")
async def get_document(document_id: str, db = Depends(get_db)):
    """Get document details by ID"""
    try:
        if hasattr(db, 'table'):  # Supabase client
            document = get_document(document_id)
        else:  # SQLAlchemy
            document = db.query(Document).filter(Document.id == document_id).first()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if isinstance(document, dict):
            return {
                "id": document['id'],
                "filename": document['filename'],
                "original_filename": document['original_filename'],
                "file_path": document['file_path'],
                "file_size": document['file_size'],
                "mime_type": document['mime_type'],
                "municipality": document['municipality'],
                "state": document['state'],
                "processing_status": document['processing_status'],
                "upload_date": document['upload_date'].isoformat() if document['upload_date'] else None,
                "processing_started_at": document['processing_started_at'].isoformat() if document['processing_started_at'] else None,
                "processing_completed_at": document['processing_completed_at'].isoformat() if document['processing_completed_at'] else None,
                "grok_response": document['grok_response'],
                "error_message": document['error_message'],
                "created_at": document['created_at'].isoformat() if document['created_at'] else None,
                "updated_at": document['updated_at'].isoformat() if document['updated_at'] else None,
            }
        else:
            return {
                "id": str(document.id),
                "filename": document.filename,
                "original_filename": document.original_filename,
                "file_path": document.file_path,
                "file_size": document.file_size,
                "mime_type": document.mime_type,
                "municipality": document.municipality,
                "state": document.state,
                "processing_status": document.processing_status,
                "upload_date": document.upload_date.isoformat() if document.upload_date else None,
                "processing_started_at": document.processing_started_at.isoformat() if document.processing_started_at else None,
                "processing_completed_at": document.processing_completed_at.isoformat() if document.processing_completed_at else None,
                "grok_response": document.grok_response,
                "error_message": document.error_message,
                "created_at": document.created_at.isoformat() if document.created_at else None,
                "updated_at": document.updated_at.isoformat() if document.updated_at else None,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@router.get("/stats/summary")
async def get_processing_stats(db = Depends(get_db)):
    """Get document processing statistics"""
    try:
        processor = get_processor()
        stats = processor.get_processing_stats(db)
        return {
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting processing stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
