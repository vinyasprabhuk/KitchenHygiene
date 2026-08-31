"""
Reference department names, pulled once from OmniStock's live Department
table (inventory.mokshamveg.com) so Kitchen Hygiene's Add Department form
can offer the same names instead of admins retyping/mistyping them.

This is a static snapshot, not a live link to OmniStock -- Kitchen Hygiene
stays a fully independent app (own database, no runtime dependency on
OmniStock being up). Re-run the same query there and update this list by
hand if OmniStock's departments change.
"""
from __future__ import annotations

OMNISTOCK_DEPARTMENTS = [
    "CHINESE",
    "Chaat",
    "COFFEE AND JUICE",
    "Dine In",
    "Dosa",
    "Grinding",
    "Idly",
    "PARCEL MATERIAL",
    "Parotta & Chapathi",
    "SOUTH INDIAN",
    "STAFF MENU",
]
