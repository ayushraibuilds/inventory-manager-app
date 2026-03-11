"""Product image upload endpoint — stores images as data URIs in the catalog item descriptor."""
import base64
import uuid
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from typing import Optional

from routes.auth import get_jwt_token, require_authenticated_request
from db import get_catalog, save_catalog, log_activity

router = APIRouter(tags=["images"])

MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2 MB


@router.post("/api/catalog/item/{item_id}/image", dependencies=[Depends(require_authenticated_request)])
async def upload_item_image(
    item_id: str,
    seller_id: str = Form(...),
    file: UploadFile = File(...),
    token: Optional[str] = Depends(get_jwt_token),
):
    """Upload an image for a catalog item. Stores as data URI in the item descriptor."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="Image must be under 2 MB")

    # Encode image as data URI
    b64 = base64.b64encode(content).decode("utf-8")
    data_uri = f"data:{file.content_type};base64,{b64}"

    # Update catalog item
    catalog = get_catalog(seller_id, jwt_token=token)
    try:
        items = catalog["bpp/catalog"]["bpp/providers"][0].get("items", [])
    except (KeyError, IndexError, TypeError):
        raise HTTPException(status_code=404, detail="Catalog not found")

    found = False
    for item in items:
        if isinstance(item, dict) and item.get("id") == item_id:
            if "descriptor" not in item:
                item["descriptor"] = {}
            if "images" not in item["descriptor"]:
                item["descriptor"]["images"] = []
            # Replace or add first image
            item["descriptor"]["images"] = [data_uri]
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail="Item not found")

    catalog["bpp/catalog"]["bpp/providers"][0]["items"] = items
    save_catalog(seller_id, catalog, jwt_token=token)

    log_activity(seller_id, "IMAGE_UPLOADED", item_id[:8], f"Image uploaded for item {item_id[:8]}", jwt_token=token)

    return {"status": "success", "item_id": item_id, "image_size": len(content)}
