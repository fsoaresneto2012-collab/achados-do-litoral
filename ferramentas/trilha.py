"""Gera trilha.wav (11 s, batida leve) para colocar no Short: python3 ferramentas/trilha.py; depois ffmpeg -i video.mp4 -i trilha.wav -map 0:v -map 1:a -c:v copy -c:a aac -shortest final.mp4. Para outra duração: python3 ferramentas/trilha.py SEGUNDOS."""
import numpy as np, wave
import sys
sr=44100; dur=float(sys.argv[1]) if len(sys.argv)>1 else 11.0; bpm=112; spb=60/bpm
t=np.arange(int(sr*dur))/sr; out=np.zeros_like(t)
def add(start,sig):
    i=int(start*sr); n=min(len(sig),len(out)-i)
    if n>0: out[i:i+n]+=sig[:n]
# kick
kt=np.arange(int(sr*0.25))/sr; kick=np.sin(2*np.pi*(50+80*np.exp(-kt*30))*kt)*np.exp(-kt*12)
hh=np.random.RandomState(1).randn(int(sr*0.05))*np.exp(-np.arange(int(sr*0.05))/sr*80)
chords=[[57,60,64],[53,57,60],[48,52,55],[55,59,62]]
def note(m,l):
    tt=np.arange(int(sr*l))/sr; f=440*2**((m-69)/12)
    return (np.sin(2*np.pi*f*tt)+0.3*np.sin(4*np.pi*f*tt))*np.exp(-tt*5)
b=0
while b*spb<dur:
    s=b*spb; add(s,0.9*kick); add(s+spb/2,0.15*hh)
    ch=chords[(b//4)%4]; add(s,0.12*note(ch[b%3]+12,spb*1.5)); 
    if b%2==0: add(s,0.18*note(ch[0]-12,spb*2))
    b+=1
out=out/np.max(np.abs(out))*0.5
fade=np.minimum(1,np.minimum(t/0.3,(dur-t)/0.8)); out*=fade
w=wave.open('trilha.wav','wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((out*32767).astype(np.int16).tobytes()); w.close()
