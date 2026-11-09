"""Generate original chiptune loops and effects. No external audio required."""
from array import array
import math
from pathlib import Path
import random
import wave

RATE = 22050
ROOT = Path(__file__).resolve().parent.parent / 'game/assets/audio'


def save(name, samples):
    ROOT.mkdir(parents=True, exist_ok=True)
    pcm = array('h', (int(max(-1, min(1, value)) * 28000) for value in samples))
    with wave.open(str(ROOT / (name + '.wav')), 'wb') as out:
        out.setparams((1, 2, RATE, 0, 'NONE', 'not compressed'))
        out.writeframes(pcm.tobytes())


def frequency(note):
    return 440 * 2 ** ((note - 69) / 12)


def music(name, bpm, melody, roots):
    beat = 60 / bpm
    duration = beat * 32
    samples = array('f', [0]) * round(duration * RATE)
    for step in range(64):
        start = step * beat / 2
        note = melody[step % len(melody)]
        root = roots[(step // 16) % len(roots)]
        for i in range(round(beat / 2 * RATE)):
            t = i / RATE
            env = min(1, t / .009) * max(0, 1 - t / (beat * .48))
            lead = 0 if note is None else (1 if math.sin(2 * math.pi * frequency(note) * t) > .5 else -1) * .065 * env
            bass = math.sin(2 * math.pi * frequency(root - 12) * (start + t)) * .075 * (1 - t / beat)
            arp = math.sin(2 * math.pi * frequency(root + (0, 7, 12, 7)[step % 4]) * t) * .045 * env
            index = round(start * RATE) + i
            if index < len(samples):
                samples[index] += lead + bass + arp
    save(name, samples)


def effect(name, tones, length=.12, noise=0):
    rng = random.Random(27)
    samples = []
    for i in range(round(length * RATE)):
        t = i / RATE
        progress = t / length
        freq = tones[min(len(tones)-1, int(progress * len(tones)))]
        env = min(1, t / .004) * (1 - progress) ** 1.6
        samples.append((math.sin(2 * math.pi * freq * t) * .22 + rng.uniform(-noise, noise)) * env)
    save(name, samples)


def battle_music():
    """A new minor-key adventure groove with triangle lead and soft drums."""
    beat = 60 / 120
    duration = beat * 32
    samples = array('f', [0]) * round(duration * RATE)
    melody = [
        69,None,72,76,74,None,72,69, 67,69,72,None,71,67,64,None,
        65,None,69,72,76,74,72,None, 67,71,74,77,76,None,74,71,
        69,72,76,81,79,76,74,72, 67,None,71,74,76,74,71,67,
        65,69,72,76,74,72,69,65, 64,68,71,74,76,None,71,68,
    ]
    roots = [45, 43, 41, 40]
    rng = random.Random(44)
    for step, note in enumerate(melody):
        start = step*beat/2
        root = roots[(step//16) % 4]
        for i in range(round(beat/2*RATE)):
            t = i/RATE
            env = min(1,t/.012) * max(0,1-t/(beat*.5))**.7
            lead = 0 if note is None else math.asin(math.sin(math.tau*frequency(note)*t))*2/math.pi*.13*env
            bass_note = root + (0,0,7,12)[step%4]
            bass = math.sin(math.tau*frequency(bass_note)*t)*.10*env
            arp = math.sin(math.tau*frequency(root+24+(0,7,12,7)[step%4])*t)*.035*env
            noise = rng.uniform(-1,1)
            hat = noise*.018*math.exp(-t*70)
            kick = math.sin(math.tau*(50*t+6*(1-math.exp(-t*25))))*.15*math.exp(-t*22) if step%4 == 0 else 0
            snare = noise*.065*math.exp(-t*27) if step%8 == 4 else 0
            idx = round(start*RATE)+i
            if idx < len(samples):
                seam = min(1, idx/(RATE*.012), (len(samples)-idx)/(RATE*.012))
                samples[idx] = (lead+bass+arp+hat+kick+snare)*seam
    save('stage', samples)


if __name__ == '__main__':
    music('menu', 108, [72, None, 76, 79, 76, None, 74, 72, 69, None, 72, 76, 74, 72, 67, None], [60, 57, 65, 67])
    battle_music()
    for name, notes, seconds, noise in [
        ('hover', [700, 880], .055, 0), ('confirm', [523, 659, 784], .18, 0),
        ('type', [900, 650], .035, .025), ('laser', [1500, 1100, 700, 300], .19, .015),
        ('miss', [220, 170], .18, .025), ('impact', [100, 65, 40], .35, .25),
        ('spawn', [160, 240, 320], .12, .015), ('pause', [660, 440], .14, 0),
        ('game_over', [392, 330, 262, 196], .9, 0), ('level', [523, 659, 784, 1046], .4, 0)]:
        effect(name, notes, seconds, noise)
    rng = random.Random(9)
    smooth = 0
    samples = []
    for i in range(RATE * 8):
        smooth = smooth * .94 + rng.uniform(-1, 1) * .06
        t = i / RATE
        # Periodic envelope is quiet at the seam of the loop.
        samples.append(smooth * .13 * (.5 - .5 * math.cos(2 * math.pi * t / 8)))
    save('shore', samples)
    print('Original audio generated in', ROOT)
