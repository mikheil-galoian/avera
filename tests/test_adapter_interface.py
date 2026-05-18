"""Tests for the Adapter SDK interface and AdapterRegistry."""

from __future__ import annotations

import pytest

from avera.adapters.interface import (
    AdapterRegistry,
    RequirementsAdapter,
    VerificationAdapter,
)


# ---------------------------------------------------------------------------
# Minimal concrete implementations for testing
# ---------------------------------------------------------------------------

class _DummyVerification(VerificationAdapter):
    name = "dummy_v"
    version = "1.0.0"
    source_format = "dummy"
    file_extensions = (".dummy",)

    def adapt(self, path, *, run_id, stage):
        return {"runId": run_id, "stage": stage, "tests": [], "metadata": {}}


class _DummyRequirements(RequirementsAdapter):
    name = "dummy_r"
    version = "1.0.0"
    source_format = "dummy_req"
    file_extensions = (".dreq",)

    def adapt_requirements(self, path):
        return []


# ---------------------------------------------------------------------------
# VerificationAdapter contract
# ---------------------------------------------------------------------------

class TestVerificationAdapter:
    def test_metadata_has_required_keys(self):
        adapter = _DummyVerification()
        meta = adapter.metadata
        assert "adapter" in meta
        assert "adapter_name" in meta
        assert "adapter_version" in meta
        assert "source_format" in meta

    def test_metadata_name_matches(self):
        adapter = _DummyVerification()
        assert adapter.metadata["adapter_name"] == "dummy_v"

    def test_can_handle_matching_extension(self, tmp_path):
        adapter = _DummyVerification()
        f = tmp_path / "test.dummy"
        f.write_text("x")
        assert adapter.can_handle(f) is True

    def test_can_handle_non_matching_extension(self, tmp_path):
        adapter = _DummyVerification()
        f = tmp_path / "test.xml"
        f.write_text("x")
        assert adapter.can_handle(f) is False

    def test_can_handle_empty_extensions(self, tmp_path):
        class NoExtAdapter(VerificationAdapter):
            name = "noext"
            version = "1.0.0"
            source_format = "noext"
            file_extensions = ()
            def adapt(self, path, *, run_id, stage): return {}

        adapter = NoExtAdapter()
        f = tmp_path / "test.xml"
        f.write_text("x")
        assert adapter.can_handle(f) is False

    def test_repr(self):
        adapter = _DummyVerification()
        assert "dummy_v" in repr(adapter)


# ---------------------------------------------------------------------------
# RequirementsAdapter contract
# ---------------------------------------------------------------------------

class TestRequirementsAdapter:
    def test_metadata_has_required_keys(self):
        adapter = _DummyRequirements()
        meta = adapter.metadata
        assert "adapter" in meta
        assert "source_format" in meta

    def test_can_handle_matching_extension(self, tmp_path):
        adapter = _DummyRequirements()
        f = tmp_path / "reqs.dreq"
        f.write_text("x")
        assert adapter.can_handle(f) is True

    def test_can_handle_wrong_extension(self, tmp_path):
        adapter = _DummyRequirements()
        f = tmp_path / "reqs.csv"
        f.write_text("x")
        assert adapter.can_handle(f) is False


# ---------------------------------------------------------------------------
# AdapterRegistry
# ---------------------------------------------------------------------------

class TestAdapterRegistry:
    def _registry(self) -> AdapterRegistry:
        reg = AdapterRegistry()
        reg.register(_DummyVerification())
        reg.register(_DummyRequirements())
        return reg

    def test_register_verification(self):
        reg = AdapterRegistry()
        reg.register(_DummyVerification())
        assert "dummy_v" in reg.list_verification_adapters()

    def test_register_requirements(self):
        reg = AdapterRegistry()
        reg.register(_DummyRequirements())
        assert "dummy_r" in reg.list_requirements_adapters()

    def test_duplicate_name_raises(self):
        reg = AdapterRegistry()
        reg.register(_DummyVerification())
        with pytest.raises(ValueError, match="already registered"):
            reg.register(_DummyVerification())

    def test_duplicate_name_overwrite(self):
        reg = AdapterRegistry()
        reg.register(_DummyVerification())
        reg.register(_DummyVerification(), overwrite=True)  # no error
        assert "dummy_v" in reg.list_verification_adapters()

    def test_register_invalid_type_raises(self):
        reg = AdapterRegistry()
        with pytest.raises(TypeError):
            reg.register("not_an_adapter")  # type: ignore[arg-type]

    def test_register_empty_name_raises(self):
        class NoName(VerificationAdapter):
            name = ""
            version = "1.0.0"
            source_format = "x"
            def adapt(self, path, *, run_id, stage): return {}

        reg = AdapterRegistry()
        with pytest.raises(ValueError, match="name must not be empty"):
            reg.register(NoName())

    def test_find_by_extension(self, tmp_path):
        reg = self._registry()
        f = tmp_path / "file.dummy"
        f.write_text("x")
        adapter = reg.find_verification_adapter(f)
        assert adapter.name == "dummy_v"

    def test_find_by_explicit_name(self, tmp_path):
        reg = self._registry()
        f = tmp_path / "anything.txt"
        adapter = reg.find_verification_adapter(f, name="dummy_v")
        assert adapter.name == "dummy_v"

    def test_find_unknown_name_raises(self, tmp_path):
        reg = self._registry()
        f = tmp_path / "file.dummy"
        with pytest.raises(LookupError, match="No adapter named"):
            reg.find_verification_adapter(f, name="nonexistent")

    def test_find_no_matching_adapter_raises(self, tmp_path):
        reg = self._registry()
        f = tmp_path / "file.xml"
        f.write_text("x")
        with pytest.raises(LookupError, match="No adapter can handle"):
            reg.find_verification_adapter(f)

    def test_find_requirements_by_extension(self, tmp_path):
        reg = self._registry()
        f = tmp_path / "reqs.dreq"
        f.write_text("x")
        adapter = reg.find_requirements_adapter(f)
        assert adapter.name == "dummy_r"

    def test_unregister(self):
        reg = self._registry()
        reg.unregister("dummy_v")
        assert "dummy_v" not in reg.list_verification_adapters()

    def test_unregister_nonexistent_no_error(self):
        reg = AdapterRegistry()
        reg.unregister("does_not_exist")  # must not raise

    def test_default_registry_has_builtin_adapters(self, tmp_path):
        reg = AdapterRegistry.default()
        names = reg.list_verification_adapters()
        assert "junit_xml" in names
        assert "log_csv" in names
        assert "simulation_csv" in names
        assert "canoe" in names
        req_names = reg.list_requirements_adapters()
        assert "requirements_csv" in req_names
