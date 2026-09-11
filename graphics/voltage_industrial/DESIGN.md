---
name: Voltage Industrial
colors:
  surface: '#f8f9fa'
  surface-dim: '#d9dadb'
  surface-bright: '#f8f9fa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f4f5'
  surface-container: '#edeeef'
  surface-container-high: '#e7e8e9'
  surface-container-highest: '#e1e3e4'
  on-surface: '#191c1d'
  on-surface-variant: '#46474a'
  inverse-surface: '#2e3132'
  inverse-on-surface: '#f0f1f2'
  outline: '#76777b'
  outline-variant: '#c7c6ca'
  surface-tint: '#5f5e5f'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#1b1b1c'
  on-primary-container: '#858384'
  inverse-primary: '#c8c6c7'
  secondary: '#855300'
  on-secondary: '#ffffff'
  secondary-container: '#fea619'
  on-secondary-container: '#684000'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#001a42'
  on-tertiary-container: '#3980f4'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e5e2e3'
  primary-fixed-dim: '#c8c6c7'
  on-primary-fixed: '#1b1b1c'
  on-primary-fixed-variant: '#474647'
  secondary-fixed: '#ffddb8'
  secondary-fixed-dim: '#ffb95f'
  on-secondary-fixed: '#2a1700'
  on-secondary-fixed-variant: '#653e00'
  tertiary-fixed: '#d8e2ff'
  tertiary-fixed-dim: '#adc6ff'
  on-tertiary-fixed: '#001a42'
  on-tertiary-fixed-variant: '#004395'
  background: '#f8f9fa'
  on-background: '#191c1d'
  surface-variant: '#e1e3e4'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-caps:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  mono-data:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  container-margin: 32px
  gutter: 24px
  card-padding: 20px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
---

## Brand & Style

The design system is built on an **Industrial Professional** aesthetic, designed for high-stakes utility and operational efficiency. It targets electrician business owners who require immediate clarity, reliability, and a sense of "power under control."

The style merges **Minimalism** with **Modern Corporate** precision. It utilizes heavy whitespace to ensure data legibility, grounded by a robust charcoal foundation. The interface should evoke the feeling of a high-end physical control panel: tactical, responsive, and indestructible. Visuals are intentionally sharp and structured to convey expertise and technical mastery.

## Colors

The palette is anchored by **Deep Charcoal (#1A1A1B)**, used for primary navigation, high-level headings, and structural boundaries to provide a "heavy" professional base. **Electric Amber (#F59E0B)** serves as the high-contrast accent color, reserved exclusively for primary actions (CTAs), critical alerts, and branding elements that signify energy or "active" status.

- **Primary:** Deep Charcoal for authority and structure.
- **Secondary:** Electric Amber for energy and interaction.
- **Tertiary:** Signal Blue (#3B82F6) for secondary data points and informational links.
- **Neutral:** A range of cool grays (from #F9FAFB to #6B7280) to maintain a clean, laboratory-like environment.
- **Surface:** Crisp white (#FFFFFF) is the primary canvas to ensure maximum readability for complex data sets.

## Typography

This design system utilizes **Inter** for all primary communication to ensure a modern, geometric, and neutral tone. It is supplemented by **Geist** for labels and data displays, leveraging its technical, monospaced-adjacent character to enhance the "industrial" feel.

- **Headlines:** Use tight letter-spacing and bold weights to command attention.
- **Labels:** Use uppercase for category headers to create clear visual separators in the dashboard.
- **Data:** Numerical values in charts and tables should favor Geist for tabular lining, ensuring numbers align perfectly for quick scanning.

## Layout & Spacing

The layout follows a **Fixed Grid** philosophy for desktop to maintain a "dashboard cockpit" feel, where information remains in predictable locations. 

- **Desktop (1440px+):** 12-column grid with 24px gutters. A persistent sidebar (280px) houses primary navigation.
- **Tablet:** 8-column grid. The sidebar collapses into a narrow icon rail.
- **Mobile:** 4-column grid with 16px margins. Cards stack vertically, and complex data visualizations should prioritize horizontal scrolling or simplified "sparkline" views.

Spacing is governed by a 4px baseline. Components utilize generous internal padding to maintain a "professional" and uncluttered atmosphere, even when displaying high-density information.

## Elevation & Depth

Elevation is handled through **Tonal Layers** and **Low-Contrast Outlines** rather than heavy shadows, maintaining a flat, architectural look.

- **Level 0 (Background):** #F9FAFB (Neutral Gray).
- **Level 1 (Cards/Containers):** White background with a 1px border (#E5E7EB). No shadow.
- **Level 2 (Hover/Active):** A soft, extra-diffused "Ambient Shadow" (0px 4px 20px rgba(0,0,0,0.05)) to indicate interactivity.
- **Interactive Elements:** Use sharp, 1px borders in primary charcoal or electric amber to define focus states.
- **Depth Scrim:** For modals, use a high-opacity charcoal scrim (80% alpha) to focus the user on the task at hand.

## Shapes

The shape language is **Soft** (4px radius), reflecting industrial precision and tool-like durability. Avoid large radii or pill shapes for primary containers to maintain a serious, professional tone.

- **Small elements (Buttons, Inputs, Checkboxes):** 4px radius.
- **Medium elements (Cards, Modals):** 8px (rounded-lg).
- **Large elements (Outer Wrappers):** 12px (rounded-xl).
- **Icons:** Use 2px stroke width with sharp or slightly softened corners to match the typography.

## Components

### Buttons
- **Primary:** Deep Charcoal background, White text. High-contrast.
- **Secondary:** White background, 1px Deep Charcoal border.
- **Action/CTA:** Electric Amber background, Deep Charcoal text. Use sparingly for "New Quote" or "Emergency Call."

### Status Indicators
- **Active:** Electric Amber text with a soft amber subtle background tint.
- **Pending:** Medium Gray (#6B7280) text/background.
- **Completed:** Emerald Green (#10B981) text/background.
- *Visual Style:* Small, rectangular tags with all-caps Geist labels.

### Data Visualizations
- **Line Charts:** 2px stroke width. Primary line in Electric Amber. Use a subtle gradient fill below the line for "volume" indicators.
- **Bar Charts:** Flat, Deep Charcoal bars. Highlight "current" or "target" bars in Electric Amber.
- **Grid Lines:** Ultra-light gray (#F3F4F6) to remain unobtrusive.

### Cards
- Standard white containers with 1px light gray borders. 
- Headers should have a subtle bottom border separator.
- Use Geist Mono for technical metrics (e.g., "Voltage: 240V", "Load: 85%").

### Inputs
- 1px light gray border that transitions to a 2px Deep Charcoal border on focus. 
- Labels sit above the input in all-caps Geist.