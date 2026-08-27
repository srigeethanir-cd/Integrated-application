"""
Unit tests for Framework Strategy Engine & Framework Registry.
"""

import pytest
import os
from pathlib import Path
from app.services.framework_strategy.framework_registry import (
    FrameworkRegistry,
    build_default_framework_registry,
)
from app.services.framework_strategy.react_strategy import ReactStrategy
from app.services.framework_strategy.angular_strategy import AngularStrategy
from app.services.framework_detection.angular_detector import AngularDetector
from app.services.framework_detection.react_detector import ReactDetector
from app.services.framework_detection.framework_detector_service import FrameworkDetectorService


def test_framework_registry_registration_and_lookup():
    """Verify registry registers and retrieves React and Angular strategies."""
    registry = build_default_framework_registry()
    
    assert "React" in registry.supported_frameworks()
    assert "Angular" in registry.supported_frameworks()

    react_strat = registry.get_strategy("React")
    assert isinstance(react_strat, ReactStrategy)
    assert react_strat.framework_name == "React"

    angular_strat = registry.get_strategy("Angular")
    assert isinstance(angular_strat, AngularStrategy)
    assert angular_strat.framework_name == "Angular"

    # Case-insensitive lookup & Next.js fallback to React
    assert isinstance(registry.get_strategy("react"), ReactStrategy)
    assert isinstance(registry.get_strategy("angular"), AngularStrategy)
    assert isinstance(registry.get_strategy("Next.js"), ReactStrategy)


def test_framework_registry_unsupported_framework_raises():
    """Verify registry raises ValueError for unknown frameworks."""
    registry = build_default_framework_registry()
    with pytest.raises(ValueError, match="No framework strategy registered"):
        registry.get_strategy("Vue")


def test_angular_detector_signals(tmp_path: Path):
    """Verify AngularDetector correctly detects Angular projects via angular.json and package.json."""
    detector = AngularDetector()

    # Case 1: Empty dir
    assert detector.detect(tmp_path, None) is None

    # Case 2: package.json with @angular/core
    pkg_json = {"dependencies": {"@angular/core": "^17.0.0", "rxjs": "~7.8.0"}}
    res = detector.detect(tmp_path, pkg_json)
    assert res is not None
    assert res["framework"] == "Angular"
    assert res["framework_version"] == "17.0.0"

    # Case 3: angular.json + package.json
    (tmp_path / "angular.json").write_text("{}")
    res_full = detector.detect(tmp_path, pkg_json)
    assert res_full["confidence"] == 100
    assert res_full["framework"] == "Angular"


def test_framework_detector_unknown_error(tmp_path: Path):
    """Verify detector returns Unknown result when no framework is found."""
    (tmp_path / "index.txt").write_text("plain text file without framework signals")
    service = FrameworkDetectorService()
    res = service.detect(str(tmp_path))
    assert res["framework"] == "Unknown"

