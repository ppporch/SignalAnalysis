#!/usr/bin/env python3
"""Compile P1GL's Hershey face into SIXBIT vector streams for the tape picker.
Data terms: p1gl/HERSHEY-NOTICE.txt. No extra RAM field is allocated.
"""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent

def simplify(points):
    """Remove quantized curve vertices within half a pixel of the new segment."""
    if len(points)<3:return points
    a,b=points[0],points[-1];dx=b[0]-a[0];dy=b[1]-a[1]
    def distance2(c):
        u=max(0,min(1,((c[0]-a[0])*dx+(c[1]-a[1])*dy)/(dx*dx+dy*dy))) if dx*dx+dy*dy else 0
        return (c[0]-a[0]-u*dx)**2+(c[1]-a[1]-u*dy)**2
    d,i=max((distance2(points[i]),i) for i in range(1,len(points)-1))
    return simplify(points[:i+1])[:-1]+simplify(points[i:]) if d>.25 else [a,b]

def glyphs():
    for code,line in enumerate((ROOT/'p1gl/futural.jhf').read_text().splitlines()[:64]):
        count=int(line[5:8]);data=line[8:]
        assert len(data)==count*2
        left,right=ord(data[0])-82,ord(data[1])-82
        height=max([21]+[9-(ord(data[i+1])-82) for i in range(2,len(data),2) if data[i:i+2]!=' R'])
        strokes=[];stroke=[]
        for i in range(2,len(data),2):
            pair=data[i:i+2]
            if pair==' R':
                if stroke:strokes.append(stroke);stroke=[]
            else:
                stroke.append((round((ord(pair[0])-82-left)*20/(right-left))+2,
                               round((9-(ord(pair[1])-82))*28/height)))
        if stroke:strokes.append(stroke)
        x=y=0;words=[]
        for stroke in strokes:
            for i,(nx,ny) in enumerate(simplify(stroke)):
                dx,dy=nx-x,ny-y
                w=abs(dx)|(abs(dy)<<8)|(0o200 if dx<0 else 0)|(0o100000 if dy<0 else 0)|(0o200000 if i else 0)
                assert abs(dx)<=127 and abs(dy)<=127
                words.append(w);x,y=nx,ny
        if not words:words=[0]
        words[-1]|=0o400000
        yield code,words

def generate():
    data=list(glyphs())
    lines=['// Generated Hershey/P1GL SIXBIT font; see p1gl/HERSHEY-NOTICE.txt.',
           '// Unit-spaced relative vectors; each character starts at its baseline.',
           'picker_vfont,']
    lines += [f'        pv_char{code}:4' for code,words in data]
    for code,words in data:
        lines += [f'pv_char{code},']+[f'        {w:06o}' for w in words]
    (ROOT/'generated/picker-font.ac').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'glyphs':64,'font_words':64+sum(len(w) for _,w in data),'height':28,'advance':24}))
if __name__=='__main__':generate()
