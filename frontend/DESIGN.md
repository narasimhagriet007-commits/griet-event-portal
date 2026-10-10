---
name: GRIET Pulse
colors:
  surface: '#0b1326'
  surface-dim: '#0b1326'
  surface-bright: '#31394d'
  surface-container-lowest: '#060e20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3d'
  surface-container-highest: '#2d3449'
  on-surface: '#dae2fd'
  on-surface-variant: '#c8c5d0'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#928f9a'
  outline-variant: '#47464f'
  surface-tint: '#c4c1fb'
  primary: '#c4c1fb'
  on-primary: '#2d2a5b'
  primary-container: '#1e1b4b'
  on-primary-container: '#8683ba'
  inverse-primary: '#5b598c'
  secondary: '#4edea3'
  on-secondary: '#003824'
  secondary-container: '#00a572'
  on-secondary-container: '#00311f'
  tertiary: '#68dba9'
  on-tertiary: '#003825'
  tertiary-container: '#002819'
  on-tertiary-container: '#179c6e'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e3dfff'
  primary-fixed-dim: '#c4c1fb'
  on-primary-fixed: '#181445'
  on-primary-fixed-variant: '#444173'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#85f8c4'
  tertiary-fixed-dim: '#68dba9'
  on-tertiary-fixed: '#002114'
  on-tertiary-fixed-variant: '#005137'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
typography:
  display-xl:
    fontFamily: Outfit
    fontSize: 56px
    fontWeight: '700'
    lineHeight: 64px
  display-xl-mobile:
    fontFamily: Outfit
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
  headline-lg:
    fontFamily: Outfit
    fontSize: 40px
    fontWeight: '600'
    lineHeight: 48px
  headline-lg-mobile:
    fontFamily: Outfit
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
  headline-md:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  title-lg:
    fontFamily: Outfit
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  title-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 22px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
  label-xs:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system expresses a forward-leaning, high-caliber collegiate engineering ethos. It marries academic prestige with student-driven technological innovation. The interface must communicate institutional trust, precision engineering, and dynamic energy for hackathons, technical symposiums, cultural fests, and workshops.

The visual style blends **Modern Technical Glassmorphism** with crisp, structural clarity:
- **Atmosphere:** Deep nocturnal backgrounds overlaid with controlled translucent surfaces, high-contrast typography, and luminescent emerald accents.
- **Tone:** Methodical, high-energy, prestigious, and frictionless.
- **Visual Mechanics:** Frosted surface layers (`backdrop-filter: blur()`), fine geometric hairline strokes, sharp status badges, and luminous focus states optimized for quick scanning and streamlined registration workflows.

## Colors

The palette establishes a high-contrast nocturnal baseline punctuated by vibrant technological green highlights:

- **Primary Canvas & Overlays (`#1E1B4B` & `#0F172A`):** The primary deep indigo provides structural weight, used in conjunction with ultra-dark slate neutrals (`#0B0F19`, `#0F172A`) for foundational page background canvases, modal underlays, and structural container grouping.
- **Accents & Indicators (`#10B981` & `#059669`):** Radiant emerald drives primary CTAs, active registration states, live hackathon beacons, verified badge pills, and successful payment verifications.
- **Translucent Tonal Surfaces:**
  - Card Glass Surface: `rgba(30, 27, 75, 0.45)` with `1px` border of `rgba(241, 245, 249, 0.12)`.
  - Elevated Modal Surface: `rgba(15, 23, 42, 0.85)` with `1px` border of `rgba(16, 185, 129, 0.25)`.
- **Text & Contrast Surfaces:**
  - High Emphasis: Crisp pure white `#FFFFFF` and `#F8FAFC`.
  - Mid Emphasis / Metadata: Neutral Slate `#94A3B8`.
  - Inactive / Subtle: Slate `#475569`.

## Typography

Typography establishes an engineered, systematic hierarchy. **Outfit** delivers geometric precision and contemporary confidence for key impact moments and titles, while **Inter** guarantees dense, neutral legibility across tabular schedules, registration forms, and technical specifications.

- Headlines (`display-xl` down to `headline-md`) apply tight letter-spacing (`-0.02em` to `-0.01em`) to maintain sharp physical presence.
- Numbers, timestamps, ticket prices, and registration counters in `label-md` and `body-sm` leverage tabular numerals (`font-variant-numeric: tabular-nums`).
- Responsive shifts downscale headers on screens smaller than 768px to avoid awkward multiline wrapping in event card banners and modal dialogs.

## Layout & Spacing

The layout is structured around an adaptive 12-column responsive grid on desktop and tablet, scaling to a 4-column stack on mobile viewports.

- **Desktop (>= 1280px):** 12 columns, 1200px max-width container centered with automatic margins, 24px (`1.5rem`) gutters, and 32px (`2rem`) page margin.
- **Tablet (768px - 1279px):** 8 columns, 20px gutters, and 24px margin. Two-column presentation for event grids and schedules.
- **Mobile (< 768px):** 4 columns, 16px (`1rem`) gutters, and 16px margins. Cards collapse into single-column vertical flows; interactive bottom-sheet modals replace center dialogs.
- **Rhythm Rules:** Strict adherence to an 8px spacing baseline (`space-xs` = 4px, `space-sm` = 8px, `space-md` = 16px, `space-lg` = 24px, `space-xl` = 40px) to maintain aligned component modules and rapid spatial parsing.

## Elevation & Depth

Depth is conveyed through luminous glassmorphism and ambient emerald rim lights rather than conventional muddy drop shadows:

1. **Base Layer (Ground):** Solid canvas in deep slate `#0B0F19` with subtle radial gradient spots in indigo (`#1E1B4B`, 20% opacity) behind major event sections.
2. **Interactive Glass Cards (Level 1):** Translucent backdrop (`rgba(30, 27, 75, 0.4)` to `rgba(15, 23, 42, 0.7)`), 12px blur, wrapped in a 1px perimeter stroke (`rgba(248, 250, 252, 0.08)`). Hover triggers a transition to `rgba(16, 185, 129, 0.35)` border glow and an ambient drop shadow: `0 12px 32px -8px rgba(16, 185, 129, 0.15)`.
3. **Floating Controls & Badges (Level 2):** Translucent background with crisp light refraction: `rgba(255, 255, 255, 0.06)`, `backdrop-filter: blur(8px)`, framed with `1px solid rgba(255, 255, 255, 0.15)`.
4. **Modal Dialogs & Payment Sheets (Level 3):** Dense backdrop blur (`24px blur`, `rgba(15, 23, 42, 0.9)`), rim-lit with a dual shadow: `0 24px 48px -12px rgba(0, 0, 0, 0.65)` stacked over `0 0 0 1px rgba(16, 185, 129, 0.25)`.

## Shapes

The interface embraces modern structural roundedness (`roundedness: 2`), balancing structural precision with ergonomic warmth:

- Standard structural elements (cards, inputs, dropdowns) utilize `0.5rem` (8px) base radius.
- Larger spatial panels, event feature hero cards, and modal dialogs step up to `1rem` (16px) or `1.5rem` (24px).
- Meta tags, live status tags, date chips, and primary action buttons utilize full capsule pill geometry (`9999px`) to create an immediate visual contrast against geometric card grids.

## Components

### Buttons
- **Primary Action (Register / Pay Now):** Solid Emerald (`#10B981`) text in pure white `#FFFFFF` or dark slate `#022C22`, pill radius, font weight 600. Hover moves to `#059669` with a subtle `0 0 20px rgba(16, 185, 129, 0.4)` glow.
- **Secondary / Glass Button:** Semi-transparent slate background (`rgba(255, 255, 255, 0.05)`), border `1px solid rgba(255, 255, 255, 0.12)`, text `#F8FAFC`. Hover increases border brightness to `rgba(255, 255, 255, 0.3)`.

### Chips & Badges
- **Event Category & Department Pills:** Full pill radius (`9999px`), padding `4px 12px`. Subtle dark emerald background `rgba(16, 185, 129, 0.12)`, 1px border `rgba(16, 185, 129, 0.3)`, text `#10B981` in `label-xs` uppercase tracking.
- **Live / Status Beacon:** Includes a pulsing 6px circular dot (`#10B981`) adjacent to label text.

### Cards (Events & Hackathons)
- Structured with glassmorphic backing, 16px corner radius, internal padding of `space-lg` (24px).
- Upper tier: Event visual cover with date badge anchored top-right.
- Middle tier: Event name (`title-lg`), organizing department (CSE, ECE, IEEE GRIET SB), and short description.
- Lower tier: Fee indicator, team size counter, and instant register CTA.

### Input Fields & Controls
- Form inputs feature a dark charcoal translucent base (`rgba(15, 23, 42, 0.6)`), 8px border-radius, 1px border `rgba(148, 163, 184, 0.2)`, text `#F8FAFC`.
- Focus state activates an emerald border `#10B981` with a diffuse `0 0 0 3px rgba(16, 185, 129, 0.2)` ring.
- Checkboxes and radios use emerald fills when active with high-contrast white check vectors.

### UPI QR Payment & Checkout Modal
- Centered overlay modal featuring high-grade backdrop blur (`backdrop-filter: blur(20px)`).
- Centered QR canvas: Crisp white container card (12px radius, 16px padding) hosting the dynamic UPI QR code, flanked by a live countdown timer and copyable UPI VPA ID.
- Verified transaction badge: Animated emerald success ring confirming instant receipt generation.