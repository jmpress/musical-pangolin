from MenuItem import MenuItem

#Define menus as list of menu items
main_menu = [  #does this even need to be a menu? The selections don't do anything.
    MenuItem('HUNGER', x_padding = 3, y_padding = 6),
    MenuItem('ENERGY', x_padding = 3, y_padding = 6),
    MenuItem(' MOOD ', x_padding = 3, y_padding = 6),
    MenuItem('  XP  ', x_padding = 3, y_padding = 6)
]

care_menu = [
    MenuItem('FEED '),
    MenuItem('TREAT'),
    MenuItem('PET  '),
    MenuItem('CLEAN')
]

synth_menu = [
    MenuItem('FILTER'),
    MenuItem('LFO'),
    MenuItem('WAVETBL'),
]
    

#define the order of the menu items and links between adjacent items
care_menu[0].selected = True
care_menu[0].next = care_menu[1]
care_menu[0].prev = care_menu[3]
care_menu[1].next = care_menu[2]
care_menu[1].prev = care_menu[0]
care_menu[2].next = care_menu[3]
care_menu[2].prev = care_menu[1]
care_menu[3].next = care_menu[0]
care_menu[3].prev = care_menu[2]

main_menu[0].next = main_menu[1]
main_menu[0].prev = main_menu[3]
main_menu[1].next = main_menu[2]
main_menu[1].prev = main_menu[0]
main_menu[2].next = main_menu[3]
main_menu[2].prev = main_menu[1]
main_menu[3].next = main_menu[0]
main_menu[3].prev = main_menu[2]

synth_menu[0].selected = True
synth_menu[0].next = synth_menu[1]
synth_menu[0].prev = synth_menu[2]
synth_menu[1].next = synth_menu[2]
synth_menu[1].prev = synth_menu[0]
synth_menu[2].next = synth_menu[0]
synth_menu[2].prev = synth_menu[1]