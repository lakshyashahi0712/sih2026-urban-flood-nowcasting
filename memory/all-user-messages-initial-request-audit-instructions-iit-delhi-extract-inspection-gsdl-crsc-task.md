---
name: all-user-messages-initial-request-audit-instructions-iit-delhi-extract-inspection-gsdl-crsc-task
description: All user messages including initial request, audit instructions, IIT Delhi extract inspection, GSDL CRSC task
metadata:
  type: reference
---

# All User Messages

1. "Continue the conversation from where it left off without asking the user any further questions. Resume directly — do not acknowledge the summary, do not recap what was happening, do not preface with 'I'll continue' or similar. Pick up the last task as if the break never happened."

2. "Target: Claude Code (NVIDIA Nemotron 3) The Antigravity research agent has just hit its usage limit. Do NOT implement any new hydraulic/hydrology features. Perform a repository state audit only. Inspect git status and recent commits. Inspect all files changed/created by the most recent IIT Delhi 2018 investigation. Check whether: docs/DELHI_IITD_2018_KUSHAK_CROSS_SECTION_INVESTIGATION.md exists, data/delhi/raw/iitd_2018/ exists, data/delhi/derived/hydraulic/iitd_2018_audit/ exists. Read the investigation report if it exists. Determine exactly what Antigravity completed before hitting its limit. Do not infer missing research. Do not modify canonical Kushak geometry, catchment, rainfall, hydrology, or hydraulic code. Return a concise report with: COMPLETED, PARTIALLY COMPLETED, NOT COMPLETED, FILES CREATED/CHANGED, ANY SCIENTIFIC RISK, RECOMMENDED NEXT SINGLE ACTION"

3. "We have confirmed that the planned IIT Delhi 2018 investigation did NOT produce new files before Antigravity hit its usage limit. Do NOT search the web. Do NOT implement hydraulics. Do NOT modify canonical geometry, catchment, rainfall, hydrology, or hydraulic code. Inspect ONLY the existing file: data/delhi/raw/hydraulic/iitd_dmp_2018_barapullah_kushak_extract.txt. Goal: Determine exactly what useful IIT Delhi 2018 engineering evidence is already present in this existing extract. Audit it for: [12 specific audit points]. Return: A. EXACT useful evidence already present, B. CROSS-SECTIONS FOUND, C. KUSHAK-SPECIFIC EVIDENCE, D. DATA PROVENANCE, E. WHAT IS STILL MISSING, F. WHETHER THIS EXISTING EXTRACT IS SUFFICIENT TO PROCEED WITH HYDRAULICS, G. ONE recommended next action"

4. "NEXT SINGLE TASK: GSDL CRSC CROSS-SECTION FORENSIC AUDIT [extremely detailed instructions for auditing GSDL CRSC layer for Kushak cross-section points]"

Security-relevant instructions and constraints (preserved verbatim):
- "Do NOT implement any new hydraulic/hydrology features"
- "Do NOT search the web"
- "Do NOT implement hydraulics"
- "Do NOT modify canonical geometry, catchment, rainfall, hydrology, or hydraulic code"
- "Do NOT modify canonical Kushak geometry or the 27.66 km² catchment"
- "Do not implement hydraulic routing"
- "Do NOT: modify canonical geometry, modify catchment, modify rainfall, modify hydrology, implement hydraulic solver, create synthetic cross-sections, assume CRSC points are surveyed, use them in the hydraulic model yet, resurrect KP-01–KP-25"
- "This is an EVIDENCE-RECOVERY task only. Do not proceed to hydraulic implementation after this audit."