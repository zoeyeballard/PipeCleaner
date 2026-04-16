"""
person2_alu.py — Compatibility Wrapper for Rolando's ALU
ECE 5367 Final Project: Pipelined Performance Analyzer

Purpose:
- Keep existing imports of person2_alu working.
- Route all ALU/register/sign-extension behavior to rolandoU_alu.py.

Prototype/Main alignment note:
- If the team standardizes on direct rolandoU_alu imports everywhere,
  this file can remain as a thin alias layer for backward compatibility.
"""

# All exported ALU API functions are delegated to Rolando's implementation.
from rolandoU_alu import alu_execute, register_read, register_write, sign_extend

# Explicit export list to keep module contract clear for other teammates.
__all__ = ["alu_execute", "register_read", "register_write", "sign_extend"]
