# Signal Station v6.2 — P1GL continuous vectors

This is a rendering update to an existing Type 340 application. Waveform sample
positions, power calculation, gain factors and clipped bar heights are unchanged.
The waveform, bars and guides use scale zero throughout, removing the wider
dot spacing that made steep lines and tall bars look dotted.

## Integration

Signal Station owns two lists in field 2 and an interrupt handler in field 0.
Its main builder runs in field 1; it never writes the list currently scanned.
Using P1GL's standalone blocking frame manager would conflict with that design,
so the shared vector_sink.ac module is deliberately non-owning. The caller sets
native VECTOR mode/scale zero, signed deltas and an optional END flag. It emits
AC words through a compile-time P1GL_VECTOR_EMIT sink. Here that sink is the
existing EMIT, including capacity checking and the extended-memory store.

The module issues no display or drum IOTs. Its scratch is independent of ISR
scratch, so the existing sequence break may interrupt it safely. Source, public
inputs and scratch share field 1; no new field or font storage is allocated.
The tiny licensed P1GL snapshot is in p1gl/ with content hashes/provenance.

## Geometry and size

All 256 waveform samples remain endpoints. Neighboring samples are joined by
unit-spaced native vectors; intermediate spans larger than the seven-bit
component field are split. Small integer rounding can select a nearby split
point, while the total displacement and next sample endpoint remain exact.
Spectrum heights preserve DC/Nyquist weighting, gain and clipping. Tall axial
bars use 127-unit pieces, avoiding a fourth command for height 256.
The 768-pixel guides are six 127-unit vectors plus one six-unit vector.

A deliberately adversarial scene alternates maximum positive/negative samples
and saturates all 129 bars simultaneously, even though that power/waveform
combination is not physically produced by an FFT. Drum layout uses 1,935 words;
tape layout uses 1,965 in the 1,984-word buffer. Both preserve every endpoint,
all bar heights, unit spacing and FFT/power memory. No allocation was enlarged.

## Validation

Frontend, gain, hold/step/run, single-channel/SBS16 interrupts, clock wrap, slow
refresh accounting, acquisition, checksums, WAV conversion, core arithmetic,
Microtape load, Apollo RAM contents, picker, loading spinner and host filesystem
compatibility suites passed. Actual CPU execution checked 146 Apollo analysis
frames. The captured display lists retain 37,376 waveform endpoints, every
spectrum bar and valid bounds. No active list mutation is allowed by the runner.

P1GL's emitter was independently executed over 4,496 signed displacements with
an AC-clobbering sink. Component bounds, sign, connected endpoints, total
movement, final END placement and axial chunk counts were checked.

The scan-cost model for the same high-gain Apollo frames changes from mean
15.10/max 23.35 ms to mean 19.10/max 45.05 ms. Thirty-six of 146 full-resolution
scenes model above 25 ms. This is an intentional quality tradeoff following
Phillip/Bill's guidance, not a guarantee of wall-clock timing or client frame
rate. The live Pi run measured 12–47 ms with no faults or FFT overflows;
a 20-second sample completed 1,021 display starts. The waveform, spectrum and
guides were visually inspected in an X11 capture. The drum image hash remained
unchanged. See validation/vector-live.json and VALIDATION.md.
