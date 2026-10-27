from threading import Event
import shutil
import pytest
from fonesi_edit.prototypes.media import MediaError, RenderSpec, create_fixture, extract_frame, probe, render

pytestmark = pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'), reason='FFmpeg tools unavailable')


def test_real_render_unicode_paths_filter_text_and_output_validation(tmp_path):
    files = create_fixture(tmp_path / 'thư mục 中文', duration=1)
    destination = tmp_path / "kết quả ' [x];$.mp4"
    calls = []
    result = render(files['source'], destination, RenderSpec(title="O'Brien: 100% [x]; ${not_shell}",
                    subtitles=files['subtitles'], logo=files['logo'], speed_px_s=10), calls.append)
    assert result['validated'] is True
    assert destination.is_file()
    actual = probe(destination)
    assert actual.video_codec == 'h264' and actual.audio_codec == 'aac'
    assert abs(actual.duration - probe(files['source']).duration) < 0.15
    assert calls[-1] == 1.0
    extract_frame(destination, tmp_path / 'frame.png', 0.2)
    assert (tmp_path / 'frame.png').stat().st_size > 1000
    assert not list(tmp_path.glob('.fonesi-p02-*'))


def test_logo_fixture_contains_visible_and_transparent_pixels(tmp_path):
    files = create_fixture(tmp_path, duration=0.5)
    import subprocess
    result = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(files['logo']),
        '-vf', 'alphaextract', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True, check=True)
    assert 0 in result.stdout and max(result.stdout) > 100


def test_render_does_not_overwrite_input_or_existing_output(tmp_path):
    source = tmp_path / 'source.mp4'
    source.write_bytes(b'unchanged')
    destination = tmp_path / 'out.mp4'
    destination.write_bytes(b'keep')
    with pytest.raises(FileExistsError):
        render(source, source, RenderSpec())
    with pytest.raises(FileExistsError):
        render(source, destination, RenderSpec())
    assert source.read_bytes() == b'unchanged'
    assert destination.read_bytes() == b'keep'


def test_failure_and_cancel_never_publish_a_successful_output(tmp_path):
    broken = tmp_path / 'broken.mp4'
    broken.write_bytes(b'not a movie')
    with pytest.raises(MediaError):
        render(broken, tmp_path / 'bad.mp4', RenderSpec())
    assert not (tmp_path / 'bad.mp4').exists()
    files = create_fixture(tmp_path / 'fixture', duration=2)
    cancel = Event()
    cancel.set()
    with pytest.raises(MediaError, match='hủy'):
        render(files['source'], tmp_path / 'canceled.mp4', RenderSpec(), cancel=cancel)
    assert not (tmp_path / 'canceled.mp4').exists()


@pytest.mark.parametrize('values', [{'x': float('nan')}, {'y': 2}, {'font_size': 0}, {'speed_px_s': float('inf')}])
def test_invalid_render_parameters_fail_before_ffmpeg(values):
    with pytest.raises(ValueError):
        RenderSpec(**values)
