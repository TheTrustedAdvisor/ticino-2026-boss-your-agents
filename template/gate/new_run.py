"""Orchestrator: start a new review round (empties reports/run, keeps the gate reports)."""
import shutil

import findings as F

shutil.rmtree(F.RUN, ignore_errors=True)
print("reports/run emptied: new review round")
