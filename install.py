#!/usr/bin/env python3

# Photon installer script

import os
import sys
from core.dependencies import haveDependencies, resolveDependencies

with open('core/photon.py') as w:
    code = w.read()

code = code.replace('PHOTON_INSTALL_PATH =', f'PHOTON_INSTALL_PATH = r"{os.getcwd()}/core" #')

if sys.platform in {'linux', 'linux2', 'darwin'}:
    try:
        with open('/usr/local/bin/photon','w') as w:
            w.write(code)
        os.chmod('/usr/local/bin/photon',0o777)
        print("Successfully installed! Now you can use the photon command!")
    except PermissionError:
        print(
        " Please run this script with the 'sudo' command.\n",
        "Example:\n    'sudo python3 install.py'")
elif sys.platform in {'win32', 'cygwin', 'msys'}:
    p_dir = os.path.expandvars('%ProgramFiles%\\Photon')
    try:
        if not os.path.exists(p_dir):
            os.mkdir(p_dir)
        with open(os.path.join(p_dir, 'photon.py'), 'w') as w:
            w.write(code)
        with open(os.path.join(p_dir, 'photon.bat'), 'w') as w:
            w.write('@echo off\nset bat_dir=%~dp0\npython "%bat_dir%photon.py"')
        os.system(f'setx /M PATH "%PATH%;{p_dir}"')
        print("Successfully installed! Now you can use the photon command!")
    except PermissionError:
        print('The installation has not been completed. Try to run the script as administrator')
else:
    print('Automatic installation in this system is not supported yet.')
    exit()

if not haveDependencies('c', sys.platform):
    resolveDependencies('c', sys.platform)
