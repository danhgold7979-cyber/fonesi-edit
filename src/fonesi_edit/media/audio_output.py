"""Qt Multimedia output adapter for already-decoded interleaved float PCM.

This is a bounded PCM sink primitive. It does not schedule against video,
perform sample-rate conversion, mix tracks, or provide a master A/V clock.
"""
from __future__ import annotations

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QObject, Signal
from PySide6.QtMultimedia import QAudio, QAudioFormat, QAudioSink, QMediaDevices

from fonesi_edit.media.audio_decode import PCMBuffer


class AudioOutputError(RuntimeError):
    pass


class QtAudioOutput(QObject):
    state_changed = Signal(object)
    error_changed = Signal(str)

    def __init__(self, parent=None, *, device=None):
        super().__init__(parent)
        self.device = device or QMediaDevices.defaultAudioOutput()
        if self.device.isNull():
            raise AudioOutputError("No default audio output device is available.")
        self._sink: QAudioSink | None = None
        self._buffer: QBuffer | None = None

    def start(self, pcm: PCMBuffer) -> None:
        if not isinstance(pcm, PCMBuffer):
            raise AudioOutputError("A validated PCMBuffer is required.")
        if self._sink is not None:
            self.stop()
        fmt = QAudioFormat()
        fmt.setSampleRate(pcm.sample_rate)
        fmt.setChannelCount(pcm.channels)
        fmt.setSampleFormat(QAudioFormat.SampleFormat.Float)
        if not self.device.isFormatSupported(fmt):
            raise AudioOutputError(
                "Selected output device does not support the decoded float PCM format; "
                "resampling/conversion is not silently applied."
            )
        import struct
        payload = struct.pack("<" + "f" * len(pcm.samples), *pcm.samples)
        buffer = QBuffer(self)
        buffer.setData(QByteArray(payload))
        if not buffer.open(QIODevice.OpenModeFlag.ReadOnly):
            raise AudioOutputError("Could not open the PCM output buffer.")
        sink = QAudioSink(self.device, fmt, self)
        sink.stateChanged.connect(self._on_state_changed)
        sink.start(buffer)
        if sink.error() != QAudio.Error.NoError:
            sink.stop()
            buffer.close()
            raise AudioOutputError("Qt audio output failed to start.")
        self._buffer = buffer
        self._sink = sink

    def _on_state_changed(self, state) -> None:
        self.state_changed.emit(state)
        if self._sink is not None and self._sink.error() != QAudio.Error.NoError:
            self.error_changed.emit("Audio output device reported an error.")

    def stop(self) -> None:
        sink, buffer = self._sink, self._buffer
        self._sink = None
        self._buffer = None
        if sink is not None:
            sink.stop()
            sink.deleteLater()
        if buffer is not None:
            buffer.close()
            buffer.deleteLater()

    def state(self):
        return self._sink.state() if self._sink is not None else QAudio.State.StoppedState

    def processed_us(self) -> int:
        return self._sink.processedUSecs() if self._sink is not None else 0

    def bytes_free(self) -> int:
        return self._sink.bytesFree() if self._sink is not None else 0
