"""Qt audio output adapter tests with an injected fake device."""
from fractions import Fraction

import pytest

from fonesi_edit.media.audio_decode import PCMBuffer
from fonesi_edit.media.audio_output import AudioOutputError, QtAudioOutput


class FakeDevice:
    def __init__(self, supported=True, null=False):
        self.supported = supported
        self.null = null
    def isNull(self):
        return self.null
    def isFormatSupported(self, fmt):
        return self.supported


def _pcm():
    return PCMBuffer("a"*64, 0, 48000, 2, 2,
                     (0.1, -0.1, 0.2, -0.2), 2)


def test_audio_output_rejects_device_without_supported_float_format(qt_app):
    output = QtAudioOutput(device=FakeDevice(supported=False))
    with pytest.raises(AudioOutputError, match="does not support"):
        output.start(_pcm())
    assert output.state().name == "StoppedState"


def test_audio_output_rejects_missing_default_device(qt_app):
    with pytest.raises(AudioOutputError, match="No default"):
        QtAudioOutput(device=FakeDevice(null=True))


def test_audio_output_requires_validated_pcm_buffer(qt_app):
    output = QtAudioOutput(device=FakeDevice())
    with pytest.raises(AudioOutputError, match="PCMBuffer"):
        output.start(object())
