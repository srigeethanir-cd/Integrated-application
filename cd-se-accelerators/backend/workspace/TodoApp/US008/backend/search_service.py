def search_tasks_by_query(query: str):
    mock_tasks = [{"id": "t1", "title": "Buy groceries", "status": "Pending"}, {"id": "t2", "title": "Prepare report", "status": "Completed"}]
    if not query:
        return mock_tasks
    return [t for t in mock_tasks if query.lower() in t["title"].lower()]
