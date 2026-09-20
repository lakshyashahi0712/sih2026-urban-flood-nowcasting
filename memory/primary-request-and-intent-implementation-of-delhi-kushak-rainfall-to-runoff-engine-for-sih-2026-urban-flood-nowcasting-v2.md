---
name: primary-request-and-intent-implementation-of-delhi-kushak-rainfall-to-runoff-engine-for-sih-2026-urban-flood-nowcasting-v2
description: Initial request for Delhi/Kushak rainfall-to-runoff engine implementation with exclusions
metadata:
  type: user
---

# Primary Request and Intent

Implementation of Delhi/Kushak rainfall-to-runoff engine for SIH 2026 Urban Flood Nowcasting V2 scientific pipeline with strict exclusions (no SWMM, hydraulic routing, ML, etc.)

Audit request: Forensically audit and correct the existing rainfall→runoff core only, focusing on mathematics, unit consistency, mass balance conservation (error ≤0.10%), automated tests for specified test matrix, verification that lateral_inflows.py is not active in rainfall→runoff pipeline, and documentation updates

Explicit constraints: Do not add new modeling capability or proceed to hydraulic routing

Subsequent request (after Antigravity hit usage limit): Perform a repository state audit only - inspect git status, recent commits, and files related to IIT Delhi 2018 investigation; check existence of specific files/directories; read investigation report if exists; determine what Antigravity completed

Follow-up request: Inspect ONLY the existing file data/delhi/raw/hydraulic/iitd_dmp_2018_barapullah_kushak_extract.txt to audit for IIT Delhi 2018 engineering evidence (cross-section IDs, chainages, coordinates, elevations, widths, depths, slopes, covered/open status, Kushak-specific vs Barapullah information, surveyed vs interpolated/assumed values, references to appendices/sections, evidence for Kushak hydraulic geometry, data source references)

Current task: Prepare for GSDL CRSC cross-section forensic audit to determine if official GSDL CRSC layer contains actual cross-section survey points intersecting/corresponding to Kushak corridor (do not implement hydraulics yet; evidence-recovery only)