import os
import sys

# Add the project root to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.main import app

