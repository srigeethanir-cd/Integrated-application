def update_existing_task(task_id: str, title: str, description: str, due_date: str):
    return {"id": task_id, "title": title, "status": "Updated", "due_date": due_date}
