"""Explicit test-only pinned candidate: no downloader, installer or product grant."""
from pathlib import Path, PurePosixPath
from hashlib import sha256
from fractions import Fraction
import argparse
import json
import os
import platform
import stat
import sys
import zipfile

PIN = Path(__file__).with_name('windows_ffmpeg_candidate.json')


def safe_name(name, root):
    parts = PurePosixPath(name).parts
    reserved = {'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))}
    return (bool(parts) and parts[0] == root and not name.startswith('/') and
            not any(c in name for c in '\\:<>"|?*') and not any(ord(c)<32 for c in name) and
            all(p not in ('.','..') and not p.endswith((' ','.')) and
                p.split('.')[0].upper() not in reserved for p in parts))


def digest(path):
    h = sha256()
    with path.open('rb') as stream:
        size = os.fstat(stream.fileno()).st_size
        if not 0 <= size <= 256 * 1024**2:
            raise ValueError('Test file exceeds bound')
        total = 0
        while chunk := stream.read(min(1024 * 1024, size - total + 1)):
            total += len(chunk)
            if total > size:
                raise ValueError('Test file grew during fingerprint')
            h.update(chunk)
        if total != size:
            raise ValueError('Test file shrank during fingerprint')
    return h.hexdigest()


def extract_candidate(archive, target, pin):
    """Fresh controlled test namespace only; never a production installer."""
    info = archive.lstat()
    if not stat.S_ISREG(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
        raise ValueError('Regular archive required')
    if info.st_size != pin['size'] or digest(archive) != pin['sha256']:
        raise ValueError('Exact reviewed archive integrity mismatch')
    with zipfile.ZipFile(archive) as zipped:
        entries = zipped.infolist()
        if len(entries) > 10000 or sum(x.file_size for x in entries) > 1024**3:
            raise ValueError('Archive bounds exceeded')
        seen = set()
        for item in entries:
            name = item.filename
            # ZipInfo normalizes OS separators on Windows, and truncates NULs.
            # Refuse those raw spellings rather than validate only the alias.
            if (item.orig_filename != name or not safe_name(name, pin['root']) or
                name.casefold() in seen or item.file_size > 256 * 1024**2 or
                stat.S_ISLNK(item.external_attr >> 16) or item.flag_bits & 1 or
                item.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)):
                raise ValueError('Unsafe archive entry')
            seen.add(name.casefold())
        # Validate required entries before creating any output. ZIP integrity pin
        # authenticates unextracted docs/headers too; never execute those files.
        for name, expected in pin['members'].items():
            item = zipped.getinfo(pin['root'] + '/' + name)
            if item.is_dir() or item.file_size != expected['size']:
                raise ValueError('Required member mismatch')
        target.mkdir(mode=0o700)  # exclusive; no overwrite/adoption/delete fallback
        (target / 'bin').mkdir(mode=0o700)
        for name, expected in pin['members'].items():
            path = target / name
            h = sha256()
            total = 0
            with zipped.open(pin['root'] + '/' + name) as source, path.open('xb') as out:
                while chunk := source.read(1024 * 1024):
                    total += len(chunk)
                    if total > expected['size']:
                        raise ValueError('Expanded member exceeds pin')
                    h.update(chunk)
                    out.write(chunk)
            if total != expected['size'] or h.hexdigest() != expected['sha256']:
                raise ValueError('Required member hash mismatch; retain failed target')
    return target / 'bin' / 'ffmpeg.exe', target / 'bin' / 'ffprobe.exe'


def verify_members(target, pin):
    for name, expected in pin['members'].items():
        path = target / name
        info = path.lstat()
        if (not stat.S_ISREG(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400 or
            info.st_size != expected['size'] or digest(path) != expected['sha256']):
            raise ValueError('Candidate member changed')


def native_cases(ffmpeg, ffprobe, work, pin, report):
    from fonesi_edit.jobs.process import run_owned, ProcessCanceled
    from fonesi_edit.media.retirement import ValidationLifecycle
    from fonesi_edit.media.probe import inspect_media
    from fonesi_edit.media.observations import normalize_probe
    from fonesi_edit.media.frames import observe_frames
    from fonesi_edit.media.validation import ExpectedStream, validate_media, MediaValidationError
    from fonesi_edit.dependencies.checks import ToolPin, check_pair

    def generate(args):
        result = run_owned([str(ffmpeg), '-nostdin', '-hide_banner', '-v', 'error', '-n',
                            *args], timeout=30, max_output_bytes=256*1024)
        if result.returncode:
            raise AssertionError('Synthetic fixture generation failed')

    cfr = work / 'owned-cfr.mp4'
    generate(['-f', 'lavfi', '-i', 'testsrc2=size=48x32:rate=10:duration=1',
              '-vf', 'setsar=4/3', '-an', '-c:v', 'mpeg4', '-threads', '1', str(cfr)])
    expected = (ExpectedStream(0, 'video', 'mpeg4', Fraction(0), Fraction(1),
                              Fraction(1,100), 48, 32, Fraction(10)),)
    before = digest(cfr)
    pair = check_pair(ToolPin('ffmpeg', ffmpeg, pin['members']['bin/ffmpeg.exe']['sha256']),
                      ToolPin('ffprobe', ffprobe, pin['members']['bin/ffprobe.exe']['sha256']),
                      cfr, before, expected)
    report['pair'] = {'version': pair.ffmpeg_version.version,
                      'libraries': pair.ffmpeg_version.libraries,
                      'ffmpeg_response_sha256': pair.ffmpeg_version.response_sha256,
                      'ffprobe_response_sha256': pair.ffprobe_version.response_sha256}
    facts = normalize_probe(inspect_media(cfr, ffprobe))
    assert len(facts.streams) == 1 and facts.streams[0].sar == Fraction(4,3)
    assert 'NO_AUDIO_TRACK' in facts.diagnostics and not facts.render_ready
    report['cases'].append('compatible-pair-full-decode-black-frame-no-audio-SAR')

    vfr = work / 'owned-vfr.mp4'
    generate(['-protocol_whitelist', 'file,pipe', '-i', str(cfr), '-vf',
              r'select=not(eq(n\,1)+eq(n\,4))', '-fps_mode', 'vfr', '-an',
              '-c:v', 'mpeg4', '-threads', '1', str(vfr)])
    observed = normalize_probe(inspect_media(vfr, ffprobe))
    frames = observe_frames(vfr, ffprobe, observed, 0, max_frames=64)
    times = [x.pts * frames.time_base if x.pts is not None else None for x in frames.frames]
    assert times == [Fraction(n,10) for n in (0,2,3,5,6,7,8,9)]
    assert frames.status == 'OBSERVED_EOF' and not frames.render_ready
    report['cases'].append('actual-VFR-ordered-frame-facts-not-validity')
    report['frame_times'] = [str(x) for x in times]

    rotated = work / 'owned-rotation.mp4'
    generate(['-protocol_whitelist', 'file,pipe', '-display_rotation:v:0', '90',
              '-i', str(cfr), '-c', 'copy', str(rotated)])
    rotation_facts = normalize_probe(inspect_media(rotated, ffprobe))
    report['rotation_observation'] = rotation_facts.to_dict()
    rotation = rotation_facts.streams[0]
    assert rotation.display_matrix is not None and abs(rotation.rotation_degrees) == 90
    report['cases'].append('rotation-matrix-and-summary-facts')

    corrupt = work / 'owned-corrupt.mp4'
    data = bytearray(cfr.read_bytes())
    offset = 0
    damaged = False
    while offset + 8 <= len(data):
        size = int.from_bytes(data[offset:offset+4], 'big')
        if size < 8 or offset + size > len(data):
            raise AssertionError('Unexpected synthetic MP4 box layout')
        if data[offset+4:offset+8] == b'mdat':
            data[offset+8:offset+size] = bytes(size-8)
            damaged = True
        offset += size
    assert damaged
    with corrupt.open('xb') as stream:
        stream.write(data)
    corrupt_hash = digest(corrupt)
    inspect_media(corrupt, ffprobe)  # Probe completion is NOT full-decode success.
    try:
        validate_media(corrupt, ffprobe, ffmpeg, expected, timeout=30)
    except MediaValidationError:
        pass
    else:
        raise AssertionError('Corrupt synthetic media unexpectedly validated')
    assert digest(corrupt) == corrupt_hash
    report['cases'].append('corrupt-media-refused-source-unchanged')

    operation = object()
    lifecycle = ValidationLifecycle(operation)
    ready = bytearray()
    def progress(chunk):
        ready.extend(chunk)
    try:
        with lifecycle.validation_body():
            lifecycle.run(run_owned, [str(ffmpeg), '-nostdin', '-hide_banner', '-v', 'error',
                '-re', '-stream_loop', '-1', '-protocol_whitelist', 'file,pipe', '-i', str(cfr),
                '-progress', 'pipe:1', '-f', 'null', '-'], cancel=lambda: b'progress=' in ready,
                on_stdout=progress, timeout=15, max_output_bytes=256*1024)
    except ProcessCanceled:
        pass
    else:
        raise AssertionError('Actual FFmpeg cancellation was not observed')
    assert ready and lifecycle.confirmed_for(operation)
    assert lifecycle.mechanisms == ('WINDOWS_JOB_EMPTY',)
    assert digest(cfr) == before
    report['cases'].append('actual-FFmpeg-progress-cancel-job-empty')
    report['fixture_sha256'] = {x.name: digest(x) for x in (cfr,vfr,rotated,corrupt)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--work-dir', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--execute-reviewed-candidate', action='store_true')
    args = parser.parse_args(argv)
    if sys.platform != 'win32' or not args.execute_reviewed_candidate:
        parser.error('Explicit reviewed Windows execution grant required')
    if not all(x.is_absolute() for x in (args.archive,args.work_dir,args.report)):
        parser.error('Absolute owned paths required')
    pin = json.loads(PIN.read_text())
    report = {'status':'FAIL','scope':'test-only pinned Windows CPU synthetic corpus; no installer/product/GPU/renderer acceptance',
              'platform':platform.platform(),'python':platform.python_version(),
              'archive_sha256':pin['sha256'],'asset_id':pin['asset_id'],'cases':[]}
    # Reserve report BEFORE any candidate launch; no accidental overwrite.
    with args.report.open('x', encoding='utf-8') as output:
        try:
            args.work_dir.mkdir(mode=0o700)
            target = args.work_dir / 'candidate'
            ffmpeg,ffprobe = extract_candidate(args.archive,target,pin)
            verify_members(target,pin)
            # Standalone harness only. Absolute EXE alone does not constrain DLL
            # lookup; this fresh bin/CWD and trusted ephemeral runner are required.
            previous = Path.cwd()
            try:
                os.chdir(target / 'bin')
                native_cases(ffmpeg,ffprobe,args.work_dir,pin,report)
            finally:
                os.chdir(previous)
            verify_members(target,pin)
            report['members'] = pin['members']
            report['status'] = 'PASS'
        except BaseException as exc:
            report['failure_type'] = type(exc).__name__
            raise
        finally:
            json.dump(report,output,indent=2)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
