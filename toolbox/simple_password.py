#!/usr/bin/env python

"""
System, Username, Password dialog utility built on PySimpleGUI.
Author: Chris Advena

Inspired by: https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Password_Login.py

Functions:
    get_credentials: credentials (system, user, pw) dialog box.

    get_user_pw: user / pw dialog box.

    pw_hash: create a sha_256 hash from a password.

Classes:
    _Examples: contains methods demonstrating use of the functions above.

"""
import PySimpleGUI as sg
from os import environ
from typing import Union
from collections import namedtuple
import hashlib
from toolbox import tb_cfg


# ##############################################################################
# Constants
# ##############################################################################
DEFAULT_USERNAME = environ['username']
EX_DBS = tb_cfg['ORACLE_DBS']['EXSCR']
# EX_DBS = ['PRD', 'TRN', 'STG', 'TST']


# ##############################################################################
# Custom Types
# ##############################################################################
CredentialsTuple = namedtuple(typename = 'CredentialsTuple',
                               field_names = ['system', 'user', 'pw'])
UserPwTuple = namedtuple(typename = 'UserPwTuple',
                          field_names = ['user', 'pw'])

# ##############################################################################
# Fucntions:
# ##############################################################################
"""
Functions:
    get_credentials: credentials (system, user, pw) dialog box.

    get_user_pw: user / pw dialog box.    
    
    pw_hash: create a sha_256 hash from a password.
    
"""


def get_credentials(window_title:str = 'Login',
                    systems:Union[list, tuple, set, str] = '',
                    user:str = '',
                    keep_on_top = True,
                    **kwargs) -> CredentialsTuple:
    """
    Open window/gui to get a user and pw from the end user.
    dialog user may:
        - select a system from a combo-box (if allowed by the developer)
        - enter username
        - enter password.
    developer may optionally:
        - specify a list of 1+ systems.  If len(systems) > 1, then the
            dialog user will be able to select a system from a combo-box.
        - specify default username: argument user or kwarg['id']).  Default: OS username
        - specify default password: kwarg of 'pw', 'pwd' or 'password'
                                    Providing as pw as an input to
                                    get_credentials is not a normal use case.
        - pass kwargs to the sqlalchemy.engine.create_engine


    :param window_title: Title to display in pop-up window
    :param systems: (list, tuple, set or str):  name of system, for example,
                    url or database name
    :param user: user (default: DEFAULT_USERNAME)
    hidden param pw: Generally not intended to be used in the popup.  It
                           exists for a special use case where user and
                           pw are already known, but the system has not
                           yet been chosen.
    :return: namedtuple, CredentialsTuple(system, user, pw)
    """
    assert type(systems) in [str, list, tuple, set]

    # sg.theme(tb_cfg['SG_THEME'])

    # See if pw was provided
    pw = ''
    for k in ['pw', 'pwd', 'password']:
        if k in kwargs.keys():
            pw = kwargs.pop(k)
            break
    pw = pw.strip ()

    # If user not provided, user = DEFAULT_USERNAME
    if not user:
        user = DEFAULT_USERNAME
        for k in ['user', 'id']:
            if k in kwargs.keys():
                user = kwargs.pop (k)
                break
    user = user.strip()

    # If systems is list-like and contains multiple values, allow user to select.
    # If systems is a string, then i
    if systems is None or len(systems) == 0:
        # No systems provided.  Don't show systems in the credentials window.
        sg_system = [sg.Input(key = '-system-',
                              default_text = '',
                              visible = False)]
    elif type(systems) == str:
        # One system provided.
        systems = systems.strip()
        sg_system = [sg.Text(systems.strip(), size = (40,1)), sg.Input(key = '-system-',
                                                   default_text = systems,
                                                   visible = False)]
    elif len(systems) == 1:
        sg_system = [sg.Text(systems[0].strip(), size = (40,1)), sg.Input(key = '-system-',
                                                 default_text = systems[0],
                                                 visible = False)]
    else:
        sg_system = [sg.Text('System'), sg.Combo(key = '-system-', values = systems, default_value = systems[0])]

    layout = [
        [sg.Titlebar(title = window_title)],
        # [sg.Text(window_title, size = (40, 1), font = 'Any 15')],
        sg_system,
        [sg.Text('Username'), sg.Input(key = '-user-', default_text = user)],
        [sg.Text('Password'), sg.Input(key = '-pw-', password_char = '*',
                                       default_text = pw, focus = True)],
        [sg.Text('', key = '-msg-', text_color = 'red', size = (40,1))],
        [sg.OK(), sg.Cancel()],
    ]

    window = sg.Window(window_title, layout,
                       auto_size_text = False,
                       default_element_size = (10, 1),
                       text_justification = 'l',
                       return_keyboard_events = True,
                       grab_anywhere = False,
                       keep_on_top = keep_on_top,
                       resizable = True,
                       **kwargs)

    while True:
        event, values = window.read()
        if event in ['OK']:
            if values['-user-'] and values['-pw-']:
                system = values['-system-'].strip()
                user = values['-user-'].strip()
                pw = values['-pw-']
                break
            else:
                window['-msg-'].update("!!! user and pw required !!!")
        elif event in ('Cancel', sg.WIN_CLOSED):
            system, user, pw = '', '', ''
            break

    window.close()

    return CredentialsTuple(system, user, pw)


def get_user_pw(user:str = DEFAULT_USERNAME, **kwargs):
    """
    Username / password dialog box.
    dialog user may:
        - enter username and password.
    developer may optionally:
        - specify default username
        - specify default pw (rarely appropriate)
        - pass kwarg['system'], which will affect the
             window title and the prompt, but has not behavioral effect.
        - pass kwargs to the sqlalchemy.engine.create_engine
    :param user: username
    :param kwargs: kwarg['system'] is used direclty in this function.
                   Other kwargs are passed to get_credentials().
                   kwarg['system']: the name of the system to log into.  This
                                    is used only to build the GUI title.
    :return:
    """
    system = ''
    for sys in ['sys', 'system', 'host', 'hosts']:
        if sys in kwargs.keys():
            system = kwargs.pop(sys)
            if type(system) != str:
                system = system[0]
    title = f'{system} Login'.title().strip()
    prompt = f'Enter credentials:'
    if system:
        prompt = f'Enter credentials for {system.title()}:'
    host, user, pw = get_credentials(window_title = title,
                                     systems = prompt,
                                     user = user,
                                     **kwargs)
    return UserPwTuple(user, pw)


def pw_hash(phrase: str):
    """
    For future use.
    :param phrase: string to hash
    :return: sha256 hash of phrase
    """
    # Initializing the sha256() method
    sha256 = hashlib.sha256 ()
    # Pass phrase to sha256 (i.e., update function with phrase)
    sha256.update (phrase)
    # sha256.hexdigest() hashes phrase
    # and returns output in hexadecimal format
    return sha256.hexdigest ()


# ##############################################################################
# Examples
# ##############################################################################

class _Examples:
    @classmethod
    def get_user_pw_basic(cls):
        user, pw = get_user_pw(system='My App')
        print(user, '/', len(pw)*'*')

    @classmethod
    def get_credentials_basic(cls):
        creds = get_credentials()
        print(creds.system, creds.user, len(creds.pw) * '*')

    @classmethod
    def get_credentials(cls):
        title = 'Log into My Database'
        systems = EX_DBS[0]
        user = environ['user']
        creds = get_credentials(window_title = title, systems = systems, user = user)
        print(creds.system, creds.user, len(creds.pw) * '*')

    @classmethod
    def try_many_credentials(cls):
        inputs = [['title', 'sys', 'id'],
                  [None, None, None],
                  ['title', None, None],
                  ['title', None, 'id'],
                  ['title', 'sys', None],
                  [None, 'sys', None],
                  [None, 'sys', 'id'],
                  ['title', 'sys', None],
                  [None, None, 'id'],]
        for row in inputs:
            creds = get_credentials(window_title = row[0], systems = row[1], user = row[2])
            print('defaults:  ', row)
            print('    output:', creds.system, creds.user, creds.pw)

def main():
    pass

if __name__ == '__main__':
    # main()
    _Examples.get_credentials()
