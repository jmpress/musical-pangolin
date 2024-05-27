import board
import math
import displayio
import rotaryio
import digitalio
import time
import random
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import label
from adafruit_display_shapes.triangle import Triangle
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.roundrect import RoundRect
from gameMenus import care_menu, main_menu, synth_menu

display = board.DISPLAY
font = bitmap_font.load_font('/font/Hyperlight.bdf')
color = 0xFFFFFF
bg_color = 0x000000

# TODO load these in from save game state?
# max values are likely to stay constant however should still be accessible in the same scope as the current values, so if this gets changed into a game state object, include the max values.
current_hunger=0
max_hunger=100
hunger_decay_rate=0.026
current_energy=100
max_energy=100
energy_decay_rate=0.5
current_mood=100
max_mood=100
mood_decay_rate = 0.1
current_xp=0
max_xp=10
level=1     #where is this information expressed in game to the user?

def selected_index(menu):
    for i in range(len(menu)):
        if menu[i].selected:
            return i
    return -1

current_screen = main_menu
current_selection = None

main_menu_group = displayio.Group()

def reset_select_state(menu_item_list):
    for item in menu_item_list:
        item.selected = False
        
def load_meters(current_group):
    #global color, current_hunger, max_hunger, current_energy, max_energy, current_mood, max_mood, current_xp, max_xp
    hunger_bar = None
    energy_bar = None
    mood_bar = None
    xp_bar = None
    hungerP = math.floor((current_hunger/max_hunger)*52)
    energyP = math.floor((current_energy/max_energy)*52)
    moodP = math.floor((current_mood/max_mood)*52)
    xpP = math.floor((current_xp/max_xp)*52)
    meters = displayio.Group()
    hunger_meter = RoundRect(6, 9, 52, 5, 2, outline=color, fill=None)
    if hungerP != 0:
        hunger_bar = Rect(7, 10, hungerP, 3, outline=color, fill=color)
    energy_meter = RoundRect(6, 25, 52, 5, 2, outline=color, fill=None)
    if energyP != 0:
        energy_bar = Rect(7, 26, energyP, 3, outline=color, fill=color)
    mood_meter = RoundRect(6, 41, 52, 5, 2, outline=color, fill=None)
    if moodP != 0:
        mood_bar = Rect(7, 42, moodP, 3, outline=color, fill=color)
    xp_meter = RoundRect(6, 57, 52, 5, 2, outline=color, fill=None)
    if xpP != 0:
        xp_bar = Rect(7, 58, xpP, 3, outline=color, fill=color)
    meters.append(hunger_meter)
    if hunger_bar:
        meters.append(hunger_bar)
    meters.append(energy_meter)
    if energy_bar:
        meters.append(energy_bar)
    meters.append(mood_meter)
    if mood_bar:
        meters.append(mood_bar)
    meters.append(xp_meter)
    if xp_bar:
        meters.append(xp_bar)
    meters.x = 0
    meters.y = 0
    current_group.append(meters)
    return current_group
        
def display_menu(menu_item_list):
    global font
    global color
    text_area_group = displayio.Group()
    menu_item_text_areas = []
    line_group = displayio.Group()
    for menu_item in menu_item_list:
        if (menu_item.selected):
            #invert colors to indicate selection
            new_text_area = label.Label(font=font, text=menu_item.text, color=bg_color, background_color=color)
        else:
            #display with normal colors
            new_text_area = label.Label(font=font, text=menu_item.text, color=color, background_color = bg_color)
        y = 1 + ( (10 + menu_item.y_padding) * len(menu_item_text_areas) )
        x = 5 + menu_item.x_padding
        new_text_area.anchor_point = (0,0)
        new_text_area.anchored_position = (x,y)
        menu_item_text_areas.append(new_text_area)
        text_area_group.append(new_text_area)
    if menu_item_list == main_menu:
            text_area_group = load_meters(text_area_group)
    if len(main_menu_group[-1]) > 1:
        main_menu_group.pop()
    main_menu_group.append(text_area_group)
    display.root_group = main_menu_group

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
    
switched = False
last_switch = -1

#define animations
ani_tick = 200000000    #animation tick speed; TODO link this to Tempo
idle_anim= {
    "prev_time": -1,
    "next_frame": 0,
    "frames": "/img/basic_form_spritesheet.bmp",
    "x_offset": [0,-128,-256,-384,-256,-128]
}
main_sprite_bmp = displayio.OnDiskBitmap(idle_anim["frames"])
main_sprite_tiles = displayio.TileGrid(main_sprite_bmp, pixel_shader=main_sprite_bmp.pixel_shader)
main_sprite = displayio.Group()
main_sprite.append(main_sprite_tiles)
main_menu_group.append(main_sprite)

def idle(now):
    global idle_anim, ani_tick
    if now >= (idle_anim["prev_time"] + ani_tick):
        main_sprite.x = idle_anim["x_offset"][idle_anim["next_frame"]]
        idle_anim["prev_time"]=now
        idle_anim["next_frame"] = (idle_anim["next_frame"] + 1)%len(idle_anim["x_offset"])

last_tick = -1
tick_speed = 2000000000

def tick(now): #global clock for handling things like hunger decay
    global current_hunger, hunger_decay_rate, current_energy, energy_decay_rate, current_mood, mood_decay_rate
    if now >= last_tick + tick_speed:
        if current_hunger+hunger_decay_rate > 100:
            current_hunger = 100
        else:
            current_hunger += hunger_decay_rate

        if current_energy-energy_decay_rate < 0:
            current_energy = 0
        else:
            current_energy -= energy_decay_rate

        #mood should decay to the center and maintain at 50
        if current_mood < 50:
            current_mood += mood_decay_rate
        elif current_mood > 50:
            current_mood -= mood_decay_rate
        else:
            pass
    display_menu(current_screen)

display_menu(current_screen)

def feed():
    pass

def treat():
    global current_mood
    current_mood += 10
    if current_mood > 100:
        current_mood = 100

def pet():
    current_mood -= 10
    if current_mood < 0:
        current_mood = 0

def clean():
    pass

def poop():
    # add poop stink overlay art


while True:
    now = time.monotonic_ns()
    idle(now)
    tick(now)
    position = encoder.position
    
    if current_screen != main_menu:
        if position < last_position:
            print('up')
            current_selection.selected = False
            current_selection = current_selection.next
            current_selection.selected = True
            last_position = position
            display_menu(current_screen)
        
        if position > last_position:
            print('down')
            current_selection.selected = False
            current_selection = current_selection.prev
            current_selection.selected = True
            last_position = position
            display_menu(current_screen)
        
    if not buttons[0].value:
        if switched == False:
            switched = True
            last_switch = now    
            print(current_selection)
            if current_selection == care_menu[0]:
                treat()
                
            
        
    if not buttons[1].value:
        if switched == False:
            switched = True
            last_switch = now    
            print("Up Button!")
        
    if not buttons[2].value:
       if switched == False:
            switched = True
            last_switch = now     
            print("Left button!")
            # should navigate leftward -   care menu <-> main menu <-> synth menu
            if current_screen == main_menu:
                current_screen = care_menu
                reset_select_state(current_screen)
                current_selection = care_menu[0]
                current_selection.selected = True
                if main_menu_group[-1] != main_sprite:
                    main_menu_group.pop() #assumes last item is the menu
                display_menu(current_screen)
            elif current_screen == care_menu:
                pass
            elif current_screen == synth_menu:
                current_screen = main_menu
                current_selection = None
                reset_select_state(current_screen)
                if main_menu_group[-1] != main_sprite:
                    main_menu_group.pop() #assumes last item is the menu
                display_menu(current_screen)
        
    if not buttons[3].value:
        if switched == False:
            switched = True
            last_switch = now    
            print("Down Button")

    if not buttons[4].value:
        if switched == False:
            switched = True
            last_switch = now    
            print("Right button!")
            # should navigate rightward -   care menu <-> main menu <-> synth menu
            if current_screen == main_menu:
                current_screen = synth_menu
                reset_select_state(current_screen)
                current_selection = synth_menu[0]
                current_selection.selected = True
                if main_menu_group[-1] != main_sprite:
                    main_menu_group.pop() #assumes last item is the menu
                display_menu(current_screen)
            elif current_screen == care_menu:
                current_screen = main_menu
                current_selection = None
                reset_select_state(current_screen)
                if main_menu_group[-1] != main_sprite:
                    main_menu_group.pop() #assumes last item is the menu
                display_menu(current_screen)
            elif current_screen == synth_menu:
                pass
        
    #attempt at a debounce; feels long, but much shorter still bounces.
    if now > last_switch + 500000000:  #  500 ms :(
        switched = False