# P1GL embedded vector emitter

This is a small source snapshot from Phillip Porch's P1GL library:
https://github.com/ppporch/P1GL

The non-owning native vector emitter and its constants support the analysis display.
The code is GPL-3.0; see LICENSE. The original source is src/vector_sink.ac and
src/type340.ah in P1GL. This adapter was added for Signal Station v6.2.

The frontend defines P1GL_VECTOR_EMIT as its existing bounds-checked EMIT macro.
It calls p1gl_vector with signed p1gl_vdx/vdy and tail 0 or END. The display must
already be in VECTOR mode at scale zero. The routine emits bounded native
vectors, preserving the total displacement, and sets END only on the final
word when requested. It issues no device IOT and owns neither buffer nor ISR.
Private scratch is separate from Signal Station's interrupt-handler state.

Keeping this tiny snapshot with SignalAnalysis makes its standalone checkout
buildable without an external P1GL install or an extra font memory bank. The
full P1GL frame manager and banked G_VTEXT renderer are not linked into Signal Station.

The picker additionally uses futural.jhf from P1GL, under the separate data
terms in HERSHEY-NOTICE.txt. generate_picker_font.py compiles its 64 SIXBIT
characters into compact native vector streams in unused field-4 space. The
face is fitted to 24-pixel cells with 28-pixel capitals; curve simplification
is bounded to half a pixel after coordinate quantization. The original source
and notice are retained. These data do not change the GPL code license.

Snapshot SHA256:
2ad7bccc8aee4eb011bf7a2c8df67b9fdc995d5c313543201daf4f2dd171db93  vector_sink.ac
1bfb921145334ac7160daffcb31f63bfde7ee0bdaa928cff549374be8ceb0875  type340.ah
