"""Offline, real FFmpeg/FFprobe smoke for the reproducible Batch planning benchmark."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'),
                    reason='Real FFmpeg and FFprobe tools required')
def test_small_real_media_benchmark_outputs_bounded_machine_labeled_json(tmp_path):
    root=Path(__file__).resolve().parents[1]
    report=tmp_path/'benchmark.json'
    command=[sys.executable,str(root/'scripts'/'benchmark_batch.py'),
             '--copies','3','--output',str(report)]
    completed=subprocess.run(command,cwd=root,capture_output=True,
                             text=True,errors='replace',timeout=90,check=True)
    result=json.loads(report.read_text(encoding='utf-8'))
    assert result==json.loads(completed.stdout)
    assert result['schema_version']==1
    assert result['scenario']=='synthetic-ffprobe-batch-planning-only'
    assert result['fixture_count']==result['planned_count']==3
    assert result['failed_count']==0
    assert result['elapsed_seconds']>0 and result['planning_files_per_second']>0
    assert result['rss_before_bytes']>0 and result['rss_after_bytes']>0
    assert result['peak_python_traced_bytes']>=0
    assert result['sample_source_unchanged'] is True
    assert result['generated_output_count']==0 and result['progress_complete']
    assert 'ffprobe' in result['ffprobe_version'].lower()
    assert 'ffmpeg' in result['ffmpeg_version'].lower()
    assert result['platform'] and result['python_version']
    assert 'not render duration/ETA' in result['limitations']
    assert list(tmp_path.iterdir())==[report]  # Fixture corpus lives only in TemporaryDirectory.
