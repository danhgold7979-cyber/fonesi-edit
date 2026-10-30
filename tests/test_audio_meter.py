"""Unit-level sample meter checks; no Qt/FFmpeg or hardware dependency."""
import math
import struct
import pytest

from fonesi_edit.audio_meter import AudioLevels,dbfs,measure_pcm,meter_bar


def test_silence_and_empty_pcm_buffers():
    empty=measure_pcm(b'','Int16',2)
    assert empty==AudioLevels(0,0,-math.inf,-math.inf,0,0)
    silent=measure_pcm(struct.pack('=hhhh',0,0,0,0),'Int16',2)
    assert silent.sample_count==4 and silent.rms==0
    assert silent.peak_dbfs==-math.inf and meter_bar(silent.rms_dbfs)==0


def test_int16_peaks_and_multichannel_rms():
    levels=measure_pcm(struct.pack('=hhhh',0,-32768,32767,0),'Int16',2)
    assert levels.sample_count==4 and levels.clipped_samples==2
    assert levels.peak==1 and levels.peak_dbfs==0
    assert levels.rms==pytest.approx(math.sqrt((1+(32767/32768)**2)/4))
    assert -3.05 < levels.rms_dbfs < -3.0
    assert meter_bar(levels.peak_dbfs)==600


def test_uint8_silence_signed_polarity_and_clip_warning():
    levels=measure_pcm(bytes([128,0,255,128]),'UInt8',1)
    assert levels.peak==1 and levels.clipped_samples==2
    assert levels.rms==pytest.approx(math.sqrt((0**2+1**2+(127/128)**2+0**2)/4))


def test_int32_full_scale_native_endian_and_mono():
    levels=measure_pcm(struct.pack('=ii',-2147483648,2147483647),'Int32',1)
    assert levels.peak==1 and levels.clipped_samples==2
    assert levels.rms==pytest.approx(math.sqrt((1+(2147483647/2147483648)**2)/2))


def test_float_above_full_scale_is_not_silently_clamped():
    levels=measure_pcm(struct.pack('=ffff',0.0,.25,-1.0,1.25),'Float',2)
    assert levels.peak==1.25
    assert levels.peak_dbfs>0
    assert levels.clipped_samples==2
    assert levels.rms==pytest.approx(math.sqrt((.25**2+1+1.25**2)/4))
    assert meter_bar(levels.peak_dbfs)==600


@pytest.mark.parametrize('data,kind,channels,reason',[
    (b'\0','Int16',1,'complete interleaved'),
    (struct.pack('=hh',0,1),'Int16',3,'complete interleaved'),
    (b'\0','BadFormat',1,'Unsupported'),
    (b'\0','UInt8',0,'channel'),
    (b'\0','UInt8',True,'channel'),
    (b'\0','UInt8',33,'channel'),
    (struct.pack('=f',float('nan')),'Float',1,'Non-finite'),
    (struct.pack('=f',float('inf')),'Float',1,'Non-finite'),
])
def test_invalid_pcm_fails_closed(data,kind,channels,reason):
    with pytest.raises(ValueError,match=reason):
        measure_pcm(data,kind,channels)


@pytest.mark.parametrize('amplitude',[float('nan'),float('inf'),-.1])
def test_invalid_dbfs_is_rejected(amplitude):
    with pytest.raises(ValueError,match='amplitude'):
        dbfs(amplitude)


def test_bar_range_silence_minus_sixty_and_clipping():
    assert meter_bar(-math.inf)==0
    assert meter_bar(-60)==0
    assert meter_bar(-30)==300
    assert meter_bar(0)==600
    assert meter_bar(3)==600
    with pytest.raises(ValueError):
        meter_bar(float('nan'))


def test_bytes_like_views_are_supported_without_mutation():
    source=bytearray(struct.pack('=hh',-100,100))
    before=bytes(source)
    assert measure_pcm(memoryview(source),'Int16',1).sample_count==2
    assert bytes(source)==before
