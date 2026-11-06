"""Fail-closed policy contracts for Article Machine V2."""

from .gates import canonical_gate, file_sha256, workspace_snapshot

__all__ = ["canonical_gate", "file_sha256", "workspace_snapshot"]
