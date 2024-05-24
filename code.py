import board
import displayio
import rotaryio
import digitalio
import time
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import label
from adafruit_display_shapes.triangle import Triangle
from adafruit_display_shapes.roundrect import RoundRect
from gameMenus import care_menu, main_menu, synth_menu

display = board.DISPLAY
font = bitmap_font.load_font('/font/Hyperlight.bdf')
color = 0xFFFFFF
bg_color = 0x000000

def selected_index(menu):
    for i in range(len(menu)):
        if menu[i].selected:
            return i
    return -1

current_screen = main_menu
#current_selection = current_screen[0]
 
def draw_triangle(x0 = 1, y0 = 1, state='closed'):
    global color
    x1 = x0
    x2 = x0+2
    y1 = y0+5
    y2 = y0+2
    new_triangle = Triangle(x0,y0,x1,y1,x2,y2,fill=color,outline=color)
    return new_triangle
    
def reset_select_state(menu_item_list):
    for item in menu_item_list:
        item.selected = False
        
def load_meters(current_group):
    meters = displayio.Group()
    hunger_meter = RoundRect(6, 9, 52, 5, 2, outline=color, fill=None)
    energy_meter = RoundRect(6, 25, 52, 5, 2, outline=color, fill=None)
    mood_meter = RoundRect(6, 41, 52, 5, 2, outline=color, fill=None)
    xp_meter = RoundRect(6, 57, 52, 5, 2, outline=color, fill=None)
    meters.append(hunger_meter)
    meters.append(energy_meter)
    meters.append(mood_meter)
    meters.append(xp_meter)
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
        
        #do I even want the triangles? little 2px circles? nothing?
        #new_triangle = draw_triangle(x-4, y+1)
        #text_area_group.append(new_triangle)
        
        text_area_group.append(new_text_area)
    if menu_item_list == main_menu:
            text_area_group = load_meters(text_area_group)
    display.root_group = text_area_group
    
display_menu(current_screen)


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
    
while True:
    now = time.monotonic_ns()
    
    
    position = encoder.position
    # This mostly works. Seems to require two clicks of the wheel to move one space TODO fix it
    
    if current_screen != main_menu:
        if position > last_position:
            print('+')
            current_selection.selected = False
            current_selection = current_selection.next
            current_selection.selected = True
            last_position = position
            display_menu(current_screen)
        
        if position < last_position:
            print('-')
            current_selection.selected = False
            current_selection = current_selection.prev
            current_selection.selected = True
            last_position = position
            display_menu(current_screen)
        
    if not buttons[0].value:
        if switched == False:
            switched = True
            last_switch = now    
            print("Center button!")
            print(current_selection.text + " action GO!")
            
        
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
                display_menu(current_screen)
            elif current_screen == care_menu:
                pass
            elif current_screen == synth_menu:
                current_screen = main_menu
                reset_select_state(current_screen)
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
                display_menu(current_screen)
            elif current_screen == care_menu:
                current_screen = main_menu
                reset_select_state(current_screen)
                display_menu(current_screen)
            elif current_screen == synth_menu:
                pass
        
    #attempt at a debounce        
    if now > last_switch + 500000000:  #  500 ms :(
        switched = False