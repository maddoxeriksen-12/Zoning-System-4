"""
Requirements API endpoints for zoning requirements data
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from ..core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_requirements(
    town: Optional[str] = Query(None, description="Filter by town/municipality"),
    county: Optional[str] = Query(None, description="Filter by county"),
    state: Optional[str] = Query(None, description="Filter by state"),
    zone: Optional[str] = Query(None, description="Filter by zone"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db=Depends(get_db)
):
    """
    Get zoning requirements with optional filters
    
    - **town**: Filter by town/municipality name
    - **county**: Filter by county name
    - **state**: Filter by state code
    - **zone**: Filter by zone code/name
    - **limit**: Maximum number of results (1-500)
    - **offset**: Offset for pagination
    """
    try:
        if hasattr(db, 'table'):  # Supabase client
            query = db.table('requirements').select('*')
            
            # Apply filters
            if town:
                query = query.ilike('town', f'%{town}%')
            if county:
                query = query.ilike('county', f'%{county}%')
            if state:
                query = query.eq('state', state)
            if zone:
                query = query.ilike('zone', f'%{zone}%')
            
            # Apply pagination
            query = query.range(offset, offset + limit - 1)
            
            # Execute query
            result = query.execute()
            
            return {
                "success": True,
                "data": result.data,
                "count": len(result.data),
                "offset": offset,
                "limit": limit
            }
        else:
            # SQLAlchemy fallback
            from sqlalchemy import text
            
            conditions = []
            params = {"limit": limit, "offset": offset}
            
            if town:
                conditions.append("town ILIKE :town")
                params["town"] = f"%{town}%"
            if county:
                conditions.append("county ILIKE :county")
                params["county"] = f"%{county}%"
            if state:
                conditions.append("state = :state")
                params["state"] = state
            if zone:
                conditions.append("zone ILIKE :zone")
                params["zone"] = f"%{zone}%"
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            query = text(f"""
                SELECT * FROM requirements
                WHERE {where_clause}
                ORDER BY town, zone
                LIMIT :limit OFFSET :offset
            """)
            
            result = db.execute(query, params)
            data = [dict(row) for row in result]
            
            return {
                "success": True,
                "data": data,
                "count": len(data),
                "offset": offset,
                "limit": limit
            }
            
    except Exception as e:
        logger.error(f"Error fetching requirements: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch requirements: {str(e)}")


@router.get("/by-location")
async def get_requirements_by_location(
    town: str = Query(..., description="Town/municipality name"),
    state: str = Query(..., description="State code"),
    county: Optional[str] = Query(None, description="County name"),
    db=Depends(get_db)
):
    """
    Get all zoning requirements for a specific location
    
    - **town**: Town/municipality name (required)
    - **state**: State code (required)
    - **county**: County name (optional)
    """
    try:
        if hasattr(db, 'table'):  # Supabase client
            query = db.table('requirements').select('*').eq('town', town).eq('state', state)
            
            if county:
                query = query.eq('county', county)
            
            result = query.execute()
            
            return {
                "success": True,
                "location": {
                    "town": town,
                    "county": county,
                    "state": state
                },
                "zones": result.data,
                "zone_count": len(result.data)
            }
        else:
            # SQLAlchemy fallback
            from sqlalchemy import text
            
            if county:
                query = text("""
                    SELECT * FROM requirements
                    WHERE town = :town AND state = :state AND county = :county
                    ORDER BY zone
                """)
                params = {"town": town, "state": state, "county": county}
            else:
                query = text("""
                    SELECT * FROM requirements
                    WHERE town = :town AND state = :state
                    ORDER BY zone
                """)
                params = {"town": town, "state": state}
            
            result = db.execute(query, params)
            data = [dict(row) for row in result]
            
            return {
                "success": True,
                "location": {
                    "town": town,
                    "county": county,
                    "state": state
                },
                "zones": data,
                "zone_count": len(data)
            }
            
    except Exception as e:
        logger.error(f"Error fetching requirements by location: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch requirements: {str(e)}")


@router.get("/zones")
async def get_unique_zones(
    town: Optional[str] = Query(None, description="Filter by town"),
    state: Optional[str] = Query(None, description="Filter by state"),
    db=Depends(get_db)
):
    """
    Get list of unique zones
    
    - **town**: Filter by town (optional)
    - **state**: Filter by state (optional)
    """
    try:
        if hasattr(db, 'table'):  # Supabase client
            query = db.table('requirements').select('zone, town, county, state')
            
            if town:
                query = query.eq('town', town)
            if state:
                query = query.eq('state', state)
            
            result = query.execute()
            
            # Group by unique zone names
            zones_dict = {}
            for row in result.data:
                zone = row['zone']
                if zone not in zones_dict:
                    zones_dict[zone] = []
                zones_dict[zone].append({
                    'town': row['town'],
                    'county': row['county'],
                    'state': row['state']
                })
            
            zones_list = [
                {
                    'zone': zone,
                    'locations': locations,
                    'location_count': len(locations)
                }
                for zone, locations in zones_dict.items()
            ]
            
            return {
                "success": True,
                "zones": zones_list,
                "total_zones": len(zones_list)
            }
        else:
            # SQLAlchemy fallback
            from sqlalchemy import text
            
            conditions = []
            params = {}
            
            if town:
                conditions.append("town = :town")
                params["town"] = town
            if state:
                conditions.append("state = :state")
                params["state"] = state
            
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            
            query = text(f"""
                SELECT DISTINCT zone, town, county, state
                FROM requirements
                {where_clause}
                ORDER BY zone
            """)
            
            result = db.execute(query, params)
            data = [dict(row) for row in result]
            
            # Group by unique zone names
            zones_dict = {}
            for row in data:
                zone = row['zone']
                if zone not in zones_dict:
                    zones_dict[zone] = []
                zones_dict[zone].append({
                    'town': row['town'],
                    'county': row['county'],
                    'state': row['state']
                })
            
            zones_list = [
                {
                    'zone': zone,
                    'locations': locations,
                    'location_count': len(locations)
                }
                for zone, locations in zones_dict.items()
            ]
            
            return {
                "success": True,
                "zones": zones_list,
                "total_zones": len(zones_list)
            }
            
    except Exception as e:
        logger.error(f"Error fetching zones: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch zones: {str(e)}")


@router.get("/jobs")
async def get_jobs(
    status: Optional[str] = Query(None, description="Filter by processing status"),
    town: Optional[str] = Query(None, description="Filter by town"),
    state: Optional[str] = Query(None, description="Filter by state"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db=Depends(get_db)
):
    """
    Get job records with optional filters
    
    - **status**: Filter by processing status (pending, processing, completed, failed)
    - **town**: Filter by town
    - **state**: Filter by state
    - **limit**: Maximum results
    - **offset**: Pagination offset
    """
    try:
        if hasattr(db, 'table'):  # Supabase client
            query = db.table('jobs').select('*')
            
            if status:
                query = query.eq('processing_status', status)
            if town:
                query = query.ilike('town', f'%{town}%')
            if state:
                query = query.eq('state', state)
            
            query = query.range(offset, offset + limit - 1).order('created_at', desc=True)
            
            result = query.execute()
            
            return {
                "success": True,
                "jobs": result.data,
                "count": len(result.data),
                "offset": offset,
                "limit": limit
            }
        else:
            # SQLAlchemy fallback
            from sqlalchemy import text
            
            conditions = []
            params = {"limit": limit, "offset": offset}
            
            if status:
                conditions.append("processing_status = :status")
                params["status"] = status
            if town:
                conditions.append("town ILIKE :town")
                params["town"] = f"%{town}%"
            if state:
                conditions.append("state = :state")
                params["state"] = state
            
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            
            query = text(f"""
                SELECT * FROM jobs
                {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """)
            
            result = db.execute(query, params)
            data = [dict(row) for row in result]
            
            return {
                "success": True,
                "jobs": data,
                "count": len(data),
                "offset": offset,
                "limit": limit
            }
            
    except Exception as e:
        logger.error(f"Error fetching jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch jobs: {str(e)}")


@router.get("/jobs/summary")
async def get_jobs_summary(db=Depends(get_db)):
    """Get summary statistics of all jobs"""
    try:
        if hasattr(db, 'rpc'):  # Supabase client
            result = db.rpc('get_jobs_summary').execute()
            
            if result.data and len(result.data) > 0:
                return {
                    "success": True,
                    "summary": result.data[0]
                }
            else:
                return {
                    "success": True,
                    "summary": {
                        "total_jobs": 0,
                        "pending_jobs": 0,
                        "processing_jobs": 0,
                        "completed_jobs": 0,
                        "failed_jobs": 0
                    }
                }
        else:
            # SQLAlchemy fallback
            from sqlalchemy import text
            
            query = text("""
                SELECT
                    COUNT(*) as total_jobs,
                    COUNT(*) FILTER (WHERE processing_status = 'pending') as pending_jobs,
                    COUNT(*) FILTER (WHERE processing_status = 'processing') as processing_jobs,
                    COUNT(*) FILTER (WHERE processing_status = 'completed') as completed_jobs,
                    COUNT(*) FILTER (WHERE processing_status = 'failed') as failed_jobs
                FROM jobs
            """)
            
            result = db.execute(query).fetchone()
            
            return {
                "success": True,
                "summary": {
                    "total_jobs": result.total_jobs or 0,
                    "pending_jobs": result.pending_jobs or 0,
                    "processing_jobs": result.processing_jobs or 0,
                    "completed_jobs": result.completed_jobs or 0,
                    "failed_jobs": result.failed_jobs or 0
                }
            }
            
    except Exception as e:
        logger.error(f"Error fetching jobs summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch jobs summary: {str(e)}")
