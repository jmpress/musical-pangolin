#This is basically the game state as a class, to be saved to the micro SD card

class Pango():
    def __init__(self, **kwargs):  #read kwargs in from JSON save state file
        self.name	# user input, 4 characters like old final fantasy, selected with rotary encoder, use HyperLight font
    	self.scale	# string from scale_name in pangolinScales.py
    	self.happiness	# 0-100
    	self.energy	# 0-100
    	self.mood	# calculated from happiness and energy
    	self.xp		# starts at 0; 1 xp per Feed; 1 xp per bar played?
    	self.level 	# starts at 1; 16 to tier 2, 64 to tier 3?
    	self.evolution 	# ['basic', 'crystal', 'metal', 'galaxy', 'astral', 'industrial', 'death']
    	self.instr	# a synthio.Synthesizer.Note object
    	self.drums	# array of synthio.Synthesizer.Note objects
    	
    	
#this should go somewhere else

#new user intro flow
seed = 3 #(find a value unique to hardware; MAC address?
