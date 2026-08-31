"""Compatibility module for repository-root operations.

The implementation lives in :mod:`aw.config` so config loading and root rendering share one
source of truth.
"""
from .config import cmd_root_auto, cmd_root_env, cmd_root_set, cmd_root_show, declared_repository_root

__all__ = ["cmd_root_auto", "cmd_root_env", "cmd_root_set", "cmd_root_show", "declared_repository_root"]
