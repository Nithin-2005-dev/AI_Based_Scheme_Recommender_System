"""pytest configuration for backend tests."""
import sys
import os

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# Add frontend locales to path so tests can import them
frontend_locales = os.path.join(
    backend_dir, "..", "frontend", "src", "locales"
)
sys.path.insert(0, os.path.normpath(frontend_locales))
