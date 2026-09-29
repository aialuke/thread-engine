"""Pure rules that scripts/loop.py runs. No file writes, network or environment reads.

loop.py stays the only writer of loop state; nothing here touches the ledger or state files.
"""
