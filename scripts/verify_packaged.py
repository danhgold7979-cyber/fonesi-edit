from pathlib import Path
import argparse
import os
import subprocess
import time
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
root=Path(__file__).resolve().parents[1];exe=root/'dist/FonesiEdit'/('FonesiEdit.exe' if os.name=='nt' else 'FonesiEdit')
out=(args.output or root/'.local'/('packaged-proof-'+str(time.time_ns()))).resolve()
env=os.environ.copy();env.pop('PYTHONPATH',None);env['QT_QPA_PLATFORM']='offscreen'
subprocess.run([str(exe),'--verify',str(out)],cwd=exe.parent,env=env,check=True)
print('Verified packaged proof:',out/'proof.json')
