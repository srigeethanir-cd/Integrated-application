def filter_tasks_by_status(status: str):
    tasks = [{"id": "1", "title": "Read book", "status": "Completed"}, {"id": "2", "title": "Write code", "status": "Pending"}]
    if status == "All":
        return tasks
    return [t for t in tasks if t["status"].lower() == status.lower()]
