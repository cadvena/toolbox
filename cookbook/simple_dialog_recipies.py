import PySimpleGUI as sg
from PySimpleGUI import popup_yes_no
"""
Simple pop-ups reference: 
https://pysimplegui.readthedocs.io/en/latest/#high-level-api-calls-popups

"""

# Prompt for text input:
# result = sg.popup_get_text("Enter something", title = "My Title", keep_on_top = True)

# Prompt for password:
for i in range(3):
    result = sg.popup_get_text("Enter secret text.", title = "My Title", keep_on_top = True,
                               password_char = "*")
    if result: break
print('Password:', len(result) * '*')

# Request a yes/no response.
print('You responded:', popup_yes_no('Do you put ketchup on your eggs?', title = "My Title",
                               keep_on_top = True))

# Display a dialog for with long (scrollable) text
lst = ''.join([f'This is sentence {i+1} of 100.  \n' for i in range(100)])
sg.popup_scrolled(lst, title = "My Title", keep_on_top = True)

# result = sg.popup_no_wait('This popup will not pause python kernel processing.',
#                           title = "My Title",  keep_on_top = True)


