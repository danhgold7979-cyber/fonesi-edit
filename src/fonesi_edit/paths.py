from pathlib import Path
import os
import sys


def data_directory():
    configured=os.environ.get('FONESI_DATA_DIR')
    if configured:return Path(configured).resolve()
    if os.name=='nt':return Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'FonesiEdit'
    return Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))/'fonesi-edit'


def resource_directory(name):
    if getattr(sys,'frozen',False):return Path(sys._MEIPASS)/name
    source=Path(__file__).resolve().parents[2]/name
    return source if source.exists() else Path(__file__).resolve().parent/'resources'/name
