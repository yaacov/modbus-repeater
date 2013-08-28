from distutils.core import setup
import py2exe, sys, os

sys.argv.append('py2exe')

setup(
    options = {
        'py2exe': {
            'bundle_files': 1, 
            'compressed': True,
            'dll_excludes': ['w9xpopen.exe']
        }
    },
    console = [{'script': "mbs_server.py"}, {'script': "mbs_client.py"}],
    zipfile = None,
)
