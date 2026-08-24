from typing import Any, Dict, List

def paginate(items: List[Any], page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    total = len(items)
    start = (page - 1) * page_size
    return {'items': items[start:start+page_size], 'total': total, 'page': page,
            'page_size': page_size, 'total_pages': (total+page_size-1)//page_size}
