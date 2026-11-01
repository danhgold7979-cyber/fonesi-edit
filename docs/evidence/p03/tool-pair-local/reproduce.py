"""New wrapper integration; retained approved binaries/fixture, no regeneration."""
from pathlib import Path
from hashlib import sha256
from fractions import Fraction as F
from dataclasses import asdict
import json,platform,sys
from fonesi_edit.dependencies.checks import ToolPin,check_pair
from fonesi_edit.media.validation import ExpectedStream
root=Path(__file__).resolve().parents[4]
output=Path(sys.argv[1]);assert not output.exists(),'Never overwrite evidence'
fixture=root/'runtime/media-decode-negative/generated.mp4'
ffmpeg=ToolPin('ffmpeg',Path('/usr/bin/ffmpeg'),'e8a8d46f5225f3062cec7c07fb145d58ae73c603cb740dcd5bad34bfb54e455a')
ffprobe=ToolPin('ffprobe',Path('/usr/bin/ffprobe'),'cefc5f81c0b18429cdbf8fa5a89e1e9c759235e10f93f9b329ff1b2fdff26f46')
result=check_pair(ffmpeg,ffprobe,fixture,'c374672fd3188ba261043f82d93097e566bd3f64c5325af3c2c1e58e42f853a6',
                  (ExpectedStream(0,'video','h264',F(0),F(1),F(1,25),width=64,height=48,frame_rate=F(25)),))
report={'scope':'Actual Linux pair wrapper integration only; no Windows/codec/GPU/subtitle/full readiness',
        'platform':platform.platform(),'python':sys.version,'observation':asdict(result),
        'checks_source_sha256':sha256((root/'src/fonesi_edit/dependencies/checks.py').read_bytes()).hexdigest(),
        'harness_sha256':sha256(Path(__file__).read_bytes()).hexdigest()}
with output.open('x',encoding='utf-8') as stream:json.dump(report,stream,ensure_ascii=True,indent=2,default=str)
print('Pinned Linux pair/version/library/known fixture probe+decode/black RGB frame observation PASS')
