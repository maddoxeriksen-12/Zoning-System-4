"""
Database connection and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import text
import logging

from .config import settings
from .supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

# Supabase client (primary)
supabase_client = get_supabase_client()

# Always create Base for model definitions (even if using Supabase)
Base = declarative_base()

# Fallback SQLAlchemy engine (if no Supabase client)
if not supabase_client:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        echo=settings.DEBUG,
        pool_size=10,
        max_overflow=20,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    engine = None
    SessionLocal = None

def get_db():
    """Dependency to get database session or Supabase client"""
    if supabase_client:
        yield supabase_client
    else:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

def create_tables():
    """Create all database tables using Supabase client or fallback"""
    try:
        if supabase_client:
            # Supabase handles schema via migrations; verify by selecting from a table
            result = supabase_client.table('documents').select('id').limit(1).execute()
            logger.info("Supabase tables verified")
        else:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create/verify database tables: {e}")
        raise

def test_connection():
    """Test database connection using Supabase client or fallback"""
    try:
        if supabase_client:
            # Simple test - try to select from a table (will succeed even if empty)
            result = supabase_client.table('documents').select('id').limit(1).execute()
            logger.info("Supabase connection successful")
            return True
        else:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info("Database connection successful")
                return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

# Test connection on import
if __name__ != "__main__":
    test_connection()
