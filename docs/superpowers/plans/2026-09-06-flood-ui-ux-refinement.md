# Flood Nowcasting UI/UX Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refine the flood nowcasting system's UI/UX to achieve a professional, cohesive industrial-design aesthetic that avoids generic "AI-generated" appearances while maintaining high readability and functional clarity for emergency operations use.

**Architecture:** The refinement will focus on four key areas: 1) Industrial-inspired color palette with purposeful data encoding, 2) Improved typography hierarchy and spacing, 3) Consistent component styling using shadcn-ui principles, and 4) Subtle, purposeful animations for feedback and state changes. Changes will be made to CSS variables, component files, and potentially introducing a design token system.

**Tech Stack:** React, TypeScript, Tailwind CSS (via existing CSS variables), MapLibre GL, shadcn-ui components

**Spec:** docs/superpowers/specs/2026-09-06-flood-ui-ux-design.md

## Global Constraints

- Must maintain all existing functionality
- Must remain responsive across mobile/desktop
- Must maintain accessibility standards (WCAG AA)
- Must preserve existing color encoding semantics for hydrological data
- Must not break integration with backend APIs
- Should leverage existing CSS variable system where possible

---

### Task 1: Establish Design Tokens and Color System

**Files:**
- Create: `src/styles/design-tokens.css`
- Modify: `src/index.css:1-58`
- Modify: `src/App.css:1-58`

**Interfaces:**
- Consumes: None
- Produces: CSS variables for refined color palette, typography scale, spacing system

- [ ] **Step 1: Analyze current color usage and define industrial-inspired palette**

```css
/* src/styles/design-tokens.css */
/* Industrial/Flood Operations Inspired Palette */
:root {
  /* Base Neutrals - Warmer, less clinical than current */
  --slate-50: #f8fafc;
  --slate-100: #f1f5f9;
  --slate-200: #e2e8f0;
  --slate-300: #cbd5e1;
  --slate-400: #94a3b8;
  --slate-500: #64748b;
  --slate-600: #475569;
  --slate-700: #334155;
  --slate-800: #1e293b;
  --slate-900: #0f172a;
  --slate-950: #020617;
  
  /* Hydrological Data Encoding - More Distinct, Scientifically Grounded */
  --hydro-no-water: #f8fafc;        /* 0mm */
  --hydro-minimal: #f0f9ff;         /* 0-2mm */
  --hydro-light: #e0f2fe;           /* 2-5mm */
  --hydro-moderate: #bae6fd;        /* 5-10mm */
  --hydro-significant: #7dd3fc;     /* 10-20mm */
  --hydro-high: #38bdf8;            /* 20-30mm */
  --hydro-severe: #0ea5e9;          /* 30-50mm */
  --hydro-extreme: #0284c7;         /* 50mm+ */
  
  /* Operational Status - Clear, Action-Oriented */
  --status-normal: #10b981;         /* Success/Normal */
  --status-advisory: #f59e0b;       /* Watch/Advisory */
  --status-warning: #ef4444;        /* Warning */
  --status-critical: #dc2626;       /* Critical/Action Required */
  
  /* Interactive Elements */
  --primary: #0ea5e9;               /* Main CTA */
  --primary-hover: #0284c7;
  --secondary: #64748b;             /* Secondary actions */
  --secondary-hover: #475569;
  
  /* Typography Scale - More Refined */
  --text-xs: 0.75rem;               /* 12px */
  --text-sm: 0.875rem;              /* 14px */
  --text-base: 1rem;                /* 16px */
  --text-lg: 1.125rem;              /* 18px */
  --text-xl: 1.25rem;               /* 20px */
  --text-2xl: 1.5rem;               /* 24px */
  --text-3xl: 1.875rem;             /* 30px */
  --text-4xl: 2.25rem;              /* 36px */
  --text-5xl: 3rem;                 /* 48px */
  
  /* Spacing System - 4px Grid */
  --spacing-0: 0;
  --spacing-1: 0.25rem;             /* 4px */
  --spacing-2: 0.5rem;              /* 8px */
  --spacing-3: 0.75rem;             /* 12px */
  --spacing-4: 1rem;                /* 16px */
  --spacing-5: 1.25rem;             /* 20px */
  --spacing-6: 1.5rem;              /* 24px */
  --spacing-8: 2rem;                /* 32px */
  --spacing-10: 2.5rem;             /* 40px */
  --spacing-12: 3rem;               /* 48px */
  
  /* Border Radius */
  --radius-sm: 0.25rem;             /* 4px */
  --radius-md: 0.375rem;            /* 6px */
  --radius-lg: 0.5rem;              /* 8px */
  --radius-xl: 0.75rem;             /* 12px */
  
  /* Shadows - Subtle, Functional */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}
```

- [ ] **Step 2: Run build to verify CSS compiles without errors**

Run: `npm run build` (if applicable) or check CSS validity
Expected: No CSS compilation errors

- [ ] **Step 3: Update index.css to import design tokens and refine base styles**

```css
/* src/index.css - Addition at top */
@import './styles/design-tokens.css';

/* Refined base styles */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #root {
  width: 100%;
  height: 100%;
  overflow: hidden;
  font-family: var(--font-sans);
  background-color: var(--slate-50);
  color: var(--slate-900);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Updated typography utilities */
.text-xs { font-size: var(--text-xs); line-height: 1rem; }
.text-sm { font-size: var(--text-sm); line-height: 1.25rem; }
.text-base { font-size: var(--text-base); line-height: 1.5rem; }
.text-lg { font-size: var(--text-lg); line-height: 1.75rem; }
.text-xl { font-size: var(--text-xl); line-height: 1.75rem; }
.text-2xl { font-size: var(--text-2xl); line-height: 2rem; }
.text-3xl { font-size: var(--text-3xl); line-height: 2.25rem; }
.text-4xl { font-size: var(--text-4xl); line-height: 2.5rem; }
.text-5xl { font-size: var(--text-5xl); line-height: 2.5rem; }

.font-light { font-weight: 300; }
.font-normal { font-weight: 400; }
.font-medium { font-weight: 500; }
.font-semibold { font-weight: 600; }
.font-bold { font-weight: 700; }
.font-extrabold { font-weight: 800; }
```

- [ ] **Step 4: Update App.css to use new design tokens**

```css
/* src/App.css - Replace existing :root with design token references */
:root {
  /* Base Neutrals - Now using design tokens */
  --monsoon-deep: var(--slate-900);       /* Deep water/night */
  --monsoon-mid: var(--slate-700);        /* Water depth indicator */
  --monsoon-shallow: var(--slate-500);    /* Shallow water/transition */
  --monsoon-surface: var(--slate-100);    /* Water surface reflection */
  --alert-clear: var(--slate-50);         /* Maximum legibility */

  /* Hydrological Data Encoding - Updated to use hydro-* tokens */
  --flow-velocity: var(--primary);        /* Water movement - primary interactive */
  --infiltration: var(--status-normal);   /* Soil absorption - secondary actions */
  --surface-runoff: var(--status-warning);/* Overland flow - warnings/critical */
  --groundwater: var(--accent-primary);   /* Subsurface - informational */
  --evaporation: var(--status-advisory);  /* Flux dissipation - metrics */

  /* Flood Depth Encoding - Now using hydro scale for better distinction */
  --depth-0: var(--hydro-no-water);            /* No water */
  --depth-0-25: var(--hydro-minimal);          /* Ankle-deep */
  --depth-0-5: var(--hydro-light);             /* Calf-deep - action threshold */
  --depth-1.0: var(--hydro-moderate);          /* Waist-deep - evacuation consideration */
  --depth-1.5: var(--hydro-significant);       /* Chest-deep - high risk */
  --depth-2.0: var(--hydro-high);              /* Head-deep - extreme danger */
  --depth-3-0: var(--hydro-extreme);           /* Submerged - critical infrastructure */

  /* Emergency Semantics - Updated */
  --alert-imminent: var(--status-critical);    /* Flash flood imminent */
  --alert-active: var(--status-warning);       /* Flooding occurring */
  --alert-recording: var(--status-normal);     /* Monitoring active */

  /* Risk Semantics - Refined */
  --risk-severe: var(--slate-800);             /* Severe/inundation risk */
  --risk-high: var(--slate-700);               /* High risk */
  --risk-mod: var(--slate-500);                /* Moderate risk */
  --risk-low: var(--slate-400);                /* Low risk */

  /* Legacy Variables - Updated */
  --topbar-bg: var(--monsoon-deep);
  --topbar-border: var(--monsoon-mid);
  --topbar-text: var(--alert-clear);
  --topbar-text-muted: var(--monsoon-shallow);

  --panel-bg: var(--slate-50);
  --panel-border: var(--slate-200);
  --panel-shadow: var(--shadow-md);
  --text-main: var(--slate-900);
  --text-muted: var(--slate-500);
  --text-sub: var(--slate-400);

  --accent-primary: var(--primary);
  --accent-dark: var(--slate-800);

  --color-depth-low: var(--depth-0-25);
  --color-depth-mod: var(--depth-0-5);
  --color-depth-high: var(--depth-1.0);
  --color-depth-severe: var(--depth-2.0);
}

/* Refine panel and button styles to use new tokens */
.panel {
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--panel-shadow);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--font-semibold);
  font-size: var(--text-sm);
  letter-spacing: var(--tracking-tight);
  border-radius: var(--radius-md);
  border-width: 1px;
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: center;
  white-space: nowrap;
  padding: var(--spacing-2) var(--spacing-4);
}

.btn-primary {
  background-color: var(--primary);
  border-color: var(--primary);
  color: var(--alert-clear);
}

.btn-primary:hover {
  background-color: var(--primary-hover);
  border-color: var(--primary-hover);
}

/* Update utility classes */
.m-0 { margin: var(--spacing-0); }
.m-1 { margin: var(--spacing-1); }
.m-2 { margin: var(--spacing-2); }
.m-3 { margin: var(--spacing-3); }
.m-4 { margin: var(--spacing-4); }
.m-5 { margin: var(--spacing-5); }
.m-6 { margin: var(--spacing-6); }
.m-8 { margin: var(--spacing-8); }
.m-10 { margin: var(--spacing-10); }
.m-12 { margin: var(--spacing-12); }

.mx-0 { margin-left: var(--spacing-0); margin-right: var(--spacing-0); }
.mx-1 { margin-left: var(--spacing-1); margin-right: var(--spacing-1); }
.mx-2 { margin-left: var(--spacing-2); margin-right: var(--spacing-2); }
.mx-3 { margin-left: var(--spacing-3); margin-right: var(--spacing-3); }
.mx-4 { margin-left: var(--spacing-4); margin-right: var(--spacing-4); }
.mx-5 { margin-left: var(--spacing-5); margin-right: var(--spacing-5); }
.mx-6 { margin-left: var(--spacing-6); margin-right: var(--spacing-6); }
.mx-8 { margin-left: var(--spacing-8); margin-right: var(--spacing-8); }
.mx-10 { margin-left: var(--spacing-10); margin-right: var(--spacing-10); }
.mx-12 { margin-left: var(--spacing-12); margin-right: var(--spacing-12); }

.my-0 { margin-top: var(--spacing-0); margin-bottom: var(--spacing-0); }
.my-1 { margin-top: var(--spacing-1); margin-bottom: var(--spacing-1); }
.my-2 { margin-top: var(--spacing-2); margin-bottom: var(--spacing-2); }
.my-3 { margin-top: var(--spacing-3); margin-bottom: var(--spacing-3); }
.my-4 { margin-top: var(--spacing-4); margin-bottom: var(--spacing-4); }
.my-5 { margin-top: var(--spacing-5); margin-bottom: var(--spacing-5); }
.my-6 { margin-top: var(--spacing-6); margin-bottom: var(--spacing-6); }
.my-8 { margin-top: var(--spacing-8); margin-bottom: var(--spacing-8); }
.my-10 { margin-top: var(--spacing-10); margin-bottom: var(--spacing-10); }
.my-12 { margin-top: var(--spacing-12); margin-bottom: var(--spacing-12); }

.p-0 { padding: var(--spacing-0); }
.p-1 { padding: var(--spacing-1); }
.p-2 { padding: var(--spacing-2); }
.p-3 { padding: var(--spacing-3); }
.p-4 { padding: var(--spacing-4); }
.p-5 { padding: var(--spacing-5); }
.p-6 { padding: var(--spacing-6); }
.p-8 { padding: var(--spacing-8); }
.p-10 { padding: var(--spacing-10); }
.p-12 { padding: var(--spacing-12); }

.px-0 { padding-left: var(--spacing-0); padding-right: var(--spacing-0); }
.px-1 { padding-left: var(--spacing-1); padding-right: var(--spacing-1); }
.px-2 { padding-left: var(--spacing-2); padding-right: var(--spacing-2); }
.px-3 { padding-left: var(--spacing-3); padding-right: var(--spacing-3); }
.px-4 { padding-left: var(--spacing-4); padding-right: var(--spacing-4); }
.px-5 { padding-left: var(--spacing-5); padding-right: var(--spacing-5); }
.px-6 { padding-left: var(--spacing-6); padding-right: var(--spacing-6); }
.px-8 { padding-left: var(--spacing-8); padding-right: var(--spacing-8); }
.px-10 { padding-left: var(--spacing-10); padding-right: var(--spacing-10); }
.px-12 { padding-left: var(--spacing-12); padding-right: var(--spacing-12); }

.py-0 { padding-top: var(--spacing-0); padding-bottom: var(--spacing-0); }
.py-1 { padding-top: var(--spacing-1); padding-bottom: var(--spacing-1); }
.py-2 { padding-top: var(--spacing-2); padding-bottom: var(--spacing-2); }
.py-3 { padding-top: var(--spacing-3); padding-bottom: var(--spacing-3); }
.py-4 { padding-top: var(--spacing-4); padding-bottom: var(--spacing-4); }
.py-5 { padding-top: var(--spacing-5); padding-bottom: var(--spacing-5); }
.py-6 { padding-top: var(--spacing-6); padding-bottom: var(--spacing-6); }
.py-8 { padding-top: var(--spacing-8); padding-bottom: var(--spacing-8); }
.py-10 { padding-top: var(--spacing-10); padding-bottom: var(--spacing-10); }
.py-12 { padding-top: var(--spacing-12); padding-bottom: var(--spacing-12); }

.gap-0 { gap: var(--spacing-0); }
.gap-1 { gap: var(--spacing-1); }
.gap-2 { gap: var(--spacing-2); }
.gap-3 { gap: var(--spacing-3); }
.gap-4 { gap: var(--spacing-4); }
.gap-5 { gap: var(--spacing-5); }
.gap-6 { gap: var(--spacing-6); }
.gap-8 { gap: var(--spacing-8); }
.gap-10 { gap: var(--spacing-10); }
.gap-12 { gap: var(--spacing-12); }
```

- [ ] **Step 5: Verify changes don't break existing UI**

Run: `npm start` or manual verification
Expected: UI loads correctly with updated colors and spacing

- [ ] **Step 6: Commit design token establishment**

```bash
git add src/styles/design-tokens.css src/index.css src/App.css
git commit -m "design: establish industrial-inspired design tokens and refined color system"
```

---

### Task 2: Refine Typography and Text Hierarchy

**Files:**
- Modify: `src/App.css:1526-1800` (Typography sections)
- Modify: `src/components/FloodMap.tsx:1240-1400` (Text elements in UI)

**Interfaces:**
- Consumes: Design tokens from Task 1
- Produces: Improved typography hierarchy throughout the application

- [ ] **Step 1: Update typography scale in App.css for better hierarchy**

```css
/* src/App.css - Replace typography section (lines 1526-1560) */
/* Base Typography - Refined for better hierarchy */
* {
  font-family: var(--font-sans);
}

/* Enhanced Scale System with better ratios */
.text-xs { font-size: var(--text-xs); line-height: calc(var(--text-xs) * 1.4); }
.text-sm { font-size: var(--text-sm); line-height: calc(var(--text-sm) * 1.4); }
.text-base { font-size: var(--text-base); line-height: calc(var(--text-base) * 1.5); }
.text-lg { font-size: var(--text-lg); line-height: calc(var(--text-lg) * 1.5); }
.text-xl { font-size: var(--text-xl); line-height: calc(var(--text-xl) * 1.4); }
.text-2xl { font-size: var(--text-2xl); line-height: calc(var(--text-2xl) * 1.4); }
.text-3xl { font-size: var(--text-3xl); line-height: calc(var(--text-3xl) * 1.35); }
.text-4xl { font-size: var(--text-4xl); line-height: calc(var(--text-4xl) * 1.3); }
.text-5xl { font-size: var(--text-5xl); line-height: calc(var(--text-5xl) * 1.25); }

.font-light { font-weight: 300; }
.font-normal { font-weight: 400; }
.font-medium { font-weight: 500; }
.font-semibold { font-weight: 600; }
.font-bold { font-weight: 700; }
.font-extrabold { font-weight: 800; }

/* Improved Tracking for different sizes */
.tracking-tighter { letter-spacing: -0.05em; }
.tracking-tight { letter-spacing: -0.025em; }
.tracking-normal { letter-spacing: 0; }
.tracking-wide { letter-spacing: 0.025em; }
.tracking-wider { letter-spacing: 0.05em; }
.tracking-widest { letter-spacing: 0.1em; }

/* Leading (line-height) utilities */
.leading-none { line-height: 1; }
.leading-tight { line-height: 1.25; }
.leading-snug { line-height: 1.375; }
.leading-normal { line-height: 1.5; }
.leading-relaxed { line-height: 1.625; }
.leading-loose { line-height: 2; }
```

- [ ] **Step 2: Refine text elements in FloodMap.tsx for better hierarchy**

```tsx
// src/components/FloodMap.tsx - Update text styling (example changes)
return (
  <div className="flood-app">
    {/* 1. TOP BAR: IMMEDIATE 3-SECOND SYSTEM IDENTITY */}
    <header className="app-topbar">
      <div className="topbar-left">
        <div className="system-identity">
          <span className="system-mark text-2xl font-bold tracking-tight">⛯</span>
          <span className="system-title text-xl font-extrabold letter-spacing-[-0.5px]">
            URBAN FLOOD NOWCAST
          </span>
        </div>
        {/* ... */}
      </div>
      
      {/* ... */}
    </header>
    
    {/* 2. MAP WORKSPACE */}
    <div className="map-workspace">
      {/* ... */}
      
      {/* LEFT WORKSPACE OVERLAY */}
      <div className="map-left-overlay">
        {/* TIMELINE & SCENARIO CONTROLS */}
        <div className="flood-timeline-panel">
          {/* Mode Switcher */}
          <div className="mode-toggle-group">
            <button
              type="button"
              className={`mode-toggle-btn ${appMode === 'LIVE' ? 'active' : ''}`}
              onClick={() => handleSetMode('LIVE')}
            >
              <span className="font-medium text-base">LIVE FORECAST</span>
            </button>
            {/* ... */}
          </div>
          
          {/* Historical Controls - Improved typography */}
          {appMode === 'HISTORICAL' ? (
            <>
              <div className="timeline-header">
                <span className="timeline-heading text-lg font-semibold tracking-[-0.5px]">
                  29 AUG 2017 REPLAY
                </span>
                <span className="timeline-active-tag text-sm font-semibold">
                  Step {historicalStep + 1}/24
                </span>
              </div>
              {/* ... */}
            </>
          ) : !isScenarioMode ? (
            <>
              <div className="timeline-header">
                <span className="timeline-heading text-lg font-semibold tracking-[-0.5px]">
                  FLOOD OUTLOOK
                </span>
                <span className="timeline-active-tag text-sm font-semibold">
                  Active: {currentHorizonConfig.label}
                </span>
              </div>
              {/* ... */}
            </>
          ) : (
            <>
              <div className="timeline-header">
                <span className="timeline-heading text-lg font-semibold tracking-[-0.5px]" 
                        style={{ color: '#0369a1' }}>
                  RAINFALL SCENARIOS
                </span>
                <span className="timeline-active-tag text-sm font-semibold"
                        style={{ background: '#e0f2fe', color: '#0369a1' }}>
                  {activeScenario} mm/h
                </span>
              </div>
              {/* ... */}
            </>
          )}
        </div>
        
        {/* ... */}
        
        {/* FLOOD STATUS & RISK ASSESSMENT PANEL */}
        <div className="flood-status-panel">
          <div className="status-panel-top">
            <div className="status-horizon-kicker text-xs font-semibold text-uppercase tracking-wider">
              {statusKicker}
            </div>
            <div className="status-horizon-title text-2xl font-extrabold tracking-[-0.5px]">
              {statusTitle}
            </div>
          </div>
          
          {/* PRIMARY HERO CALLOUT: RISK & PEAK DEPTH */}
          <div
            className="status-hero-card"
            style={{
              backgroundColor: riskInfo.bannerBg,
              borderColor: riskInfo.bannerBorder
            }}
          >
            <div className="hero-risk-header flex justify-between items-center">
              <span className="hero-risk-kicker text-xs font-semibold text-uppercase tracking-wider"
                    style={{ color: riskInfo.textCol }}>
                {isHistoricalMode ? 'SIMULATED RISK' : isScenarioMode ? 'SCENARIO RISK' : 'PREDICTED RISK'}
              </span>
              <span className={`hero-risk-badge ${riskInfo.badgeClass}` 
                          text-xs font-semibold px-2.5 py-0.5 rounded}>
                {riskInfo.text}
              </span>
            </div>
            
            <div className="hero-depth-row flex justify-between items-baseline">
              <div className="depth-digit-group flex items-baseline">
                <span className="depth-large text-5xl font-extrabold tracking-[-1px] "
                      style={{ color: riskInfo.depthCol }}>
                  {Number(maxDepthM).toFixed(2)}
                </span>
                <span className="depth-metric-unit text-lg font-bold">
                  m
                </span>
              </div>
              
              <div className="depth-context-label text-right">
                <div className="context-primary text-base font-semibold">
                  Peak Inundation
                </div>
                <div className="context-secondary text-sm font-medium">
                  {Math.round(maxDepthM * 100)} cm depth
                </div>
              </div>
            </div>
            
            <div className="hero-impact-note text-sm font-medium"
                  style={{ color: riskInfo.textCol }}>
              {riskInfo.description}
            </div>
          </div>
          
          {/* SECONDARY METRICS GRID */}
          <div className="status-metric-grid grid grid-cols-2 gap-4">
            <div className="grid-metric-box">
              <span className="metric-box-label text-xs font-semibold text-uppercase tracking-wider">
                {rainfallMetricLabel}
              </span>
              <span className="metric-box-val text-2xl font-bold">
                {rainfallMetricVal}{' '}
                <span className="sub-unit text-xs">mm</span>
              </span>
              <span className="metric-box-sub text-xs font-medium">
                {rainfallMetricSub}
              </span>
            </div>
            
            <div className="grid-metric-box">
              <span className="metric-box-label text-xs font-semibold text-uppercase tracking-wider">
                INUNDATED AREA
              </span>
              <span className="metric-box-val text-xl font-semibold">
                {Math.round(floodedAreaM2)} <span className="sub-unit text-xs">m²</span>
              </span>
              <span className="metric-box-sub text-xs font-medium">
                30m DEM grid
              </span>
            </div>
          </div>
          
          {/* SIMULATION SUMMARY FOOTER */}
          <div className="status-panel-footer">
            <div className="footer-engine-title text-xs font-semibold text-uppercase tracking-wider">
              MODEL PIPELINE
            </div>
            <div className="footer-engine-desc text-sm font-medium">
              Rainfall–runoff + drainage capacity + surface routing
            </div>
            <div className="footer-engine-param text-xs font-medium">
              {isHistoricalMode
                ? 'Conveyance: 100% capacity • 78 inlets • Runoff C = 0.7'
                : isScenarioMode && activeScenario === 20
                ? 'Conveyance: 100% capacity • 0 surcharge'
                : 'Runoff C = 0.7 • 60-minute model timestep'}
            </div>
          </div>
        </div>
        
        {/* ... other panels with similar typography improvements ... */}
      </div>
      
      {/* FLOOD DEPTH LEGEND */}
      <div className="flood-legend-card">
        <div className="legend-heading text-lg font-semibold text-uppercase tracking-[-0.5px]">
          Modelled flood depth
        </div>
        <div className="legend-space flex flex-col gap-2">
          <div className="legend-grade flex items-center gap-3">
            <span className="grade-color w-4 h-2.5 rounded" 
                  style={{ backgroundColor: 'var(--depth-0-5)' }} />
            <span className="grade-range text-base font-medium">
              0.0 – 0.5 m
            </span>
            <span className="grade-desc text-sm font-medium">
              Minor
            </span>
          </div>
          {/* ... */}
        </div>
      </div>
      
      {/* BANNERS */}
      {loading && (
        <div className="map-banner-status flex items-center gap-3">
          <span className="banner-spinner h-3 w-3 border-2 border-t-transparent 
                    rounded-full animate-spin border-primary" />
          <span className="text-base font-medium">Simulating flood nowcast...</span>
        </div>
      )}
      {error && (
        <div className="map-banner-error flex items-center gap-3">
          <span className="text-xs font-medium">⚠️</span>
          <span className="text-sm font-medium">Simulation Error: {error}</span>
        </div>
      )}
    </div>
  </div>
);
```

- [ ] **Step 3: Verify typography improvements don't break layout**

Run: `npm start` or manual verification
Expected: All text renders correctly with improved hierarchy and spacing

- [ ] **Step 4: Commit typography refinements**

```bash
git add src/App.css src/components/FloodMap.tsx
git commit -m "design: refine typography hierarchy and text styling for better readability"
```

---

### Task 3: Implement Consistent Component Styling with shadcn Principles

**Files:**
- Create: `src/components/ui/button.tsx`
- Create: `src/components/ui/badge.tsx`
- Create: `src/components/ui/alert.tsx`
- Modify: `src/components/FloodMap.tsx:800-1200` (Replace custom button/badge usage)

**Interfaces:**
- Consumes: Design tokens from Task 1
- Produces: Consistent, reusable UI components following shadcn-ui patterns

- [ ] **Step 1: Create reusable Button component following shadcn principles**

```tsx
// src/components/ui/button.tsx
import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 px-3",
        lg: "h-11 px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    }
  }
);

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof buttonVariants.__defaultProps;
  size?: keyof typeof buttonVariants.__defaultProps;
}

export { buttonVariants, type ButtonProps };
export default function Button(
  { className, variant, size, ...props }: ButtonProps
) {
  return (
    <button
      className={cn(
        buttonVariants({ variant, size, className })
      )}
      {...props}
    />
  );
}
```

- [ ] **Step 2: Create Badge component for status indicators**

```tsx
// src/components/ui/badge.tsx
import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        destructive: "border-destructive/50 text-destructive bg-destructive/50",
        outline: "border-foreground",
        success: "border-success/50 text-success bg-success/50",
        warning: "border-warning/50 text-warning bg-warning/50",
        error: "border-error/50 text-error bg-error/50",
      },
    },
    defaultVariants: {
      variant: "default",
    }
  }
);

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: keyof typeof badgeVariants.__defaultProps;
}

export { badgeVariants, type BadgeProps };
export default function Badge(
  { className, variant, ...props }: BadgeProps
) {
  return (
    <span
      className={cn(
        badgeVariants({ variant, className })
      )}
      {...props}
    />
  );
}
```

- [ ] **Step 3: Create Alert component for status messages**

```tsx
// src/components/ui/alert.tsx
import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const alertVariants = cva(
  "relative w-full rounded-lg border p-4 [&_svg]:absolute [&_svg]:left-4 [&_svg]:top-4 [&_svg]:text-foreground [&_svg:not(:first-child)]:mt-0.5",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground",
        destructive: "bg-destructive text-destructive-foreground",
        success: "bg-success text-success-foreground",
        warning: "bg-warning text-warning-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    }
  }
);

interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: keyof typeof alertVariants.__defaultProps;
  className?: string;
}

export { alertVariants, type AlertProps };
export default function Alert(
  { className, variant, ...props }: AlertProps
) {
  return (
    <div
      className={cn(
        alertVariants({ variant, className }),
        "flex items-start space-x-4"
      )}
      {...props>
    >
      <span className="shrink-0 flex h-3 w-3 items-center justify-center">
        {/* Icon would go here based on variant */}
      </span>
      <div className="space-y-1">
        <span className="text-sm font-medium">{props.title}</span>
        <div className="text-sm space-y-0.5">{props.description}</div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Create utils module for cn helper**

```tsx
// src/lib/utils.ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

- [ ] **Step 5: Update FloodMap.tsx to use new components**

```tsx
// src/components/FloodMap.tsx - Import new components
import Button from "@/components/ui/button";
import Badge from "@/components/ui/badge";
import Alert from "@/components/ui/alert";

// Replace custom button implementations
<div className="mode-toggle-group">
  <Button
    variant="outline"
    size="sm"
    className={appMode === 'LIVE' ? 'active' : ''}
    onClick={() => handleSetMode('LIVE')}
  >
    LIVE FORECAST
  </Button>
  <Button
    variant="outline"
    size="sm"
    className={appMode === 'SCENARIO' ? 'scenario-active' : ''}
    onClick={() => handleSetMode('SCENARIO')}
  >
    MODEL SCENARIO
  </Button>
  <Button
    variant="outline"
    size="sm"
    className={appMode === 'HISTORICAL' ? 'historical-active' : ''}
    onClick={() => handleSetMode('HISTORICAL')}
  >
    HISTORICAL REPLAY
  </Button>
</div>

// Replace badge usage
<span className={`badge ${riskInfo.badgeClass}`}>
  {riskInfo.text}
</span>

// Replace alert banners
{loading && (
  <Alert variant="default" className="map-banner-status">
    Simulating flood nowcast...
  </Alert>
)}
{error && (
  <Alert variant="destructive" className="map-banner-error">
    Simulation Error: {error} (Backend :8000)
  </Alert>
)}
```

- [ ] **Step 6: Verify component replacements work correctly**

Run: `npm start` or manual verification
Expected: All buttons, badges, and alerts function correctly with new styling

- [ ] **Step 7: Commit component implementation**

```bash
git add src/components/ui/button.tsx src/components/ui/badge.tsx src/components/ui/alert.tsx src/lib/utils.ts src/components/FloodMap.tsx
git commit -m "design: implement consistent UI components following shadcn principles"
```

---

### Task 4: Add Purposeful Animations and Transitions

**Files:**
- Modify: `src/index.css:1-20` (Add animation utilities)
- Modify: `src/App.css:1160-1210` (Update banners and popups)
- Modify: `src/components/FloodMap.tsx:1160-1210` (Add transition classes)

**Interfaces:**
- Consumes: Design tokens from Task 1
- Produces: Subtle, purposeful animations for user feedback and state changes

- [ ] **Step 1: Add animation utilities to index.css**

```css
/* src/index.css - Add after imports */
/* Animation utilities */
@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes ping {
  75%, 100% {
    transform: scale(2);
    opacity: 0;
  }
}

@keyframes pulse {
  50% {
    opacity: .5;
  }
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(-25%);
    animation-timing-function: cubic-bezier(0.8,0,1,1);
  }
  50% {
    transform: translateY(0);
    animation-timing-function: cubic-bezier(0,0,0.2,1);
  }
}

/* Transition utilities */
.transition-all {
  transition-property: all;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
}

.transition-colors {
  transition-property: background-color, border-color, color, fill, stroke;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
}

.transition-opacity {
  transition-property: opacity;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
}

.transition-shadow {
  transition-property: box-shadow;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
}

.duration-100 {
  transition-duration: 100ms;
}
.duration-150 {
  transition-duration: 150ms;
}
.duration-200 {
  transition-duration: 200ms;
}
.duration-300 {
  transition-duration: 300ms;
}
.duration-500 {
  transition-duration: 500ms;
}

.ease-linear {
  transition-timing-function: linear;
}
.ease-in {
  transition-timing-function: cubic-bezier(0.4, 0, 1, 1);
}
.ease-out {
  transition-timing-function: cubic-bezier(0, 0, 0.2, 1);
}
.ease-in-out {
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}

/* Animation classes */
.animate-spin {
  animation: spin 1s linear infinite;
}
.animate-ping {
  animation: ping 1s cubic-bezier(0, 0, 0.2, 1) infinite;
}
.animate-pulse {
  animation: pulse 2s cubic-bezier(0 diaz, 0.2, 1) infinite;
}
.animate-bounce {
  animation: bounce 1s infinite;
}
```

- [ ] **Step 2: Update banner animations in App.css**

```css
/* src/App.css - Update banner styles */
.map-banner-status, .map-banner-error {
  /* ... existing styles ... */
  animation: slide-down 0.3s ease-out;
}

@keyframes slide-down {
  from {
    opacity: 0;
    transform: translateY(-100%);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.banner-spinner {
  width: 12px;
  height: 12px;
  border: 2px solid var(--primary);
  border-top-color: transparent;
  border-radius: 50%;
  display: inline-block;
  animation: spin 0.8s linear infinite;
}
```

- [ ] **Step 3: Add transition classes to FloodMap.tsx elements**

```tsx
// src/components/FloodMap.tsx - Add transitions to interactive elements
<div className="map-left-overlay">
  {/* ... */}
  
  {/* Buttons with hover transitions */}
  <Button
    variant="outline"
    size="sm"
    className={cn(
      appMode === 'LIVE' ? 'active' : '',
      "transition-all duration-150 ease-in-out"
    )}
    onClick={() => handleSetMode('LIVE')}
  >
    LIVE FORECAST
  </Button>
  {/* ... */}
  
  {/* Timeline buttons */}
  {horizons.map((h) => {
    const isSelected = activeHorizon === h.key;
    return (
      <Button
        key={h.key}
        variant="outline"
        size="sm"
        className={cn(
          isSelected ? 'active' : '',
          "transition-all duration-150 ease-in-out"
        )}
        onClick={() => handleHorizonChange(h.key)}
      >
        <span className="step-time text-sm font-medium">{h.label}</span>
        <span className="step-rain-tag text-xs font-mono">
          {h.rainfallMm !== null ? `${h.rainfallMm.toFixed(1)}mm` : '--mm'}
        </span>
      </Button>
    );
  })}
  
  {/* ... */}
  
  {/* Map extent buttons */}
  <div className="map-extent-tools">
    <Button
      variant="outline"
      size="sm"
      className="transition-all duration-150 ease-in-out"
      onClick={handleResetOverview}
      title="Reset to full Mumbai region"
    >
      ⛶ Full Extent (Mumbai)
    </Button>
    <Button
      variant="outline"
      size="sm"
      className="highlight transition-all duration-150 ease-in-out"
      onClick={handleFocusFloodParcel}
      title="Center on Mumbai pilot zone (Kurla / SCLR)"
    >
      🎯 Target Zone (Kurla)
    </Button>
  </div>
</div>
```

- [ ] **Step 4: Add hover effects to map layers**

```tsx
// src/components/FloodMap.tsx - Add hover effects in map initialization
newMap.on('mouseenter', 'flood-depth-layer', () => {
  newMap.getCanvas().style.cursor = 'pointer';
  // Add subtle pulse effect to indicate interactivity
  // (This would require custom layer manipulation or overlay)
});
newMap.on('mouseleave', 'flood-depth-layer', () => {
  newMap.getCanvas().style.cursor = '';
});

// Similar for roads and intersections layers
```

- [ ] **Step 5: Verify animations work correctly**

Run: `npm start` or manual verification
Expected: Subtle animations on banners, buttons, and interactive elements

- [ ] **Step 6: Commit animation implementation**

```bash
git add src/index.css src/App.tsx src/components/FloodMap.tsx
git commit -m "design: add purposeful animations and transitions for user feedback"
```

---

### Task 5: Refine Map Styling and Layer Visual Hierarchy

**Files:**
- Modify: `src/components/FloodMap.tsx:530-650` (Map layer styling)
- Modify: `src/App.css` (Map-related CSS variables if needed)

**Interfaces:**
- Consumes: Design tokens from Task 1
- Produces: Improved visual hierarchy and readability of map layers

- [ ] **Step 1: Enhance flood depth layer styling for better data representation**

```tsx
// src/components/FloodMap.tsx - Update flood depth layer (around line 530)
// Flood polygon fill with improved visual encoding
newMap.addLayer({
  id: 'flood-depth-layer',
  type: 'fill',
  source: 'flood-depth',
  paint: {
    'fill-color': [
      'interpolate',
      ['linear'],
      ['get', 'depth'],
      0, 'var(--hydro-no-water)',           /* 0m - no water */
      0.1, 'var(--hydro-minimal)',          /* 0.1m - minimal */
      0.25, 'var(--hydro-light)',           /* 0.25m - light */
      0.5, 'var(--hydro-moderate)',         /* 0.5m - moderate */
      1.0, 'var(--hydro-significant)',      /* 1.0m - significant */
      1.5, 'var(--hydro-high)',             /* 1.5m - high */
      2.0, 'var(--hydro-severe)',           /* 2.0m - severe */
      2.5, 'var(--hydro-extreme)',          /* 2.5m+ - extreme */
      3.0, 'var(--hydro-extreme)'           /* 3.0m+ - extreme */
    ],
    'fill-opacity': [
      'case',
      ['boolean', ['feature-state', 'hover'], false],
      0.7,
      0.85
    ]
  }
});

// Add hover state for depth layer
newMap.addLayer({
  id: 'flood-depth-hover',
  type: 'fill',
  source: 'flood-depth',
  filter: ['==', 'active', true],
  paint: {
    'fill-color': 'var(--alert-clear)',
    'fill-opacity': 0.1
  }
});

// Outer boundary stroke (more subtle)
newMap.addLayer({
  id: 'flood-depth-halo',
  type: 'line',
  source: 'flood-depth',
  paint: {
    'line-color': 'var(--hydro-extreme)',
    'line-width': [
      'interpolate',
      ['linear'],
      ['zoom'],
      11, 1.0,
      14, 2.0,
      17, 3.0
    ],
    'line-opacity': 0.1
  }
});

// Subtle water perimeter edge (more defined)
newMap.addLayer({
  id: 'flood-depth-outline',
  type: 'line',
  source: 'flood-depth',
  paint: {
    'line-color': 'var(--alert-clear)',
    'line-width': [
      'interpolate',
      ['linear'],
      ['zoom'],
      11, 0.5,
      14, 1.0,
      17, 1.5
    ],
    'line-opacity': 0.4
  }
});

// Update roads layer styling for better hierarchy
newMap.addLayer({
  id: 'affected-roads-layer',
  type: 'line',
  source: 'affected-roads',
  layout: {
    'line-join': 'round',
    'line-cap': 'round',
    'visibility': 'visible',
  },
  paint: {
    'line-color': [
      'match',
      ['get', 'risk_level'],
      'CRITICAL', 'var(--status-critical)',
      'HIGH', 'var(--status-warning)',
      'MEDIUM', 'var(--status-advisory)',
      'LOW', 'var(--status-normal)',
      'var(--alert-clear)'
    ],
    'line-width': [
      'interpolate',
      ['linear'],
      ['zoom'],
      11, 2.0,
      14, 3.0,
      17, 4.0
    ],
    'line-opacity': 0.9
  }
});

// Update intersections layer styling
newMap.addLayer({
  id: 'affected-intersections-layer',
  type: 'circle',
  source: 'affected-intersections',
  layout: {
    'visibility': 'visible',
  },
  paint: {
    'circle-radius': [
      'interpolate',
      ['linear'],
      ['zoom'],
      11, 3.5,
      14, 5.5,
      17, 8.5
    ],
    'circle-color': [
      'match',
      ['get', 'risk_level'],
      'CRITICAL', 'var(--status-critical)',
      'HIGH', 'var(--status-warning)',
      'MEDIUM', 'var(--status-advisory)',
      'LOW', 'var(--status-normal)',
      'var(--alert-clear)'
    ],
    'circle-stroke-width': 2,
    'circle-stroke-color': '#ffffff',
    'circle-opacity': 0.9
  }
});

// Update historical benchmarks layer
newMap.addLayer({
  id: 'historical-benchmarks-layer',
  type: 'circle',
  source: 'historical-benchmarks',
  layout: {
    'visibility': 'none',
  },
  paint: {
    'circle-radius': [
      'interpolate',
      ['linear'],
      ['zoom'],
      11, 4.0,
      14, 6.0,
      17, 9.0
    ],
    'circle-color': 'var(--evaporation)',  /* Using existing evaporation token */
    'circle-stroke-width': 2,
    'circle-stroke-color': '#ffffff',
    'circle-opacity': 1.0
  }
});
```

- [ ] **Step 2: Update popup styling for better readability**

```tsx
// src/components/FloodMap.tsx - Update popup styling (around line 700)
// Update to use design tokens and better typography
popupRef.current = new Popup({ 
  closeButton: true, 
  closeOnClick: true, 
  className: 'ops-popup' 
})
.setLngLat(e.lngLat)
.setHTML(`
  <div class="popup-box">
    <div class="popup-header">
      <span className="popup-title text-sm font-semibold">${headingText}</span>
      <span className="popup-badge ${risk.badgeClass} text-xs font-semibold px-2 py-0.5 rounded">
        ${risk.text}
      </span>
    </div>
    <div className="popup-body space-y-3">
      ${depthDisplayRow}
      <div className="popup-row">
        <span className="lbl text-xs font-medium">Risk classification:</span>
        <span className="val text-sm font-medium">${risk.text}</span>
      </div>
      ${horizonOrScenarioRow}
      <div className="popup-row">
        <span className="lbl text-xs font-medium">Rainfall source:</span>
        <span className="val text-xs">${rainfallSourceVal}</span>
      </div>
      <div className="popup-row">
        <span className="lbl text-xs font-medium">Data status:</span>
        <span className="val text-xs status-modelled">${dataStatusVal}</span>
      </div>
    </div>
  </div>
`)
.addTo(newMap);
```

- [ ] **Step 3: Update popup CSS in App.css for consistency**

```css
/* src/App.css - Update popup styling */
.ops-popup .maplibregl-popup-content {
  padding: 12px 16px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--slate-200);
  background: var(--slate-50);
  min-width: 240px;
}

.popup-box {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--slate-200);
  padding-bottom: var(--spacing-2);
}

.popup-title {
  font-size: var(--text-base);
  font-weight: var(--font-bold);
  letter-spacing: var(--tracking-tight);
  color: var(--slate-900);
}

.popup-badge {
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  padding: var(--spacing-1) var(--spacing-2);
  border-radius: var(--radius-sm);
}

.popup-body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.popup-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--text-sm);
}

.popup-row .lbl {
  color: var(--slate-500);
  font-weight: var(--font-medium);
}

.popup-row .val {
  font-weight: var(--font-semibold);
  color: var(--slate-900);
}

.popup-row .val.bold {
  color: var(--status-warning); /* Using warning color for emphasis */
  font-family: var(--font-mono, monospace);
}

.popup-row .status-modelled {
  color: var(--evaporation);
  font-size: var(--text-xs);
}
```

- [ ] **Step 4: Verify map styling improvements**

Run: `npm start` or manual verification
Expected: Map layers have improved visual hierarchy, better color distinctions, and improved popup readability

- [ ] **Step 5: Commit map styling refinements**

```bash
git add src/components/FloodMap.tsx src/App.css
git commit -m "design: refine map layer styling and popup visual hierarchy"
```

---

### Task 6: Final Polish and Accessibility Verification

**Files:**
- Modify: `src/components/FloodMap.tsx` (Add accessibility attributes)
- Modify: `src/index.css` (Add focus-visible styles)
- Create: `src/styles/accessibility.css` (Optional accessibility enhancements)

**Interfaces:**
- Consumes: All previous tasks
- Produces: Fully accessible, polished UI meeting WCAG AA standards

- [ ] **Step 1: Add focus-visible styles for keyboard navigation**

```css
/* src/index.css - Add after animation utilities */
/* Focus visible styles for accessibility */
:focus-visible {
  outline: 2px solid var(--ring-offset-background);
  outline-offset: 2px solid var(--ring);
}

.ring {
  --tw-ring-offset-shadow: var(--ring-offset-width) 0 0 #0000;
  --tw-ring-shadow: var(--ring-offset-width) 0 0 
    calc(var(--ring-offset-width) + var(--ring-width)) 
    var(--ring-color);
  box-shadow: var(--ring-offset-shadow), var(--ring-shadow);
}

.ring-primary {
  --ring-color: var(--primary);
}

.ring-secondary {
  --ring-color: var(--secondary);
}

.ring-inset {
  box-shadow: inset var(--ring-offset-width) 0 0 0 
    calc(var(--ring-offset-width) + var(--ring-width)) 
    var(--ring-color);
}

[aria-label] {
  cursor: pointer;
}
```

- [ ] **Step 2: Add accessibility attributes to interactive elements**

```tsx
// src/components/FloodMap.tsx - Add accessibility to controls
<div className="mode-toggle-group">
  <Button
    variant="outline"
    size="sm"
    className={cn(
      appMode === 'LIVE' ? 'active' : '',
      "transition-all duration-150 ease-in-out focus-visible:ring-2 focus-visible:ring-primary"
    )}
    onClick={() => handleSetMode('LIVE')}
    aria-label="Switch to live forecast mode"
  >
    LIVE FORECAST
  </Button>
  <Button
    variant="outline"
    size="sm"
    className={cn(
      appMode === 'SCENARIO' ? 'scenario-active' : '',
      "transition-all duration-150 ease-in-out focus-visible:ring-2 focus-visible:ring-primary"
    )}
    onClick={() => handleSetMode('SCENARIO')}
    aria-label="Switch to model scenario mode"
  >
    MODEL SCENARIO
  </Button>
  <Button
    variant="outline"
    size="sm"
    className={cn(
      appMode === 'HISTORICAL' ? 'historical-active' : '',
      "transition-all duration-150 ease-in-out focus-visible:ring-2 focus-visible:ring-primary"
    )}
    onClick={() => handleSetMode('HISTORICAL')}
    aria-label="Switch to historical replay mode"
  >
    HISTORICAL REPLAY
  </Button>
</div>

// Add to timeline buttons
{horizons.map((h) => {
  const isSelected = activeHorizon === h.key;
  return (
    <Button
      key={h.key}
      variant="outline"
      size="sm"
      className={cn(
        isSelected ? 'active' : '',
        "transition-all duration-150 ease-in-out focus-visible:ring-2 focus-visible:ring-primary"
      )}
      onClick={() => handleHorizonChange(h.key)}
      aria-label={`Select ${h.label} horizon`}
    >
      <span className="step-time text-sm font-medium">{h.label}</span>
      <span className="step-rain-tag text-xs font-mono">
        {h.rainfallMm !== null ? `${h.rainfallMm.toFixed(1)}mm` : '--mm'}
      </span>
    </Button>
  );
})}

// Add to scenario buttons
{SCENARIO_VALUES.map((sc) => {
  const isSelected = activeScenario === sc;
  return (
    <Button
      key={sc}
      variant="outline"
      size="sm"
      className={cn(
        isSelected ? 'selected scenario-selected' : '',
        "transition-all duration-150 ease-in-out focus-visible:ring-2 focus-visible:ring-primary"
      )}
      onClick={() => handleSelectScenario(sc)}
      aria-label={`Select ${sc} mm/h rainfall scenario`}
    >
      <span className="step-time text-sm font-medium">{sc}</span>
      <span className="step-rain-tag text-xs font-mono">mm/h</span>
    </Button>
  );
})}
```

- [ ] **Step 3: Add skip navigation and landmark roles**

```tsx
// src/components/FloodMap.tsx - Add to main return
return (
  <div className="flood-app" role="application">
    {/* Skip navigation for keyboard users */}
    <div className="sr-only focus-not-smaller:not-sr-only p-4">
      <a href="#main-content" className="text-sm font-medium underline underline-offset-4">
        Skip to main content
      </a>
    </div>
    
    <header className="app-topbar" role="banner">
      {/* ... */}
    </header>
    
    <div className="map-workspace" role="region" aria-label="Flood map workspace" id="main-content">
      {/* ... */}
    </div>
  </div>
);
```

Add CSS for screen-reader only class:
```css
/* src/index.css */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.focus-not-smaller:not-sr-only {
  position: static;
  width: auto;
  height: auto;
  margin: 0;
  overflow: visible;
  clip: auto;
  white-space: normal;
}
```

- [ ] **Step 4: Verify color contrast ratios**

Use browser dev tools or accessibility testing tools to verify:
- Text on background meets 4.5:1 contrast ratio (AA)
- Large text meets 3:1 contrast ratio (AA)
- UI components meet 3:1 contrast for non-text elements
- Focus indicators are visible

- [ ] **Step 5: Test keyboard navigation**

Manual test:
- Tab through all interactive elements
- Verify logical tab order
- Verify Enter/Space activates buttons
- Verify Escape closes popups
- Verify arrow keys work in sliders/dropdowns

- [ ] **Step 6: Final verification of all functionality**

Run: `npm start` or manual verification
Expected: All existing functionality works with improved UI/UX

- [ ] **Step 7: Commit accessibility and final polish**

```bash
git add src/index.css src/components/FloodMap.tsx
git commit -m "design: add accessibility enhancements and final UI/UX polish"
```

---
## Plan Summary

This implementation plan refines the flood nowcasting system's UI/UX through six interconnected tasks:

1. **Design System Foundation**: Establish industrial-inspired design tokens and color palette
2. **Typography Hierarchy**: Improve text scaling, spacing, and readability
3. **Component Consistency**: Implement reusable UI components following shadcn-ui principles
4. **Purposeful Animations**: Add subtle, meaningful animations for user feedback
5. **Map Visual Hierarchy**: Enhance map layer styling and popup readability
6. **Accessibility & Polish**: Ensure WCAG AA compliance and final refinements

Each task builds upon the previous ones and can be implemented and verified independently. The plan maintains all existing functionality while transforming the interface from a technical prototype to a professional emergency operations tool.

**Next Steps:** 
1. Review and approve this plan
2. Choose execution approach (subagent-driven or inline)
3. Begin implementation following the task order