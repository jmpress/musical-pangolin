#a custom library for music generation using CircuitPython

import random
import synthio
import ulab.numpy as np
from time import sleep

note_names = ['A','A#','B','C','C#','D','D#','E','F','F#','G','G#']
note_length = [1/16, 1/8, 1/4, 1/2, 1, 2, 4] #of course this isn't exhaustive, could implement triplets and such but...

    
#define music notes
note_fq = {
    "C" : [16.35,32.70,65.41,130.81,261.63,523.25,1046.50,2093.00,4186.01],
    "C#" : [17.32,34.65,69.30,138.59,277.18,554.37,1108.73,2217.46,4434.92],
    "D" : [18.35,36.71,73.42,146.83,293.66,587.33,1174.66,2349.32,4698.63],
    "D#" : [19.45,38.89,77.78,155.56,311.13,622.25,1244.51,2489.02,4978.03],
    "E" : [20.60,41.20,82.41,164.81,329.63,659.25,1318.51,2637.02,5274.04],
    "F" : [21.83,43.65,87.31,174.61,349.23,698.46,1396.91,2793.83,5587.65],
    "F#" : [23.12,46.25,92.50,185.00,369.99,739.99,1479.98,2959.96,5919.91],
    "G" : [24.50,49.00,98.00,196.00,392.00,783.99,1567.98,3135.96,6271.93],
    "G#" : [25.96,51.91,103.83,207.65,415.30,830.61,1661.22,3322.44,6644.88],
    "A" : [27.50,55.00,110.00,220.00,440.00,880.00,1760.00,3520.00,7040.00],
    "A#" : [29.14,58.27,116.54,233.08,466.16,932.33,1864.66,3729.31,7458.62],
    "B" : [30.87,61.74,123.47,246.94,493.88,987.77,1975.53,3951.07,7902.13]
}

sample_rate = 44100
SAMPLE_SIZE = 512 # one full period of waveform?
SAMPLE_VOLUME = 32000 #defines amplitude of wave form generation
half_period = SAMPLE_SIZE // 2
synth = synthio.Synthesizer(sample_rate=sample_rate) #CD quality sample rate, in theory

#define envelopes (times are in seconds)
pluck_env = synthio.Envelope(attack_time = 0.1, decay_time = 0.1, release_time = 0.1, attack_level = 1, sustain_level=0.00)
pad_env = synthio.Envelope(attack_time = 1.0, decay_time = 0.1, release_time = 1.0, attack_level = 1, sustain_level=1)

#define waveforms
wave_sine = np.array(np.sin(np.linspace(0, 2*np.pi, SAMPLE_SIZE, endpoint = False)) * SAMPLE_VOLUME, dtype=np.int16)
wave_saw = np.linspace(SAMPLE_VOLUME, -SAMPLE_VOLUME, num=SAMPLE_SIZE, dtype=np.int16)
wave_tri = np.concatenate((np.linspace(-SAMPLE_VOLUME, SAMPLE_VOLUME, num=half_period, dtype=np.int16), np.linspace(SAMPLE_VOLUME, -SAMPLE_VOLUME, num=half_period, dtype=np.int16)))
wave_square = np.concatenate((np.full(half_period, SAMPLE_VOLUME, dtype=np.int16), np.full(half_period, -SAMPLE_VOLUME, dtype=np.int16)))

#define LFOs
fast_lfo = synthio.LFO(waveform=wave_saw, rate=30)

#define filters
filter_set = [
    {"cutoff": 1500, "q": 0.4},
    {"cutoff": 500, "q": 0.7},
    {"cutoff": 500, "q": 0.4},
    {"cutoff": 441, "q": 0.8}
]
lpf1 = synth.low_pass_filter(filter_set[0]["cutoff"], filter_set[0]["q"])
lpf2 = synth.low_pass_filter(filter_set[1]["cutoff"], filter_set[1]["q"])
lpf3 = synth.low_pass_filter(filter_set[3]["cutoff"], filter_set[3]["q"])
hpf1 = synth.high_pass_filter(filter_set[2]["cutoff"], filter_set[2]["q"])
hpf2 = synth.high_pass_filter(filter_set[3]["cutoff"], filter_set[3]["q"])

#define musical time settings
tempo = 144
time_signature = [4,4]
ms_per_beat = 60000 / tempo #current settings = ~416.66
s_per_beat = 60 / tempo

#following calcs assume 4/4 time sig
note_length_s = [s_per_beat/4, s_per_beat/2, s_per_beat, s_per_beat*2, s_per_beat*4, s_per_beat*8, s_per_beat*16]

#prints a list of note lengths for the given settings
#for i in range(len(note_length)):
#    print(str(note_length[i]) + ' note = ' + str(note_length_ms[i]) + 'ms.')

scales = ['maj','min']
    #major W W H W W W H
    #minor W H W W H W W 


seed = 3 #replace with a hashed value based on something unique to each player/device if possible (mac address?)

random.seed(seed)
rand_note = note_names[random.randrange(len(note_names))]
rand_scale = scales[random.randrange(len(scales))]
if rand_scale == 'maj':
    scale_pattern = [0,2,4,5,7,9,11,12]
elif rand_scale =='min':
    scale_pattern = [0,2,3,5,7,8,10,12]
pet_name = rand_note + rand_scale

def generate_personal_scale():
    new_scale_start = rand_note
    note_index = note_names.index(new_scale_start)
    new_scale = []
    for i in range(8):
        new_scale.append(note_names[(note_index+scale_pattern[i])%len(note_names)])
    return new_scale
