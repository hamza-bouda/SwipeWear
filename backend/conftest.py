import sys
from pathlib import Path

# Add backend/ to sys.path so that 'from contracts.interfaces import ...' works
# regardless of how pytest is invoked.
sys.path.insert(0, str(Path(__file__).parent))
