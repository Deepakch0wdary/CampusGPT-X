from typing import Any, Dict, List, Union

def make_response(
    success: bool,
    message: str,
    data: Union[Dict[str, Any], List[Any], None] = None,
    errors: Any = None,
    extra_compat: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Standardizes every API response structure to:
    {
        "success": bool,
        "message": str,
        "data": {},
        "errors": null
    }
    While supporting extra_compat key-value pairs for backward compatibility.
    """
    response = {
        "success": success,
        "message": message,
        "data": data if data is not None else {},
        "errors": errors
    }
    if extra_compat:
        for k, v in extra_compat.items():
            if k not in response or (k == "errors" and response[k] is None):
                response[k] = v
    return response
