#!/usr/bin/env python3
"""Full-resolution geometry and adversarial display-buffer bounds on real CPU."""
import json,os,re,subprocess,tempfile
from pathlib import Path
from test_core import ROOT,tape_memory,write_mem,read_mem,encode,trunc
from test_frontend import scene
import sys
sys.path.insert(0,str(ROOT))
from drum import calibration_image

def visible_vectors(mem,start):
    mode=0;x=y=0;scale=0;rows=[]
    for a in range(start,start+1984):
        w=mem[a];nxt=(w>>13)&7
        if mode==0:
            if w&0o2000:return rows
            if w&0o100:scale=(w>>4)&3
            mode=nxt
        elif mode==1:
            if w&0o200000:y=w&1023
            else:x=w&1023
            mode=nxt
        elif mode==3:
            if any(((w>>s)&63)==31 for s in (12,6,0)):mode=0
        elif mode==4:
            nx=x+(w&127)*(1<<scale)*(-1 if w&0o200 else 1)
            ny=y+((w>>8)&127)*(1<<scale)*(-1 if w&0o100000 else 1)
            if w&0o200000:
                assert scale==0,('coarse vector',a,scale)
                rows.append((x,y,nx,ny))
            assert 0<=nx<=1023 and 0<=ny<=1023
            x,y=nx,ny
            if w&0o400000:mode=0
        else:raise AssertionError(('unexpected display mode',mode))
    raise AssertionError('No HALT within display allocation')

def main():
    memory,_=tape_memory(ROOT/'workstation.rim')
    sy={f[2]:int(f[0],8) for l in (ROOT/'workstation.sym').read_text().splitlines() if len(f:=l.split())==4 and re.fullmatch('[0-7]{6}',f[0])}
    report=[]
    with tempfile.TemporaryDirectory(prefix='saw-vector-quality-') as td:
        t=Path(td);disk=t/'disk';disk.write_bytes(calibration_image())
        # Execute only the ordinary cross-field replot gateway, leaving FFT code
        # and power values untouched. Free bank-0 area is below the RIM loader.
        entry=0o7400
        assert all(a not in memory for a in range(entry,entry+12))
        source=f'''Signal Station adversarial redraw driver
7400/
start_test, lem
lsm
cbs
eem
jsp i [0d{sy['replot']}]
lem
hlt
constants
start start_test:0
'''
        (t/'redraw.am1').write_text(source)
        subprocess.run([os.environ.get('AM1','/opt/pidp1-mods/bin/am1'),'-d','redraw.am1'],cwd=t,check=True,capture_output=True,text=True)
        driver,go=tape_memory(t/'redraw.rim')
        image=dict(memory);image.update({a:w for a,w in driver.items() if a<0o7751})
        write_mem(t/'code',image)
        samples=[131071 if n%2==0 else -131071 for n in range(256)]
        for source_mode in (0,1):
            patches={sy['waveform']+i:encode(n) for i,n in enumerate(samples)}
            patches.update({sy['phi']+i:131071 for i in range(129)})
            patches[sy['input_source']]=source_mode
            write_mem(t/'patch',patches)
            env=dict(os.environ,SAW_GAIN_MODE='1')
            cpu=subprocess.run([str(ROOT/'tests/frontend_runner'),str(t/'code'),str(t/'patch'),str(t/'out'),f'{go:o}',str(disk)],check=True,capture_output=True,text=True,env=env)
            out=read_mem(t/'out');assert out[sy['fault']]==0,cpu.stdout
            assert all(out[sy['phi']+i]==131071 for i in range(129))
            assert all(out[0o2000+i]==memory.get(0o2000+i,0) for i in range(512))
            start=out[sy['active']];render=scene(out,start);vs=visible_vectors(out,start)
            waves=[v for v in vs if min(v[1],v[3])>500 and 128<=v[0]<=893 and 128<=v[2]<=893 and 0<=v[2]-v[0]<=3]
            for i,n in enumerate(samples[1:],1):
                half=trunc(n,2);y=768+trunc(half+trunc(half,2),512)
                assert any(v[2:]==(128+3*i,y) for v in waves),(i,y)
            for k in range(129):
                x=128+6*k;y=64
                bars=[v for v in vs if v[0]==v[2]==x and 64<=v[1]<320 and v[3]>v[1]]
                while y<320:
                    ends=[v[3] for v in bars if v[1]==y and v[3]<=320]
                    assert ends,(k,y);y=max(ends)
                assert y==320
            assert render['words']<1984
            report.append(dict(source='tape' if source_mode else 'drum',words=render['words'],capacity=1984,spare=1984-render['words'],waveform_endpoints=256,saturated_spectrum_bars=129,unit_spaced_visible_vectors=len(vs),fft_and_power_unchanged=True))
    text=json.dumps(report,indent=2)+'\n';(ROOT/'tests/vector-quality-results.json').write_text(text);print(text,end='')
if __name__=='__main__':main()
