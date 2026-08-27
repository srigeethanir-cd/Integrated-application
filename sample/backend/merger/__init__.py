"""Intelligent Merge Engine package exports."""

from merger.architecture_preserver import ArchitectureCheckResult, ArchitecturePreserver
from merger.config_synchronizer import ConfigSynchronizer
from merger.conflict_detector import ConflictDetector, ConflictItem
from merger.intelligent_merger import IntelligentMerger, MergeResult
from merger.structural_comparator import FileDiffRecord, StructuralComparator

__all__ = [
    "IntelligentMerger",
    "StructuralComparator",
    "ConflictDetector",
    "ConfigSynchronizer",
    "ArchitecturePreserver",
    "MergeResult",
    "FileDiffRecord",
    "ConflictItem",
    "ArchitectureCheckResult",
]
