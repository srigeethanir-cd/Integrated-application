"""Shim for git package when GitPython is not installed.
Provides a minimal `Repo` class with a `clone_from` method that raises
`NotImplementedError`. The test suite only needs the `GitCommandError`
exception, which is defined in `git.exc`.
"""

class Repo:
    @staticmethod
    def clone_from(*args, **kwargs):
        raise NotImplementedError("GitPython is not installed; Repo.clone_from is unavailable.")
