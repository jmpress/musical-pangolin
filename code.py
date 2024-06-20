import os
import board
import math
import displayio
import rotaryio
import digitalio
import time
import random

import audiocore
import busio
import audiobusio
import audiomixer
import sdcardio
import storage
import synthio
import ulab.numpy as np
import pangolinScales as pango
import dUtils

from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import label
from adafruit_display_shapes.triangle import Triangle
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.roundrect import RoundRect
from adafruit_progressbar.progressbar import HorizontalProgressBar

from gameMenus import care_menu, main_menu, synth_menu

display = board.DISPLAY
font = bitmap_font.load_font('/font/Hyperlight.bdf')
color = 0xFFFFFF
bg_color = 0x000000

##SPI pin definition for microSD card reader module
card_cs = board.GPIO26
MOSI = board.GPIO33
MISO = board.GPIO34
SCK = board.GPIO3
#initialize spi bus
spi = busio.SPI(SCK, MOSI, MISO)

#initialize storage
try:
    sdcard = sdcardio.SDCard(spi, card_cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")
    print("Mounted SD card")
    
    ###read in save game file here, if exists
    
except OSError as error:
    print(error)

# TODO load these in from save game state, these can be default values if there is no saved game
# max values are likely to stay constant however should still be accessible in the same scope as the current values, so if this gets changed into a game state object, include the max values.
#initialize pet-specific variables
user_scale = pango.generate_personal_scale()
game_state = {
    "current_food" : 100,
    "max_food" : 100,
    "food_decay_rate" : 5,
    "current_health" : 100,
    "max_health" : 100,
    "health_decay_rate" : 5,
    "current_energy" : 100,
    "max_energy" : 100,
    "energy_decay_rate" : 5,
    "current_xp" : 0,
    "max_xp" : 10,
    "level" : 1,     #where is this information expressed in game to the user?
    "current_screen" : main_menu,
    "current_selection" : None,
    "poop": False,
}

#define and initialize screen groups here, append such into root and see how goes
splash = displayio.Group()
menu_init = displayio.Group()       #dummy group to pop later
bar_init = displayio.Group()
sprite_group = displayio.Group()   #layer 0
menu_group = displayio.Group()     #layer 1
bar_group = displayio.Group()      #layer 2
overlay_group = displayio.Group()  #layer 3
#other_group = displayio.Group()    #layer 4 - currently unused

menu_group.append(menu_init)
bar_group.append(bar_init)

splash.append(sprite_group)
splash.append(menu_group)
splash.append(bar_group)
splash.append(overlay_group)
display.root_group = splash

tick_speed = 60000000000

##i2s pins for amp to drive speaker audio
DATA = board.GPIO47
LRCLK = board.GPIO48
BCLK = board.GPIO2

## Rotary Encoder pin assignments
ENCA = board.GPIO38
ENCB = board.GPIO39
COMA = board.GPIO40
SW1 = board.GPIO41
SW2 = board.GPIO42
SW3 = board.GPIO45
SW4 = board.GPIO46
SW5 = board.GPIO5
COMB = board.GPIO4

#initialize i2s bus
i2s = audiobusio.I2SOut(BCLK, LRCLK, DATA)

#initialize rotary encoder
encoder = rotaryio.IncrementalEncoder(ENCA, ENCB,2)
last_position = 0
com_a = digitalio.DigitalInOut(COMA)
com_a.switch_to_output()
com_a = False
com_b = digitalio.DigitalInOut(COMB)
com_b.switch_to_output()
com_b = False
button_pins = (SW1, SW2, SW3, SW4, SW5)
buttons = []
for button_pin in button_pins:
    pin = digitalio.DigitalInOut(button_pin)
    pin.switch_to_input(digitalio.Pull.UP)
    buttons.append(pin)

#initialize synthesizer
sample_rate = 44100
SAMPLE_SIZE = 512 # one full period of waveform?
SAMPLE_VOLUME = 32000 #defines amplitude of wave form generation
half_period = SAMPLE_SIZE // 2
synth = synthio.Synthesizer(sample_rate=sample_rate) #CD quality sample rate, in theory

#initialize audio mixer
mixer = audiomixer.Mixer(sample_rate=sample_rate, buffer_size=2048, channel_count=1)
i2s.play(mixer)
mixer.voice[0].play(synth)
mixer.voice[0].level = 0.25
    
switched = False
last_switch = -1

#define animations
fps_tick = 200000000    #animation tick speed; TODO link this to Tempo
idle_anim= {
    "prev_time": -1,
    "next_frame": 0,
    "frames": "/img/basic_form_spritesheet.bmp",
    "x_offset": [0,-128,-256,-384,-256,-128]
}
main_sprite_bmp = displayio.OnDiskBitmap(idle_anim["frames"])
main_sprite_tiles = displayio.TileGrid(main_sprite_bmp, pixel_shader=main_sprite_bmp.pixel_shader)
sprite_group.append(main_sprite_tiles)

def idle(now):
    global idle_anim, fps_tick
    if now >= (idle_anim["prev_time"] + fps_tick):
        sprite_group.x = idle_anim["x_offset"][idle_anim["next_frame"]]
        idle_anim["prev_time"]=now
        idle_anim["next_frame"] = (idle_anim["next_frame"] + 1)%len(idle_anim["x_offset"])

last_tick = -1

#This should handle the state changes for layer 2 bar_group, including visibility changes between screens
def update_bars():
    food_bar = None
    health_bar = None
    energy_bar = None
    xp_bar = None
    new_group = displayio.Group()
    foodP = math.floor((game_state["current_food"]/game_state["max_food"])*50)
    healthP = math.floor((game_state["current_health"]/game_state["max_health"])*50)
    energyP = math.floor((game_state["current_energy"]/game_state["max_energy"])*50)
    xpP = math.floor((game_state["current_xp"]/game_state["max_xp"])*50)
    
    food_meter = RoundRect(6, 9, 52, 5, 2, outline=color, fill=None)
    if foodP != 0:
        food_bar = Rect(7, 10, foodP, 3, outline=color, fill=color)
    health_meter = RoundRect(6, 25, 52, 5, 2, outline=color, fill=None)
    if healthP != 0:
        health_bar = Rect(7, 26, healthP, 3, outline=color, fill=color)
    energy_meter = RoundRect(6, 41, 52, 5, 2, outline=color, fill=None)
    if energyP != 0:
        energy_bar = Rect(7, 42, energyP, 3, outline=color, fill=color)
    xp_meter = RoundRect(6, 57, 52, 5, 2, outline=color, fill=None)
    if xpP != 0:
        xp_bar = Rect(7, 58, xpP, 3, outline=color, fill=color)
    new_group.append(food_meter)
    if food_bar:
        new_group.append(food_bar)
    new_group.append(health_meter)
    if health_bar:
        new_group.append(health_bar)
    new_group.append(energy_meter)
    if energy_bar:
        new_group.append(energy_bar)
    new_group.append(xp_meter)
    if xp_bar:
        new_group.append(xp_bar)
    new_group.x = 0
    new_group.y = 0
    bar_group.pop()
    bar_group.append(new_group)
    bar_group.hidden = False
        

#This should handle state changes for layer 1 menu_group
def selected_index(menu):
    for i in range(len(menu)):
        if menu[i].selected:
            return i
    return -1

def reset_select_state():
    for item in game_state["current_screen"]:
        item.selected = False

def update_menu():    
    new_group = displayio.Group()
    num_menu_items = 0
    for menu_item in game_state["current_screen"]:
        if (menu_item.selected):
            #invert colors to indicate selection
            new_text_area = label.Label(font=font, text=menu_item.text, color=bg_color, background_color=color)
        else:
            #display with normal colors
            new_text_area = label.Label(font=font, text=menu_item.text, color=color, background_color = bg_color)
        y = 1 + ( (10 + menu_item.y_padding) * num_menu_items )
        x = 5 + menu_item.x_padding
        new_text_area.anchor_point = (0,0)
        new_text_area.anchored_position = (x,y)
        num_menu_items += 1
        new_group.append(new_text_area)
    menu_group.pop()
    menu_group.append(new_group)

def tick(): #global clock for handling things like food decay
    # state variable decay
    # food ticks down
    game_state["current_food"] = max(0, game_state["current_food"] - game_state["food_decay_rate"])

    # health ticks down if poop or low food ; otherwise ticks up
    if game_state["current_food"] <= 25 or game_state["poop"]:
        game_state["current_health"] = max(0, game_state["current_health"] - game_state["health_decay_rate"])
    else:
        game_state["current_health"] = min(100, game_state["current_health"] + game_state["health_decay_rate"])

    #energy should decay to the center and maintain at 50 UNLESS poop, in which case it can decay to 0
    if game_state["current_energy"] < 50 and game_state["poop"] == False:
        game_state["current_energy"] += game_state["energy_decay_rate"]
    elif game_state["current_energy"] > 50 or game_state["poop"] == True:
        game_state["current_energy"] = max(0, game_state["current_energy"] - game_state["energy_decay_rate"])
    else:
        pass

    #check for state-based changes
    #If health = 0, die
    #

    # random chance for events
    poop_chance = 1
    if random.randint(0,10) < poop_chance:
        poop()

    # refresh screen
    if game_state["current_screen"] == main_menu:
        update_menu()
        update_bars()
    print(game_state["current_food"])
    print(game_state["current_health"])
    print(game_state["current_energy"])


def feed():
    print('food time!')
    #check for overfeeding, penalize HEALTH and ENERGY
    if game_state["current_food"] == 100:
        game_state["current_health"] = max(0, game_state["current_health"] - 10)
        game_state["current_energy"] = max(0, game_state["current_energy"] - 10)
    else:
        game_state["current_food"] = min(100, game_state["current_food"] + 10)
    
def treat():
    print('treat!')
    game_state["current_energy"] = min(100, game_state["current_energy"] + 10)

def pet():
    print('gimme da pets!')
    game_state["current_energy"] = max(0, game_state["current_energy"] - 10)
    
def clean():
    print('clean it up!')
    game_state["poop"] = False
    # remove poop stink overlay art
    game_state["current_energy"] += 10

def poop():
    print('poopin!')
    game_state["poop"] = True
    # add poop stink overlay art

def test_synth():    
    note1=synthio.Note(frequency=pango.note_fq[user_scale[0]][4], waveform=pango.wave_square, envelope=pango.pluck_env, filter = pango.lpf1)
    note2=synthio.Note(frequency=pango.note_fq[user_scale[2]][4], waveform=pango.wave_square, envelope=pango.pluck_env, filter = pango.lpf2)
    note3=synthio.Note(frequency=pango.note_fq[user_scale[4]][3], waveform=pango.wave_square, envelope=pango.pad_env, filter = pango.lpf1)
    
    synth.press(note1)
    time.sleep(pango.note_length_s[2])
    synth.release(note1)
    synth.press(note2)
    time.sleep(pango.note_length_s[2])
    synth.release(note2)
    synth.press(note3)
    time.sleep(pango.note_length_s[4])
    synth.release(note3)

def menu_click_sound():
    click=synthio.Note(frequency=pango.note_fq[user_scale[0]][7], waveform=pango.wave_square, envelope=pango.click_env, filter = pango.lpf1)
    synth.press(click)

def screen_switch_sound():
    num_steps = 50
    initial_frequency = 880  # Start at a higher frequency
    final_frequency = 220    # End at a lower frequency
    step_duration = pango.note_length_s[4] / num_steps
    for i in range(num_steps):
        # Calculate the current frequency
        frequency = initial_frequency - (initial_frequency - final_frequency) * (i / num_steps)
        envelope = synthio.Envelope(attack_time=0.01, decay_time=0.1, sustain_level=0.5, release_time=0.1)
        note = synthio.Note(frequency = frequency, waveform = pango.wave_square, envelope = envelope, filter = pango.lpf1)
        synth.press(note)
        time.sleep(step_duration)
        synth.release(note)
        time.sleep(step_duration)

def rando_note():
    octaves = [3,4,5]
    return synthio.Note(frequency=pango.note_fq[dUtils.ranDex(user_scale)][dUtils.ranDex(octaves)], waveform=pango.wave_square, envelope=pango.pluck_env, filter = pango.lpf1)
    
def rando_length():
    return dUtils.ranDex(pango.note_length_s)

def rando_choon():
    choon_length = 4 #number of notes
    choon = []
    for i in range(choon_length):
        choon.append({"note": rando_note(), "time": pango.note_length_s[2]})
        
    for j in range(choon_length):
        synth.press(choon[j]["note"])
        time.sleep(choon[j]["time"])
        synth.release(choon[j]["note"])

update_menu()
update_bars()

while True:
    now = time.monotonic_ns()
    idle(now)

    if now > last_tick + tick_speed:
        tick()
        last_tick = now

    position = encoder.position
    
    if game_state["current_screen"] != main_menu:
        if position < last_position:
            print('up')
            game_state["current_selection"].selected = False
            game_state["current_selection"] = game_state["current_selection"].next
            game_state["current_selection"].selected = True
            menu_click_sound()
            update_menu()
            last_position = position
        
        if position > last_position:
            print('down')
            game_state["current_selection"].selected = False
            game_state["current_selection"] = game_state["current_selection"].prev
            game_state["current_selection"].selected = True
            update_menu()
            menu_click_sound()
            last_position = position
        
    if not buttons[0].value:
        if switched == False:
            switched = True
            last_switch = now    

            if game_state["current_selection"] == care_menu[0]:
                feed()
                rando_choon()
            elif game_state["current_selection"] == care_menu[1]:
                treat()
            elif game_state["current_selection"] == care_menu[2]:
                pet()
            elif game_state["current_selection"] == care_menu[3]:
                clean()
                
    if not buttons[1].value:
        if switched == False:
            switched = True
            last_switch = now    
            print("Vol+")
            if mixer.voice[0].level+0.1 > 1.00:
                mixer.voice[0].level = 1
            else:
                mixer.voice[0].level = mixer.voice[0].level + 0.1
            print(mixer.voice[0].level)
        
    if not buttons[2].value:
       if switched == False:
            switched = True
            last_switch = now     
            print("Left button!")
            # should navigate leftward -   care menu <-> main menu <-> synth menu
            if game_state["current_screen"] == main_menu:
                game_state["current_screen"] = care_menu
                reset_select_state()
                bar_group.hidden = True
                game_state["current_selection"] = care_menu[0]
                game_state["current_selection"].selected = True
                #screen_switch_sound()
                update_menu()
            elif game_state["current_screen"] == care_menu:
                pass
            elif game_state["current_screen"] == synth_menu:
                game_state["current_screen"] = main_menu
                game_state["current_selection"] = None
                reset_select_state()
                update_bars()
                screen_switch_sound()
                update_menu()
        
    if not buttons[3].value:
        if switched == False:
            switched = True
            last_switch = now    
            print("Vol-")
            if mixer.voice[0].level-0.1 < 0.00:
                mixer.voice[0].level = 0
            else:
                mixer.voice[0].level = mixer.voice[0].level - 0.1
            print(mixer.voice[0].level)

    if not buttons[4].value:
        if switched == False:
            switched = True
            last_switch = now    
            print("Right button!")
            # should navigate rightward -   care menu <-> main menu <-> synth menu
            if game_state["current_screen"] == main_menu:
                game_state["current_screen"] = synth_menu
                reset_select_state()
                bar_group.hidden = True
                game_state["current_selection"] = synth_menu[0]
                game_state["current_selection"].selected = True
                screen_switch_sound()
                update_menu()
            elif game_state["current_screen"] == care_menu:
                game_state["current_screen"] = main_menu
                game_state["current_selection"] = None
                reset_select_state()
                screen_switch_sound()
                update_bars()
                update_menu()
            elif game_state["current_screen"] == synth_menu:
                pass
        
    #attempt at a debounce; feels long, but much shorter still bounces.
    if now > last_switch + 500000000:  #  500 ms :(
        switched = False