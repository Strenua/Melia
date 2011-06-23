import os

command = 'nautilus %s'

home = os.getenv('HOME')

ql = {'Home': home, 'Documents': home + '/Documents', 'Downloads': home + '/Downloads', 'Pictures': home + '/Pictures', 'Music': home + '/Music', 'Videos': home + '/Videos'}
