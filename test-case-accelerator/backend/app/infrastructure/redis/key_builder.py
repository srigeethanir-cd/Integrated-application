"""Canonical Redis cache-key construction."""

from uuid import UUID


class CacheKeyBuilder:
    """Build consistently namespaced keys for Test Case Accelerator data."""

    NAMESPACE = "testforge"

    @classmethod
    def project(cls, project_id: str | UUID) -> str:
        """Return a project key for the supplied project identifier."""
        return cls._build("project", project_id)

    @classmethod
    def dependency(cls, run_id: str | UUID) -> str:
        """Return a dependency-run key for the supplied run identifier."""
        return cls._build("dependency", run_id)

    @classmethod
    def code_understanding(cls, run_id: str | UUID) -> str:
        """Return a code-understanding key for the supplied run identifier."""
        return cls._build("code-understanding", run_id)

    @staticmethod
    def code_understanding_content(
        project_id: str | UUID, content_hash: str
    ) -> str:
        """Return a content-addressed Stage 3 result key.

        Args:
            project_id: Project whose source was analyzed.
            content_hash: Deterministic digest of discovered source content.

        Returns:
            A key in code-understanding:{project_id}:{content_hash} format.
        """
        return f"code-understanding:{project_id}:{content_hash}"

    @staticmethod
    def provider_response(project_id: str | UUID, content_hash: str) -> str:
        return f"code-provider:{project_id}:{content_hash}"

    @staticmethod
    def enriched_stage3(project_id: str | UUID, content_hash: str) -> str:
        return f"code-enriched:{project_id}:{content_hash}"

    @staticmethod
    def runtime_preparation(project_id: str | UUID, content_hash: str) -> str:
        return f"runtime-preparation:{project_id}:{content_hash}"

    @staticmethod
    def quality_checkpoint(project_id: str | UUID, run_id: str | UUID) -> str:
        return f"quality-checkpoint:{project_id}:{run_id}"

    @classmethod
    def test_generation(cls, run_id: str | UUID) -> str:
        """Return a test-generation key for the supplied run identifier."""
        return cls._build("test-generation", run_id)

    @staticmethod
    def test_generation_content(
        project_id: str | UUID,
        code_understanding_run_id: str | UUID,
        generation_hash: str,
    ) -> str:
        """Return a content-addressed Stage 4 generation key.

        Args:
            project_id: Project owning the generated suite.
            code_understanding_run_id: Persisted Stage 3 input run.
            generation_hash: Digest of all deterministic generation inputs.

        Returns:
            A key in the required Stage 4 cache-key format.
        """
        return (
            f"test-generation:{project_id}:{code_understanding_run_id}:"
            f"{generation_hash}"
        )

    @classmethod
    def verification(cls, run_id: str | UUID) -> str:
        """Return a verification key for the supplied run identifier."""
        return cls._build("verification", run_id)

    @staticmethod
    def verification_content(
        project_id: str | UUID,
        verification_run_id: str | UUID,
        verification_hash: str,
    ) -> str:
        """Return a content-addressed Stage 5 verification key.

        Args:
            project_id: Project owning the verification.
            verification_run_id: Persisted run containing Stage 5 output.
            verification_hash: Digest of verification inputs and configuration.

        Returns:
            A key in the required Stage 5 cache-key format.
        """
        return f"verification:{project_id}:{verification_run_id}:{verification_hash}"

    @classmethod
    def quality(cls, run_id: str | UUID) -> str:
        """Return a quality key for the supplied run identifier."""
        return cls._build("quality", run_id)

    @staticmethod
    def quality_content(
        project_id: str | UUID,
        optimization_run_id: str | UUID,
        quality_hash: str,
    ) -> str:
        """Return a content-addressed Stage 6 optimization key.

        Args:
            project_id: Project owning the optimization.
            optimization_run_id: Persisted run containing Stage 6 output.
            quality_hash: Digest of optimization inputs and policy.

        Returns:
            A key in the required Stage 6 cache-key format.
        """
        return f"quality:{project_id}:{optimization_run_id}:{quality_hash}"

    @classmethod
    def runtime(cls, run_id: str | UUID) -> str:
        """Return a runtime-validation key for the supplied run identifier."""
        return cls._build("runtime", run_id)

    @classmethod
    def _build(cls, resource: str, identifier: str | UUID) -> str:
        """Build a namespaced key from a resource and identifier."""
        return f"{cls.NAMESPACE}:{resource}:{identifier}"
