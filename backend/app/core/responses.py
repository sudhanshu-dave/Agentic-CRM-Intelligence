from typing import Any


def success_response(data: Any = None, message: str = "Success") -> dict:
    return {
        "success": True,
        "message": message,
        "data": data,
    }


def error_response(
    error_code: str,
    message: str,
    details: dict | None = None,
) -> dict:
    return {
        "success": False,
        "error": {
            "error_code": error_code,
            "message": message,
            "details": details or {},
        },
    }