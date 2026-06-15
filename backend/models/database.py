"""SQLite placeholder for saved tests in later phases.

The current build keeps persistence out of the critical path so the backtesting API can
run statelessly. The module remains here to keep the migration path to SQLite
and PostgreSQL clean.
"""
