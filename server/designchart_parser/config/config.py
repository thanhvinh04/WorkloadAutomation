from __future__ import annotations

VN_TIMEZONE = "Asia/Ho_Chi_Minh"

FILTER_GROUPS_FABRIC = [
    {"sheet": "FABRIC", "keywords": [r"\bfabric\b"]},
]

FILTER_GROUPS_TRIM = [
    {"sheet": "TRIM", "keywords": [r"\btrim\b"]},
]

FILTER_GROUPS_LABELS = [
    {"sheet": "LABELS", "keywords": [r"\blabels?\b", r"\bLabels\s*&\s*packaging\b"]},
]

FILTER_GROUPS_ARTWORK = [
    {"sheet": "ARTWORK", "keywords": [r"\bartwork\b", r"\bart\s*work\b"]},
]

FILTER_GROUPS_ALL = [
    {"sheet": "FABRIC", "keywords": [r"\bfabric\b"]},
    {"sheet": "TRIM", "keywords": [r"\btrim\b"]},
    {"sheet": "LABELS", "keywords": [r"\blabels?\b", r"\bLabels\s*&\s*packaging\b"]},
    {"sheet": "ARTWORK", "keywords": [r"\bartwork\b", r"\bart\s*work\b"]},
]

FIELD_LABELS = {
    "internal_code": ["INTERNAL CODE", "INTERNAL_CODE", "INTERNAL"],
    "dev_code": ["DEV CODE", "DEV_CODE", "DEV"],
    "vendor_ref_no": ["VENDOR REF NO", "VENDOR REF", "VENDOR REF#"],
    "vendor": ["VENDOR", "SUPPLIER"],
    "name_fabric": ["NAME", "ITEM NAME", "FABRIC NAME", "DESCRIPTION"],
    "name_trim": ["NAME", "ITEM NAME", "TRIM NAME", "DESCRIPTION"],
    "name_labels": ["NAME", "ITEM NAME", "LABEL NAME", "DESCRIPTION"],
    "content": ["CONTENT", "FABRIC CONTENT", "COMPOSITION"],
    "construction": ["CONSTRUCTION"],
    "weight": ["WEIGHT", "WT", "FABRIC WEIGHT"],
    "width": ["WIDTH"],
    "finish": ["FINISH"],
    "coated": ["COATED"],
    "type": ["TYPE", "Type"],
    "variable": ["VARIABLE", "VAR"],
    "location": ["LOCATION", "LOCATION/PLACEMENT", "LOCATION / PLACEMENT"],
    "placement": ["PLACEMENT", "LOCATION/PLACEMENT", "LOCATION / PLACEMENT"],
    "quantity": ["QTY", "QUANTITY"],
    "size": ["SIZE"],
    "size_scale": ["SIZE SCALE", "SIZE SCALE RANGE", "SIZE RANGE"],
    "special_instructions": [
        "SPECIAL INSTRUCTIONS",
        "SPECIAL INSTRUCTION",
        "SPECIAL NOTE",
        "SPECIAL NOTES",
        "NOTES",
        "NOTE",
    ],
}

FABRIC_COLUMNS = [
    "DesignChartHeadId",
    "Position",
    "ColorGarment",
    "ColorTrim",
    "InternalCode",
    "DevCode",
    "VendorRefNo",
    "Vendor",
    "Name",
    "Content",
    "Construction",
    "Weight",
    "Width",
    "Finish",
    "Coated",
    "Page",
]

TRIM_COLUMNS = [
    "DesignChartHeadId",
    "Position",
    "ColorGarment",
    "ColorTrim",
    "InternalCode",
    "DevCode",
    "VendorRefNo",
    "Vendor",
    "Name",
    "Type",
    "Size",
    "Quantity",
    "SpecialInstructions",
    "Location",
    "SizeScale",
    "Page",
]

LABELS_COLUMNS = [
    "DesignChartHeadId",
    "Position",
    "ColorGarment",
    "ColorTrim",
    "InternalCode",
    "DevCode",
    "VendorRefNo",
    "Vendor",
    "Name",
    "Type",
    "Location",
    "Placement",
    "Variable",
    "Quantity",
    "SpecialInstructions",
    "SizeScale",
    "Page",
]