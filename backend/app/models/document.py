"""
Document model for zoning documents
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, Text, BigInteger, UUID
from sqlalchemy.sql import func
import uuid

from ..core.database import Base


class Document(Base):
    """Document model for uploaded zoning documents"""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    mime_type = Column(String(100), nullable=True)
    municipality = Column(String(255), nullable=True)
    state = Column(String(50), default="NJ")
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    processing_status = Column(String(50), default="uploaded")  # uploaded, processing, completed, failed
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    grok_response = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.processing_status}')>"

# Supabase client operations for Document
from ..core.supabase_client import get_supabase_client
from uuid import uuid4
from datetime import datetime

client = get_supabase_client()

def create_document(data: dict) -> dict:
    """Create a new document record"""
    if not client:
        raise Exception("Supabase client not initialized")
    data['id'] = str(uuid4())
    data['upload_date'] = datetime.utcnow().isoformat()
    data['created_at'] = datetime.utcnow().isoformat()
    data['updated_at'] = datetime.utcnow().isoformat()
    data['processing_status'] = data.get('processing_status', 'uploaded')
    data['state'] = data.get('state', 'NJ')
    result = client.table('documents').insert(data).execute()
    return result.data[0] if result.data else None

def get_document(document_id: str) -> dict:
    """Get document by ID"""
    result = client.table('documents').select('*').eq('id', document_id).execute()
    return result.data[0] if result.data else None

def update_document_status(document_id: str, status: str, grok_response: str = None, error_message: str = None):
    """Update document processing status"""
    update_data = {'processing_status': status, 'updated_at': datetime.utcnow().isoformat()}
    if grok_response:
        update_data['grok_response'] = grok_response
        update_data['processing_completed_at'] = datetime.utcnow().isoformat()
    if error_message:
        update_data['error_message'] = error_message
        update_data['processing_completed_at'] = datetime.utcnow().isoformat() if status == 'failed' else None
    result = client.table('documents').update(update_data).eq('id', document_id).execute()
    return result.data[0] if result.data else None

def start_document_processing(document_id: str):
    """Start document processing"""
    update_data = {'processing_status': 'processing', 'processing_started_at': datetime.utcnow().isoformat(), 'updated_at': datetime.utcnow().isoformat()}
    result = client.table('documents').update(update_data).eq('id', document_id).execute()
    return result.data[0] if result.data else None

def get_documents(limit: int = 100, offset: int = 0, status: str = None, municipality: str = None):
    """Get list of documents with filters"""
    query = client.table('documents').select('*').range(offset, offset + limit - 1)
    if status:
        query = query.eq('processing_status', status)
    if municipality:
        query = query.ilike('municipality', f'%{municipality}%')
    result = query.execute()
    return result.data

def get_processing_stats():
    """Get document processing statistics using RPC or direct query"""
    try:
        result = client.rpc('get_document_stats').execute()
        return result.data[0] if result.data else {'total_documents': 0, 'processed_documents': 0, 'failed_documents': 0, 'total_size': 0}
    except:
        # Fallback query
        total = client.table('documents').select('count').execute()
        completed = client.table('documents').select('count').eq('processing_status', 'completed').execute()
        failed = client.table('documents').select('count').eq('processing_status', 'failed').execute()
        return {
            'total_documents': total.count,
            'processed_documents': completed.count,
            'failed_documents': failed.count,
            'total_size': 0  # Calculate if needed
        }
