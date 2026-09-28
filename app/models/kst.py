"""
Backward compatibility re-export module for models.
Prefer using app.models.location instead.
"""
from app.models.location import KSTLocation

__all__ = ["KSTLocation"]
