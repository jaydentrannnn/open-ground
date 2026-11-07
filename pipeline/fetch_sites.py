"""Housing-element sites for Orange County -> data/raw/he_sites.geojson   OWNER: Builder A
Run:  python pipeline/fetch_sites.py                  all OC jurisdictions in the layer (2,126 sites)
      python pipeline/fetch_sites.py "GARDEN GROVE"   one city (names are UPPERCASE in this layer)

Source: SCAG HousingElementSite_poly_scag, layer 0 (checked 2026-11-07). Fields used: PID24, APN24,
Assessor_Parcel_Number, Jurisdiction, Low/Moderate/Above_Moderate/Total_HE_Capacity, YEAR,
Shape.STArea() (square meters: the layer is in UTM 11N, wkid 26911).

NOT in this layer (checked 2026-11-07): Santa Ana, Costa Mesa, Huntington Beach, Orange, Tustin,
Rancho Santa Margarita, Laguna Woods. Those cities need their own site-inventory source.
"""
import json
import sys

from common import RAW, fetch_all

HE = "https://maps.scag.ca.gov/scaggis/rest/services/LDX/HousingElementSite_poly_scag/MapServer/0"

city = sys.argv[1].upper() if len(sys.argv) > 1 else None
where = "COUNTY='Orange'" + (f" AND Jurisdiction='{city}'" if city else "")
feats = fetch_all(HE, where)
print(f"housing-element sites ({city or 'all Orange County'}): {len(feats)}")
if not feats:
    print("0 sites. City names are UPPERCASE, and some OC cities are not in this layer (see docstring).")
(RAW / "he_sites.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
