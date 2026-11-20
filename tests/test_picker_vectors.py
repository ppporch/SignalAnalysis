#!/usr/bin/env python3
"""Execute full vector picker scenes, including all SIXBIT and worst filenames."""
import json,os,re,subprocess,tempfile
from pathlib import Path
from test_core import ROOT,tape_memory,write_mem,read_mem
import sys
sys.path.insert(0,str(ROOT))
from drum import calibration_image

def inspect(mem):
    mode=scale=x=y=0;segments=hits=0
    for a in range(0o30000,0o40000):
        w=mem[a];nxt=(w>>13)&7
        if mode==0:
            if w&0o2000:
                assert w&0o1000 # interrupt
                return dict(words=a-0o30000+1,vectors=segments,pen_vectors=hits)
            if w&0o100:scale=(w>>4)&3
            if w&0o10000:pen=bool(w&0o4000)
            mode=nxt
        elif mode==1:
            if w&0o200000:y=w&1023
            else:x=w&1023
            mode=nxt
        elif mode==4:
            assert scale==0
            nx=x+(w&127)*(-1 if w&0o200 else 1)
            ny=y+((w>>8)&127)*(-1 if w&0o100000 else 1)
            assert 0<=nx<=1023 and 0<=ny<=1023,(a,x,y,nx,ny)
            if w&0o200000:
                segments+=1
                if pen:
                    hits+=1
                    assert (120<=min(y,ny)<=max(y,ny)<=220) or (340<=min(y,ny)<=max(y,ny)<=850)
            x,y=nx,ny
            if w&0o400000:mode=0
        else:raise AssertionError(('picker must contain only point/parameter/vector',a,mode))
    raise AssertionError('Picker exceeded field 3')

def main():
    memory,_=tape_memory(ROOT/'workstation-tape.rim')
    sy={f[2]:int(f[0],8) for l in (ROOT/'workstation-tape.sym').read_text().splitlines() if len(f:=l.split())==4 and re.fullmatch('[0-7]{6}',f[0])}
    report=[]
    with tempfile.TemporaryDirectory(prefix='saw-picker-vectors-') as td:
        t=Path(td);entry=0o7400
        assert all(a not in memory for a in range(entry,entry+12))
        (t/'draw.am1').write_text(f'''Vector picker test driver
7400/
lem
lsm
cbs
jsp {sy['p_draw']:o}
hlt
start 07400:0
''')
        subprocess.run([os.environ.get('AM1','/opt/pidp1-mods/bin/am1'),'-d','draw.am1'],cwd=t,check=True,capture_output=True)
        driver,_=tape_memory(t/'draw.rim');memory.update({a:w for a,w in driver.items() if a<0o7751})
        write_mem(t/'code',memory);(t/'disk').write_bytes(calibration_image())
        for name,codes in [('all_sixbit',list(range(64))+[0]*8),('worst_names',[32]*72)]:
            patch={sy['p_count']:8,sy['p_page']:0,sy['p_selected']:3,sy['p_error']:63,sy['p_invalid']:0}
            for n in range(24):patch[sy['p_names']+n]=(codes[n*3]<<12)|(codes[n*3+1]<<6)|codes[n*3+2]
            write_mem(t/'patch',patch)
            subprocess.run([str(ROOT/'tests/frontend_runner'),str(t/'code'),str(t/'patch'),str(t/'out'),f'{entry:o}',str(t/'disk')],check=True,capture_output=True)
            out=read_mem(t/'out');assert out[sy['fault']]==0
            result=inspect(out);result['case']=name;report.append(result)
            assert result['vectors']>500 and result['pen_vectors']>300
            for a,w in memory.items():
                if (0o20000<=a<0o27700 or 0o40000<=a or 0o11400<=a<0o13000):assert out[a]==w,('clobbered analysis/font',a)
        # The font is immutable and supports every legal filename character.
        for n in range(64):
            p=memory[sy['picker_vfont']+n];start=p
            while not memory[p]&0o400000:p+=1;assert p-start<64
            assert p<0o50000
    text=json.dumps(report,indent=2)+'\n';(ROOT/'tests/picker-vector-results.json').write_text(text);print(text,end='')
if __name__=='__main__':main()
