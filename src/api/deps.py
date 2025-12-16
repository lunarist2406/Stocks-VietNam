from fastapi import HTTPException

def handle_service_error(data):
    if isinstance(data, dict) and "error" in data:
        raise HTTPException(
            status_code=400,
            detail=data["error"]
        )
    return data
