---
name: gsdl-crsc-audit-access-limitation
description: GSDL CRSC audit blocked by authentication requirement (HTTP 403 Forbidden)
metadata:
  type: project
---

# GSDL CRSC Audit Access Limitation

## Attempted Access
- Attempted to access GSDL HYD MapServer metadata at: https://gsdl.org.in/arcgis/rest/services/GSDL_LAYERS_UPDATED/HYD/MapServer
- Received HTTP 403 Forbidden response
- Indicates authentication is required to access this service

## Constraints Impact
Per user instructions:
- "Do NOT search the web"
- "Do NOT implement hydraulics"
- "This is an EVIDENCE-RECOVERY task only. Do not proceed to hydraulic implementation after this audit."
- No authentication tools available for this endpoint within permitted toolset

## Current Status
- Cannot inspect GSDL HYD MapServer metadata to identify CRSC layer ID
- Cannot proceed with GSDL CRSC cross-section forensic audit as originally instructed
- All other constraints honored: no hydraulic implementation, no geometry modifications, etc.

## Evidence Available
- IIT Delhi 2018 extract analyzed (contains contextual data but lacks Kushak-specific hydraulic geometry)
- Rainfall-to-runoff engine implemented with mass balance verification ≤0.10%
- Lateral inflows module confirmed not active in rainfall→runoff pipeline
- Automated test suite passing
- Documentation updated to reflect actual implementation

## Recommended Next Action
Given the authentication barrier and evidence-recovery focus:
1. Document the access limitation formally
2. Acknowledge that GSDL CRSC audit cannot be completed without proper authentication
3. Suggest that if authentication becomes available, the audit should follow the original instructions:
   - Inspect GSDL HYD MapServer metadata to identify CRSC layer ID
   - Record service URL, layer ID, name, feature count, geometry type, CRS, field names, etc.
   - Query CRSC layer spatially around Kushak corridor
   - Determine CRSC point provenance and compare with canonical Kushak corridor
4. Continue with other SIH V2 prototype validation tasks that do not require external service access

This maintains fidelity to the evidence-recovery mandate while acknowledging practical limitations.