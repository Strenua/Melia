# Test extension
# You can base your own extensions on this file
import gtk

# Some handy tricks:
## Get Access to Preferences
# from melia_lib import preferences
# preferences.db_connect()
# preferences.load()
# preferences['preference_name']
##
## Modify all indicators (put in main())
# for indicator in melia.panel.indicators:
#     # do something here... (indicators are a proxy of gtk.ImageMenuItem)
##
## Theming (put in main()); NOTE: There will soon be a real themer built in. quiet mode should be disabled before using this.
# gtk.rc_parse('/path/to/melia/theme.rc')

# required in every extension:
def main(melia):
    '''Main Melia extension function. the 'melia' argument is the gtk.Window creating the launcher.
    You can also access Melia's other windows via melia.desk, melia.dash, melia.panel, etc.'''
    # ok, it works ;)
