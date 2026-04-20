"""
person2_alu.py — Compatibility Wrapper for Rolando's ALU
ECE 5367 Final Project: Pipelined Performance Analyzer

Purpose:
- Keep existing imports from 'person2_alu' working for the rest of the team.
- Redirect all function calls to the actual implementation in rolandoU_alu.py.
"""

from rolandoU_alu import (
    alu_execute,
    register_read,
    register_write,
    sign_extend
)

__all__ = ["alu_execute", "register_read", "register_write", "sign_extend"]
