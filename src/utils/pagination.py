import math
from flask import request

def get_pagination_params(default_per_page=10, max_per_page=100):
    """Extrae y valida los parámetros 'page' y 'per_page' del Flask request."""
    try:
        page = int(request.args.get("page", 1))
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1

    try:
        per_page = int(request.args.get("per_page", default_per_page))
        if per_page < 1:
            per_page = default_per_page
        elif per_page > max_per_page:
            per_page = max_per_page
    except (ValueError, TypeError):
        per_page = default_per_page

    return page, per_page

def paginate_query(query, page=1, per_page=10, transform_fn=None):
    """
    Aplica paginación (LIMIT y OFFSET) a una consulta de SQLAlchemy y construye
    la estructura JSON estandarizada.
    """
    from src.models import session
    session.commit()
    session.expire_all()
    total = query.count()
    total_pages = math.ceil(total / per_page) if per_page > 0 else 1
    
    offset = (page - 1) * per_page
    items_raw = query.offset(offset).limit(per_page).all()

    if transform_fn:
        items = [transform_fn(item) for item in items_raw]
    else:
        items = [item.to_dict() if hasattr(item, "to_dict") else item for item in items_raw]

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }
