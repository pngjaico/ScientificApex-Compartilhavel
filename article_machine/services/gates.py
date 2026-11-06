"""Compatibility service exposing the canonical V2 gate engine."""

from ..policy.gates import canonical_gate, report_is_current, workspace_snapshot

__all__ = ["canonical_gate", "report_is_current", "workspace_snapshot"]
