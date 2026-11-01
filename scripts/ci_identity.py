"""Fail CI on accidental merge-ref/default-branch checkout; write exact source identity."""
import json
import os
from pathlib import Path
import platform
import subprocess


def verify(expected):
    sha=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    if len(expected)!=40 or sha!=expected:
        raise RuntimeError(f'Wrong CI checkout: expected {expected!r}, got {sha}')
    return {'source_sha':sha,'source_tree':subprocess.check_output(['git','rev-parse','HEAD^{tree}'],text=True).strip(),
            'platform':platform.platform(),'python':platform.python_version()}

if __name__=='__main__':
    result=verify(os.environ['EXPECTED_SOURCE_SHA'])
    Path('foundation-source.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
