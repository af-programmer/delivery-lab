from typing import Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

# מילון בזיכרון לאחסון המשלוחים ומונה מזהה רץ
deliveries_db = {}
next_id = 1

# מפות מעברי סטטוס חוקיים (צעד אחד קדימה בלבד)
VALID_TRANSITIONS = {
    "created": "in_transit",
    "in_transit": "delivered"
}
VALID_STATUSES = {"created", "in_transit", "delivered"}


# --- Exception Handlers (התאמת שגיאות לחוזה: {"error": "..."}) ---

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid payload or validation error"}
    )


# --- Endpoints ---

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/deliveries", status_code=201)
async def create_delivery(request: Request):
    global next_id
    
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})
        
    if not isinstance(data, dict):
        return JSONResponse(status_code=400, content={"error": "Body must be a JSON object"})

    recipient = data.get("recipient")
    address = data.get("address")

    if not isinstance(recipient, str) or not recipient.strip():
        return JSONResponse(status_code=400, content={"error": "recipient must be a non-empty string"})
    if not isinstance(address, str) or not address.strip():
        return JSONResponse(status_code=400, content={"error": "address must be a non-empty string"})

    delivery = {
        "id": next_id,
        "recipient": recipient,
        "address": address,
        "status": "created"
    }
    
    deliveries_db[next_id] = delivery
    next_id += 1
    
    return delivery


@app.get("/deliveries")
def get_deliveries(status: Optional[str] = None):
    if status is not None:
        if status not in VALID_STATUSES:
            return JSONResponse(status_code=400, content={"error": "Invalid status filter"})
        filtered = [d for d in deliveries_db.values() if d["status"] == status]
        return filtered
    
    return list(deliveries_db.values())


@app.get("/deliveries/{delivery_id}")
def get_delivery(delivery_id: int):
    if delivery_id not in deliveries_db:
        return JSONResponse(status_code=404, content={"error": "Delivery not found"})
    return deliveries_db[delivery_id]


@app.patch("/deliveries/{delivery_id}/status")
async def update_status(delivery_id: int, request: Request):
    if delivery_id not in deliveries_db:
        return JSONResponse(status_code=404, content={"error": "Delivery not found"})

    try:
        data = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})

    if not isinstance(data, dict) or "status" not in data:
        return JSONResponse(status_code=400, content={"error": "Missing status field"})

    new_status = data.get("status")
    if new_status not in VALID_STATUSES:
        return JSONResponse(status_code=400, content={"error": "Invalid status value"})

    current_status = deliveries_db[delivery_id]["status"]
    
    # בדיקת חוקיות מעבר הסטטוס (רק צעד אחד קדימה)
    expected_next = VALID_TRANSITIONS.get(current_status)
    if new_status != expected_next:
        return JSONResponse(status_code=409, content={"error": "Invalid status transition"})

    deliveries_db[delivery_id]["status"] = new_status
    return deliveries_db[delivery_id]


@app.delete("/deliveries/{delivery_id}")
def delete_delivery(delivery_id: int):
    if delivery_id not in deliveries_db:
        return JSONResponse(status_code=404, content={"error": "Delivery not found"})

    if deliveries_db[delivery_id]["status"] != "created":
        return JSONResponse(status_code=409, content={"error": "Cannot delete delivery that is not in created status"})

    del deliveries_db[delivery_id]
    return Response(status_code=204)