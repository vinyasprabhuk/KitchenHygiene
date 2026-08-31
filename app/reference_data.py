"""
Suggested department names for the Add Department dropdown: OmniStock's
current department list (inventory.mokshamveg.com), plus a couple of
hygiene-specific locations that aren't in OmniStock (since OmniStock only
tracks stock/requirement departments, not every physical space).

This is a static snapshot, not a live link to OmniStock -- Kitchen Hygiene
stays a fully independent app (own database, no runtime dependency on
OmniStock being up). Update this list by hand if OmniStock's departments
change or more locations need adding.
"""
from __future__ import annotations

DEPARTMENT_SUGGESTIONS = [
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
    "Restaurant",
    "Second Floor Staff Canteen",
]
