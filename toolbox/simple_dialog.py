import PySimpleGUI as sg
from PySimpleGUI import popup_yes_no
"""
Simple pop-ups reference: 
https://pysimplegui.readthedocs.io/en/latest/#high-level-api-calls-popups

"""

# def input(*args, title: str = '', keep_on_top = True, **kwargs):
#     return sg.popup_get_text(*args, title = title, keep_on_top = keep_on_top, **kwargs)

def get_text(prompt: str, default_response: str = "", window_title: str = "",
          keep_on_top = True, **kwargs) -> str:
    """
    GUI version of native python 'input()' function
    https://docs.python.org/3/library/functions.html#input
    """
    window_title = window_title.title().strip()
    prompt = prompt.strip().capitalize()
    if not prompt:
        raise ValueError(f'prompt ("{prompt}") must be non-zero length and contain non-whitespace '
                         f'characters.')

    password_char = ''
    if 'password_char' in kwargs.keys():
        password_char = kwargs.pop('password_char')
        if type(password_char) != str:
            msg = f"Argument 'password_char' must be type str, not '{type(password_char)}'."
            raise TypeError(msg)

    result = None
    # attempts = 0
    # while result is None and attempts < 3:
    if True:
        layout = [
               [sg.Titlebar(title = window_title)],
               [sg.Text(prompt), sg.Input(key = '-response-', default_text = default_response,
                                          password_char = password_char)],
               [sg.Text('', key = '-msg-')],
               [sg.OK(), sg.Cancel()],
             ]

        window = sg.Window(window_title, layout,
                           auto_size_text = False,
                           default_element_size = (10, 1),
                           text_justification = 'l',
                           return_keyboard_events = True,
                           grab_anywhere = False,
                           resizable = True,
                           keep_on_top = keep_on_top,
                           **kwargs)

        while True:
            event, values = window.read()
            if event in ['OK']:
                if values['-response-'].strip():
                    result = values['-response-'].strip()
                    break
                else:
                    window['-msg-'].update("!!! user and pw required !!!")
            elif event in ('Cancel', sg.WIN_CLOSED):
                system, user, pw = '', '', ''
                break

        window.close()
        # del window
        # attempts += 1
    return result

def get_pw(prompt: str = 'Enter password', default_response: str = "", window_title: str = "",
          keep_on_top = True, **kwargs) -> str:
    return get_text(prompt = prompt, default_response = default_response,
                    window_title = window_title, keep_on_top = keep_on_top,
                    password_char = '*', **kwargs)

def yesno(*args, title: str = '', keep_on_top = True, **kwargs):
    return popup_yes_no(*args, title = title, keep_on_top = keep_on_top, **kwargs)

def popup_scrolled(*args, title: str = '', keep_on_top = True, **kwargs):
    return sg.popup_scrolled(*args, title = title, keep_on_top = keep_on_top, **kwargs)

def no_wait(*args, title: str = '', keep_on_top = True, **kwargs):
    return sg.popup_no_wait(*args, title = title, keep_on_top = keep_on_top, **kwargs)


if __name__ == '__main__':
    print(get_pw())
