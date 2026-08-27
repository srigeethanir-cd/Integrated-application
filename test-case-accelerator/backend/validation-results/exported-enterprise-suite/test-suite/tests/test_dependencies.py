import asyncio
import builtins
import hashlib
import importlib
import inspect
from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch
module = importlib.import_module('app.dependencies')
dependencies = ['UserRepository', 'UserService']
test_variant = 'positive'
expected_exceptions = []
semantic_assertions = {'authentication': False, 'boolean': False, 'collection': False, 'crud': True, 'exception_details': False, 'interaction_dependencies': ['UserRepository'], 'validation': False, 'expectations': ['The repository or database persistence operation is invoked', 'The created or persisted object is returned']}
if any((any((token in dependency.casefold() for token in ('env', 'environ', 'settings', 'config'))) for dependency in dependencies)):
    monkeypatch.setenv('TESTFORGE_UNIT_TEST', '1')
patches = ExitStack()
dependency_mocks = {}
for dependency in dependencies:
    name = dependency.rsplit('.', 1)[-1]
    if not hasattr(module, name):
        name = dependency.split('.', 1)[0]
    if hasattr(module, name):
        original = getattr(module, name)
        if inspect.isclass(original) and issubclass(original, BaseException):
            continue
        replacement = AsyncMock(name=name) if inspect.iscoroutinefunction(original) else MagicMock(name=name)
        if any((token in name.casefold() for token in ('hash', 'encode', 'digest'))):
            replacement.return_value = '00:' + '00' * 32
        elif any((token in name.casefold() for token in ('issue', 'pair', 'rotate'))):
            replacement.return_value = (MagicMock(name=f'{name}_first'), MagicMock(name=f'{name}_second'))
        else:
            replacement.return_value.__iter__.return_value = [MagicMock(name=f'{name}_first'), MagicMock(name=f'{name}_second')]
        if test_variant == 'exception' and expected_exceptions:
            exception_type = getattr(module, expected_exceptions[0], None)
            exception_type = exception_type or getattr(builtins, expected_exceptions[0], None)
            if isinstance(exception_type, type) and issubclass(exception_type, BaseException):
                try:
                    replacement.side_effect = exception_type('forced dependency failure')
                except TypeError:
                    replacement.side_effect = exception_type()
        dependency_mocks[dependency] = replacement
        patches.enter_context(patch.object(module, name, replacement))
target = _resolve_unit_target(module, 'get_user_service')
owner = getattr(target, '__self__', None)
repository = getattr(owner, 'repository', None)
if isinstance(repository, MagicMock):
    entity = MagicMock(name='repository_entity')
    entity.id = 1
    entity.is_active = True
    entity.hashed_password = hashlib.sha256(b'ValidPass123!').hexdigest()
    repository.get_by_email.return_value = None if target.__name__.startswith('create_') else entity
    repository.get_by_id.return_value = entity
    repository.add.side_effect = lambda value: value
    repository.search.return_value = []
args, kwargs = _unit_arguments(target)
for dependency in dependencies:
    parameter_name = dependency.split('.', 1)[0]
    parameter_mock = kwargs.get(parameter_name)
    if isinstance(parameter_mock, MagicMock):
        dependency_mocks.setdefault(dependency, parameter_mock)
bound = inspect.signature(target).bind(*args, **kwargs)
with patches:
    try:
        result = target(*args, **kwargs)
        if inspect.isawaitable(result):
            result = asyncio.run(result)
        if inspect.isgenerator(result):
            result = list(result)
    except Exception as error:
        if type(error).__name__ not in expected_exceptions:
            raise
        result = error
assert callable(target)
assert set(bound.arguments).issubset(inspect.signature(target).parameters)
if isinstance(result, BaseException):
    assert type(result).__name__ in expected_exceptions
    assert str(result), 'Expected exception must carry a diagnostic message'
    if semantic_assertions['exception_details'] or (hasattr(result, 'status_code') and hasattr(result, 'detail')):
        assert isinstance(result.status_code, int)
        assert result.detail not in (None, '')
        if result.headers is not None:
            assert isinstance(result.headers, dict)
    else:
        assert result.args and result.args[0] == str(result)
else:
    assert not isinstance(result, BaseException)
    return_annotation = inspect.signature(target).return_annotation
    if not isinstance(result, (MagicMock, AsyncMock)) and return_annotation is not inspect.Signature.empty and isinstance(return_annotation, type) and (return_annotation is not type(None)):
        assert isinstance(result, return_annotation)
    if semantic_assertions['boolean']:
        expected_boolean = True if semantic_assertions['crud'] else test_variant != 'negative'
        assert result is expected_boolean
    if semantic_assertions['collection'] and (not isinstance(result, (MagicMock, AsyncMock))):
        assert isinstance(result, (dict, list, set, tuple))
for dependency, mock in dependency_mocks.items():
    assert isinstance(mock, (MagicMock, AsyncMock)), dependency
interaction_mocks = [dependency_mocks[name] for name in semantic_assertions['interaction_dependencies'] if name in dependency_mocks]
if interaction_mocks and (not isinstance(result, BaseException)):
    assert any((mock.mock_calls for mock in interaction_mocks)), 'Expected the semantic collaborator interaction to occur'
