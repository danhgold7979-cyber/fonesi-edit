from pathlib import Path
import os
from fonesi_edit.core.storage import Store
from fonesi_edit.services.tools import ToolManager
from fonesi_edit.services.tool_registry import install_windows_ffmpeg
root=Path(__file__).resolve().parents[1]/'.local/windows-tools';root.mkdir(parents=True,exist_ok=True)
result=install_windows_ffmpeg(ToolManager(root,Store(root/'registry.db')),progress=lambda stage,value:print(stage,'unknown' if value is None else f'{value:.1%}'))
print(result)
if os.environ.get('GITHUB_PATH'):
    with open(os.environ['GITHUB_PATH'],'a',encoding='utf8') as f:f.write(str(Path(result['ffmpeg']).parent)+'\n')
else:print('Add this folder to the current developer shell PATH:',Path(result['ffmpeg']).parent)
