# Design Principles for RF Browser UIs

These rules produce UIs that look like they belong in an RF lab, not in a SaaS dashboard
generator. Every choice traces back to the domain: radio signals, spectral analysis,
real-time measurement.

## Ground the design in the domain

An RF UI is an instrument panel, not a marketing page. Its vocabulary comes from spectrum
analysers, oscilloscopes, and SDR consoles: grid overlays on dark backgrounds, traces
that glow against the noise floor, readings in engineering units (MHz, dBFS, dBm, MS/s).
Use those elements because they carry information, not because they look technical.

Before writing CSS, answer: what does this instrument measure? A spectrum analyser shows
power vs frequency. A waterfall shows frequency vs time. A channel table shows detection
state. Each view has a single job. Design for that job.

## Anti-patterns: what makes an RF UI look AI-generated

Avoid these — they are the most common tells of a generated technical page:

1. **Cream/terracotta palettes** or purple-to-blue gradient heroes — these belong in
   landing pages, not instrument panels
2. **Rounded cards with uniform shadows** on every element — an oscilloscope has no
   `border-radius: 12px` cards
3. **Numbered markers (01 / 02 / 03)** on views that aren't a sequence — spectrum,
   waterfall and channels are parallel views, not steps
4. **Emoji as section markers** — an RF UI uses unit labels, not 📊
5. **ALL-CAPS eyebrow labels** above every heading — instrument panels use concise
   labels inline with their readouts
6. **Big hero sections with gradient text** — the data IS the hero; don't push it
   below the fold
7. **Generic motivational copy** ("Real-time insights at your fingertips") — write
   nothing, or write the centre frequency and sample rate
8. **Identical card styling on every panel** — the spectrum trace and the channel table
   have different information densities and deserve different treatments

## What makes an RF UI feel real

- **Data first**: the spectrum trace, waterfall, and readings are visible immediately,
  not after scrolling past a hero
- **Dark by design**: RF instruments use dark backgrounds because bright pixels on a
  dark field read as signal. This isn't aesthetic preference — it's how spectrograms
  work. Light theme: invert the contrast model (dark traces on light), don't just swap
  black for white
- **Monospace for numbers**: frequency readouts, power levels, and timestamps use a
  monospace or tabular-nums font so digits don't shift as values change
- **Grid overlays with purpose**: grid lines on the spectrum match the frequency raster
  or the channel boundaries — they're reference lines, not decoration
- **Phosphor glow, sparingly**: a subtle glow on the active trace (1-2px blur, low
  opacity) evokes a CRT phosphor. More than that becomes a cliché
- **Colour encodes state**: occupied channels get one colour, clear channels another,
  threshold-near channels a third. Don't use the same accent for everything
- **Engineering notation in labels**: "97.3 MHz" not "97.3", "−37.1 dBFS" not "−37.1"
- **Status is terse**: "Connected" / "Disconnected", not "You are currently connected
  to the data stream"

## Typography

| Role | Recommendation | Why |
|------|---------------|-----|
| Data readouts | JetBrains Mono, IBM Plex Mono, or Source Code Pro | Tabular digits, clear at small sizes |
| Headings | Space Grotesk, Inter Display, or DM Sans | Technical but not cold |
| Body text | Inter, IBM Plex Sans | Neutral, high legibility at 14px |

Load from Google Fonts. Use at most two families. Set `font-variant-numeric: tabular-nums`
on any element displaying changing numbers.

## Motion

RF UIs update at 1–2 Hz (500ms frames). That IS the motion — the data animates itself.
Don't add entrance animations, fade-ins, or scroll-triggered reveals. The only justified
motion beyond data updates:

- Smooth transitions on the connection status indicator
- A brief highlight when a channel changes state (occupied ↔ clear)
- Canvas requestAnimationFrame for the actual data rendering

Everything else is decoration that competes with the signal.

## Layout philosophy

The views are instruments in a rack, not cards in a grid. They share edges, they align,
they use the full width. See `layout.md` for the specific patterns.
