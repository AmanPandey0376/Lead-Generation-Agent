import json
import io
import logging
import pandas as pd
import asyncio
from typing import Optional, List
from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import StreamingResponse

from backend.models.lead_models import (
    LeadsRequest, GenerateLeadsInput
)
import backend.services.database as db_service
from backend.services.product_analyzer import analyze_product
from backend.services.company_discovery import discover_companies
from backend.services.lead_extractor import extract_leads
from backend.services.lead_enricher import enrich_leads
from backend.services.lead_validator import validate_leads

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/api/product-service-types")
async def get_product_service_types(category: Optional[str] = Query(None)):
    """
    Returns product service types optionally filtered by category.
    """
    try:
        types = await db_service.get_product_service_types(category)
        return {"types": types}
    except Exception as e:
        logger.error(f"Failed to fetch product service types: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch types")


@router.get("/api/product-service-names")
async def get_product_service_names(typeId: int, category: str):
    """
    Returns product service names for a given type and category.
    """
    try:
        names = await db_service.get_product_service_names(typeId, category)
        return {"names": names}
    except Exception as e:
        logger.error(f"Failed to fetch product service names: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch names")


@router.post("/api/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """
    Uploads and parses an Excel file containing product listings.
    """
    try:
        contents = await file.read()
        # Read Excel spreadsheet using pandas
        df = pd.read_excel(io.BytesIO(contents))
        
        products = []
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            product_name = row_dict.get('post_title') or row_dict.get('product_name') or row_dict.get('Name') or ""
            sku = row_dict.get('SKU') or row_dict.get('sku') or ""
            brand = row_dict.get('Brand') or row_dict.get('brand') or ""
            
            # Handle potential NaN values from pandas
            if pd.isna(product_name): product_name = ""
            if pd.isna(sku): sku = ""
            if pd.isna(brand): brand = ""
            
            product_name = str(product_name).strip()
            sku = str(sku).strip()
            brand = str(brand).strip()
            
            if product_name:
                products.append({
                    "product_name": product_name,
                    "sku": sku,
                    "brand": brand
                })
                
        return {"products": products}
    except Exception as e:
        logger.error(f"Error processing uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Failed to process Excel file")


@router.post("/api/filter-existing-leads")
async def filter_existing_leads(request: LeadsRequest):
    """
    Filters out leads that already exist in the database.
    """
    try:
        # Convert pydantic models to dictionaries
        leads_dict = [l.model_dump(by_alias=True) for l in request.leads]
        unique_leads = await db_service.filter_existing_leads(leads_dict)
        return {"uniqueLeads": unique_leads}
    except Exception as e:
        logger.error(f"Error filtering leads: {e}")
        raise HTTPException(status_code=500, detail="Failed to filter leads")


@router.post("/api/save-leads")
async def save_leads(request: LeadsRequest):
    """
    Saves a batch of leads directly into the database.
    """
    try:
        # Convert pydantic models to dictionaries
        leads_dict = [l.model_dump(by_alias=True) for l in request.leads]
        res = await db_service.save_leads_directly(leads_dict)
        return res
    except Exception as e:
        logger.error(f"Error saving leads: {e}")
        raise HTTPException(status_code=500, detail="Failed to save leads")


@router.post("/api/generate-leads")
async def generate_leads(input_data: GenerateLeadsInput):
    """
    Core pipeline generator using Server-Sent Events (SSE).
    """
    async def event_generator():
        def make_event(status: str, message: str, **kwargs):
            return f"data: {json.dumps({'status': status, 'message': message, **kwargs})}\n\n"

        try:
            product_name = input_data.productName
            brand = input_data.brand
            division = input_data.division
            description = input_data.description

            if not product_name or product_name.strip() == "":
                yield make_event("error", "Product name is required.")
                return

            # Step 1: Product Analysis
            yield make_event("analyzing", "Analyzing Product...")
            try:
                analysis = await analyze_product(
                    division=division,
                    product_name=product_name,
                    brand=brand,
                    description=description
                )
                logger.info(f"Product analysis completed: {analysis}")
            except Exception as e:
                logger.error(f"Product analysis failed: {e}")
                yield make_event("error", f"Product analysis failed: {str(e)}")
                return

            # Determine keywords
            keywords = analysis.get("searchKeywords") or analysis.get("keywords") or []
            if not keywords:
                keywords = [f"{product_name} supplier Dubai"]

            # Step 2: Company Discovery
            yield make_event("searching", "Finding Companies...")
            try:
                search_results = await discover_companies(keywords)
                logger.info(f"Company discovery completed: found {len(search_results)} search results")
            except Exception as e:
                logger.error(f"Company discovery failed: {e}")
                yield make_event("error", f"Company discovery failed: {str(e)}")
                return

            if not search_results:
                yield make_event("error", "No companies found from search results.")
                return

            # Step 3: Lead Extraction
            yield make_event("extracting", "Extracting Leads...")
            try:
                extracted_leads = await extract_leads(search_results)
                logger.info(f"Lead extraction completed: extracted {len(extracted_leads)} leads")
            except Exception as e:
                logger.error(f"Lead extraction failed: {e}")
                yield make_event("error", f"Lead extraction failed: {str(e)}")
                return

            if not extracted_leads:
                yield make_event("error", "No leads could be extracted from search results.")
                return

            # Step 4: Lead Enrichment
            yield make_event("enriching", "Enriching Leads with Contact Details...")
            
            # SSE progress callback queue logic
            queue = asyncio.Queue()
            def sync_callback(msg: str):
                queue.put_nowait(msg)

            async def enrichment_worker():
                try:
                    return await enrich_leads(extracted_leads, sync_callback)
                finally:
                    # Signal that the enrichment is done
                    await queue.put(None)

            # Start enrichment in a background task
            enrichment_task = asyncio.create_task(enrichment_worker())

            # Read logs from queue and yield them to clients
            while True:
                msg = await queue.get()
                if msg is None:
                    break
                yield make_event("enriching", msg)

            enriched_leads = await enrichment_task
            logger.info(f"Lead enrichment completed: enriched {len(enriched_leads)} leads")

            # Step 5: Lead Validation
            yield make_event("validating", "Validating Leads...")
            try:
                validated_leads = validate_leads(enriched_leads)
                logger.info(f"Lead validation completed: {len(validated_leads)} valid leads remaining")
            except Exception as e:
                logger.error(f"Lead validation failed: {e}")
                yield make_event("error", f"Lead validation failed: {str(e)}")
                return

            if not validated_leads:
                yield make_event("error", "All discovered leads failed validation checks.")
                return

            # Step 6: Save to database (Upserts & partial field matching)
            yield make_event("saving", "Saving Leads...")
            try:
                db_result = await db_service.save_or_update_leads(validated_leads)
                logger.info(f"Database save completed: {db_result}")
            except Exception as e:
                logger.error(f"Database save failed: {e}")
                yield make_event("error", f"Database save failed: {str(e)}")
                return

            # Yield final completion summary
            yield make_event(
                "completed", 
                "Leads generation completed successfully!",
                leads=db_result.get("leads") or [],
                stats={
                    "totalFound": db_result.get("totalFound") or 0,
                    "newLeadsAdded": db_result.get("newLeadsAdded") or 0,
                    "existingLeadsUpdated": db_result.get("existingLeadsUpdated") or 0,
                    "duplicatesSkipped": db_result.get("duplicatesSkipped") or 0,
                }
            )

        except Exception as e:
            logger.error(f"Generate leads pipeline exception: {e}")
            yield make_event("error", f"An unexpected pipeline error occurred: {str(e)}")

    return StreamingResponse(event_generator(), media_type="text/event-stream")

