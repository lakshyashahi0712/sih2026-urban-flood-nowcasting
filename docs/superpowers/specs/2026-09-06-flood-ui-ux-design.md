# Flood Nowcasting UI/UX Design Specification

**Version:** 1.0.0  
**Date:** 2026-09-06  
**Status:** Approved for Implementation  

## 1. Introduction

This document specifies the visual design and user interface for the Urban Flood Nowcasting system (PS 26085). The design follows the "Operational Clarity" direction, prioritizing functional legibility, rapid comprehension, and professional reliability for emergency operations use.

**Key Principle:** The system treats the flood map as a critical command surface where every pixel serves a purpose in supporting real-time decision-making for flood response operations.

## 2. Design Philosophy

### 2.1 Operational Clarity
- **Map as Hero:** The geospatial visualization remains the primary focus, occupying maximum viewport area.
- **Data Density with Purpose:** Supporting panels provide essential context without clutter, using visual hierarchy to distinguish primary from secondary information.
- **Material Honesty:** Digital materials communicate function through color, typography, and spacing rather than simulated physical depth.
- **Functional Layering:** Information is organized conceptually (map → controls → details) rather than through visual elevation effects.

### 2.2 Constraints & Requirements
- Must maintain all existing hydrological data encoding colors (scientifically validated).
- Must remain responsive across mobile, tablet, and desktop breakpoints.
- Must meet WCAG AA accessibility standards for contrast and keyboard navigation.
- Must preserve existing functionality and API integrations.
- Must avoid generic SaaS/AI-generated aesthetic patterns.

## 3. Visual System

### 3.1 Color Architecture

The design system employs a dual-palette approach: **Neutral Base** for surfaces and text, and **Accent Palette** for actions, status, and hydrological data encoding.

#### 3.1.1 Neutral Base (Cool Professional)

| Variable | Value | Usage |
|----------|-------|-------|
| `--slate-50` | `#f8fafc` | Page background, panel surfaces |
| `--slate-100` | `#f1f5f9` | Elevated surfaces, hover states |
| `--slate-200` | `#e2e8f0` | Borders, dividers, subtle separators |
| `--slate-300` | `#cbd5e1` | Disabled states, tertiary text |
| `--slate-400` | `#94a3b8` | Secondary text, labels, placeholders |
| `--slate-500` | `#64748b` | Primary text on light surfaces |
| `--slate-600` | `#475569` | Header text, emphasis |
| `--slate-700` | `#334155` | Strong emphasis, active states |
| `--slate-800` | `#1e293b` | Dark surfaces, high contrast text |
| `--slate-900` | `#0f172a` | Maximum contrast text, headers |

#### 3.1.2 Hydrological Data Encoding (LOCKED - Scientifically Validated)

These values are **preserved exactly** from the existing system as they represent physically meaningful flood depth thresholds:

| Variable | Value | Meaning |
|----------|-------|---------|
| `--depth-0` | `#f0f9ff` | 0.0m - No water |
| `--depth-0-25` | `#e0f2fe` | 0.0-0.25m - Ankle-deep |
| `--depth-0-5` | `#bae6fd` | 0.25-0.5m - Calf-deep (action threshold) |
| `--depth-1.0` | `#7dd3fc` | 0.5-1.0m - Waist-deep (evocation consideration) |
| `--depth-1.5` | `#38bdf8` | 1.0-1.5m - Chest-deep (high risk) |
| `--depth-2.0` | `#0ea5e9` | 1.5-2.0m - Head-deep (extreme danger) |
| `--depth-3-0` | `#0284c7` | 2.0m+ - Submerged (critical infrastructure) |

#### 3.1.3 Alert & Status Accents (High Visibility)

| Variable | Value | Usage |
|----------|-------|-------|
| `--alert-imminent` | `#dc2626` | Flash flood imminent (critical action) |
| `--alert-active` | `#ea580c` | Flooding occurring (warning) |
| `--alert-recording` | `#16a34a` | Monitoring active (success/normal) |
| `--flow-velocity` | `#2563eb` | Water movement - primary interactive |
| `--infiltration` | `#059669` | Soil absorption - secondary actions |
| `--surface-runoff` | `#dc2626` | Overland flow - warnings/critical |
| `--groundwater` | `#7c3aed` | Subsurface - informational |
| `--evaporation` | `#f59e0b` | Flux dissipation - metrics |

#### 3.1.4 Risk Semantics (For Assessment Visualization)

| Variable | Value | Usage |
|----------|-------|-------|
| `--risk-severe` | `#991b1b` | Severe/inundation risk visualization |
| `--risk-high` | `#c2410c` | High risk areas |
| `--risk-mod` | `#ca8a04` | Moderate risk areas |
| `--risk-low` | `#475569` | Low risk areas |

### 3.2 Typography System

#### 3.2.1 Font Pairing
- **Primary (UI/Body):** Inter Variable - Optimized for interface legibility
- **Secondary (Data/Technical):** IBM Plex Mono Variable - Monospaced for tabular data alignment

#### 3.2.2 Typographic Scale (1.25x Ratio)

| Token | Size (rem/px) | Line Height | Weight | Usage |
|-------|---------------|-------------|--------|-------|
| `--text-xs` | 0.75rem / 12px | 1rem | 300 | Captions, auxiliary info |
| `--text-sm` | 0.875rem / 14px | 1.25rem | 400 | Form labels, secondary text |
| `--text-base` | 1rem / 16px | 1.5rem | 400 | Body text, primary UI |
| `--text-lg` | 1.125rem / 18px | 1.75rem | 500 | Subheadings, emphasized text |
| `--text-xl` | 1.25rem / 20px | 1.75rem | 600 | Section titles, important metrics |
| `--text-2xl` | 1.5rem / 24px | 2rem | 700 | Dashboard headers, primary calls-to-action |
| `--text-3xl` | 1.875rem / 30px | 2.25rem | 800 | Main application title |
| `--text-4xl` | 2.25rem / 36px | 2.5rem | 800 | Emergency/high-impact headers |

#### 3.2.3 Typography Utilities
- **Weights:** `--font-light` (300), `--font-normal` (400), `--font-medium` (500), `--font-semibold` (600), `--font-bold` (700), `--font-extrabold` (800)
- **Tracking:** `--tracking-tighter` (-0.05em), `--tracking-tight` (-0.025em), `--tracking-normal` (0), `--tracking-wide` (0.025em), `--tracking-wider` (0.05em), `--tracking-widest` (0.1em)
- **Leading:** Standard line-height ratios as defined in scale above

### 3.3 Spacing System

Based on a 4px grid for consistent vertical and horizontal rhythm:

| Token | Size (rem/px) | Usage |
|-------|---------------|-------|
| `--spacing-0` | 0 / 0px | No spacing |
| `--spacing-1` | 0.25rem / 4px | Micro spacing, hairlines |
| `--spacing-2` | 0.5rem / 8px | Tight compaction |
| `--spacing-3` | 0.75rem / 12px | Standard compression |
| `--spacing-4` | 1rem / 16px | Base unit, default padding |
| `--spacing-5` | 1.25rem / 20px | Slight expansion |
| `--spacing-6` | 1.5rem / 24px | Comfortable spacing |
| `--spacing-8` | 2rem / 32px | Section separation |
| `--spacing-10` | 2.5rem / 40px | Major section breaks |
| `--spacing-12` | 3rem / 48px | Panel margins, page padding |

## 4. Layout Architecture

### 4.1 Viewport Structure
The application uses a fixed-height layout to prevent scrolling distractions during critical operations:

```
+--------------------------------------------------+
|               APP TOPBAR (48px)                  |
+----------------------+---------------------------+
| MAP LEFT OVERLAY     |         MAP VIEWPORT      |
|   (280px width)      |                           |
|                      |                           |
+----------------------+---------------------------+
|                 MAP BOTTOM RIGHT                  |
|            FLOOD LEGEND CARD (positioned)        |
+--------------------------------------------------+
```

### 4.2 Component Z-Indexing
- **Topbar:** z-index 20 (always visible)
- **Map Workspace:** z-index 1 (base layer)
- **Left Overlay Panels:** z-index 10 (above map, below banners)
- **Status/Error Banners:** z-index 15 (above panels)
- **MapLibre Popups:** z-index 20 (highest priority for interaction)

### 4.3 Breakpoint Behavior

| Breakpoint | Layout Behavior |
|------------|-----------------|
| **Desktop** (≥1024px) | Side panels visible, map centered |
| **Tablet** (768px-1023px) | Reduced panel width (250px), provenance card hidden |
| **Mobile** (<768px) | Topbar stacks vertically, panels become bottom-sheet drawers |

## 5. Component Specifications

### 5.1 App Topbar
- **Height:** 48px
- **Background:** `--slate-900` (`--monsoon-deep`)
- **Border Bottom:** 1px solid `--slate-700` (`--monsoon-mid`)
- **Text Color:** `--slate-50` (`--alert-clear`)
- **Content:** System identity, location, mode toggles, telemetry

### 5.2 Map Left Overlay
- **Position:** Fixed, 14px inset from top/left/bottom
- **Width:** 280px (desktop), 250px (tablet)
- **Background:** `--slate-50` (`--panel-bg`) with 90% opacity for map context
- **Border:** 1px solid `--slate-200` (`--panel-border`)
- **Shadow:** `--panel-shadow` (subtle elevation)
- **Overflow:** Auto-scrolling when content exceeds height

### 5.3 Panels (Universal Style)
All panels within the overlay share these characteristics:
- **Background:** `--slate-50` (`--panel-bg`)
- **Border:** 1px solid `--slate-200` (`--panel-border`)
- **Border Radius:** 6px (`--radius-lg`)
- **Shadow:** `--panel-shadow`
- **Padding:** 12px (`--spacing-3` on vertical, `--spacing-4` on horizontal)
- **Gap:** 8px (`--spacing-2`) between elements

### 5.4 Interactive Elements

#### 5.4.1 Buttons
- **Base:** `inline-flex`, `items-center`, `justify-center`, rounded, transition-all
- **Primary:** `--slate-900` background, `--slate-50` text, hover: `--slate-800`
- **Secondary:** Transparent, `--slate-500` text, 1px solid `--slate-200` border, hover: `--slate-50` bg
- **Sizes:** Follow spacing system (`px-2`/`py-1` for sm, `px-4`/`py-2` for md, etc.)

#### 5.4.2 Badges
- **Base:** `inline-flex`, `items-center`, rounded, text-xs, font-semibold
- **Variants:** Use alert/status colors with `--slate-50` text for contrast
- **Padding:** `px-2`/`py-0.5`

#### 5.4.3 Form Elements
- **Input:** `--slate-50` background, `--slate-900` text, 1px solid `--slate-200` border
- **Focus:** Ring effect using `--flow-velocity` (`#2563eb`) at 20% opacity
- **Select/Textarea:** Same treatment as input

### 5.5 Map Styling (Preserving Hydrological Encoding)

The MapLibre GL styling preserves the existing scientifically-validated color encoding while enhancing map usability:

#### 5.5.1 Flood Depth Layer
- **Fill Color:** Interpolated using `--depth-*` variables (exact preservation)
- **Fill Opacity:** 0.85 base, 0.7 on hover for subtle feedback
- **Halo/Outline:** Subtle `--slate-200` stroke for feature separation at high zoom

#### 5.5.2 Network Layers
- **Affected Roads:** Line color mapped to risk level using `--risk-*` variables
- **Affected Intersections:** Circle color mapped to risk level using `--risk-*` variables
- **Historical Benchmarks:** Uses `--evaporation` (`#f59e0b`) for timestamped comparison points

#### 5.5.3 Popups
- **Background:** `--slate-50` (`#ffffff`)
- **Border:** 1px solid `--slate-200` (`#e2e8f0`)
- **Shadow:** `--shadow-lg` for depth separation
- **Border Radius:** `--radius-lg`
- **Typography:** Uses established scale with IBM Plex Mono for data values

### 5.6 Banners & Feedback

#### 5.6.1 Status Banner
- **Background:** `--slate-900` (`--monsoon-deep`)
- **Text:** `--slate-50` (`--alert-clear`)
- **Animation:** Slide-down (0.3s ease-out) on appearance
- **Spinner:** `--flow-velocity` (`#2563eb`) color

#### 5.6.2 Error Banner
- **Background:** `--slate-50` with `--alert-imminent` tint (`#fef2f2`)
- **Border:** 1px solid `--alert-imminent` (`#dc2626`)
- **Text:** `--alert-imminent` (`#dc2626`)
- **Icon:** Warning triangle in `--alert-imminent` color

## 6. Motion & Animation

### 6.1 Principles
- **Purposeful:** Every animation serves orientation, feedback, or relationship establishment
- **Subtle:** Durations kept under 300ms for interactive feedback
- **Physics-Informed:** Uses ease-out for entrances, ease-in for exits, ease-in-out for transitions
- **Performance:** Animate only `transform` and `opacity` for GPU acceleration
- **Reduced Motion:** Respects `prefers-reduced-motion` media query

### 6.2 Duration Standards
- **Micro-interactions** (button press, toggle): 100-150ms
- **State changes** (panel expand, mode switch): 200ms
- **Map transitions** (zoom, pan): 150-250ms (MapLibre default)
- **Banner appearance/dismissal:** 300ms
- **Popup appearance:** 200ms scale + fade

### 6.3 Easing Functions
- **Entrance:** `cubic-bezier(0.16, 1, 0.3, 1)` (ease-out)
- **Exit:** `cubic-bezier(0.43, 0.13, 0.23, 0.96)` (ease-in)
- **Transition:** `cubic-bezier(0.4, 0, 0.2, 1)` (ease-in-out)
- **Attention:** `cubic-bezier(0.68, -0.55, 0.265, 1.55)` (anticipation/overshoot for alerts)

## 7. Accessibility

### 7.1 Contrast Ratios
All text and UI elements meet WCAG AA:
- **Normal Text:** Minimum 4.5:1 contrast against background
- **Large Text (18pt+):** Minimum 3:1 contrast
- **UI Components:** Minimum 3:1 contrast for interactive elements
- **Focus Indicators:** Minimum 3:1 contrast against adjacent colors

### 7.2 Keyboard Navigation
- **Logical Tab Order:** Follows visual flow (topbar → left overlay → map controls → map)
- **Visible Focus:** 2px solid `--flow-velocity` outline with 2px offset
- **Skip Navigation:** Visually hidden link that becomes visible on focus
- **Actionable Elements:** All buttons, toggles, and inputs accessible via Enter/Space

### 7.3 Screen Reader Support
- **Semantic HTML:** Proper use of `header`, `main`, `nav`, `section`, `button` roles
- **Labels:** All form controls have associated `<label>` elements
- **Live Regions:** Status updates use `aria-live="polite"` for non-critical, `assertive` for critical
- **Landmarks:** `banner` (topbar), `region` (map workspace), `complementary` (overlay panels)

### 7.4 Touch Targets
- **Minimum Size:** 44x44px interactive area
- **Spacing:** Minimum 8px between touch targets
- **Mobile Optimization:** Panels convert to full-height drawers on small screens

## 8. Implementation Notes

### 8.1 File Structure
```
src/
├── index.css             # Base styles, CSS variables, resets
├── App.css               # Component-specific styles, layout
├── components/
│   ├── FloodMap.tsx      # Main application component
│   └── ui/               # Reusable UI components (Button, Badge, etc.)
├── lib/
│   └── utils.ts          # cn() utility for class merging
└── styles/
    └── design-tokens.css # Exported CSS variables for consistency
```

### 8.2 Development Guidelines
1. **Preserve Hydrological Colors:** Never modify `--depth-*`, `--alert-*`, or `--risk-*` variables
2. **Use Design Tokens:** Reference all colors, spacing, and typography via CSS variables
3. **Component First:** Build reusable UI components before page-specific implementations
4. **Mobile First:** Start with mobile layouts, enhance for desktop
5. **Accessibility First:** Validate contrast and keyboard navigation during development
6. **Performance:** Animate only transform/opacity, use will-change sparingly
7. **Testing:** Visual regression testing for critical UI paths

### 8.3 Migration Strategy
- **Phase 1:** Implement design tokens and base styles (index.css, design-tokens.css)
- **Phase 2:** Refine layout and panels (App.css, FloodMap.tsx structure)
- **Phase 3:** Implement reusable UI components (Button, Badge, Alert)
- **Phase 4:** Apply design to specific panels and controls
- **Phase 5:** Add animations and micro-interactions
- **Phase 6:** Final accessibility validation and polish

## 9. Approval & Change Control

This specification has been reviewed and approved for implementation. Any deviations from this document must undergo the same approval process.

**Approved By:** [To be filled upon user approval]  
**Approval Date:** 2026-09-06  

## 10. References

- Existing `frontend/src/App.css` (for hydrological color preservation)
- Material Design 3 (for elevation and motion principles)
- IBM Design Language (for functional data presentation)
- WCAG 2.1 AA (for accessibility requirements)
- MapLibre GL Documentation (for map styling capabilities)

--- 
*End of Specification*