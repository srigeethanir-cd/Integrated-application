class AppError(Exception):
    def __init__(self, message: str, code: int = 400):
        super().__init__(message)
        self.code = code

class NotFoundError(AppError):
    def __init__(self, resource: str):
        super().__init__(f'{resource} not found', code=404)

class ValidationError(AppError):
    def __init__(self, detail: str):
        super().__init__(f'Validation error: {detail}', code=422)

class UnauthorizedError(AppError):
    def __init__(self):
        super().__init__('Unauthorized', code=401)
