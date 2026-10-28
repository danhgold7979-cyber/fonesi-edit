from pathlib import Path
from PIL import Image
from PySide6.QtCore import QObject,Signal,QUrl
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import QMediaPlayer,QAudioOutput,QVideoSink

class Playback(QObject):
    frame=Signal(object);position=Signal(object);failed=Signal(str);state=Signal(bool)
    def __init__(self,parent=None):
        super().__init__(parent);self.player=QMediaPlayer(self);self.audio=QAudioOutput(self);self.audio.setVolume(.8)
        self.sink=QVideoSink(self);self.player.setAudioOutput(self.audio);self.player.setVideoSink(self.sink)
        self.sink.videoFrameChanged.connect(self.on_frame);self.player.positionChanged.connect(lambda ms:self.position.emit(ms*1000))
        self.player.errorOccurred.connect(lambda error,text:self.failed.emit(text))
        self.player.playbackStateChanged.connect(lambda state:self.state.emit(state==QMediaPlayer.PlaybackState.PlayingState))
    def on_frame(self,frame):
        image=frame.toImage()
        if image.isNull():return
        image=image.convertToFormat(QImage.Format.Format_RGBA8888)
        pil=Image.frombytes('RGBA',(image.width(),image.height()),bytes(image.bits()),'raw','RGBA',image.bytesPerLine()).convert('RGB')
        self.frame.emit(pil)
    def load(self,path:Path):self.player.stop();self.player.setSource(QUrl.fromLocalFile(str(path.resolve())))
    def toggle(self):
        if self.player.playbackState()==QMediaPlayer.PlaybackState.PlayingState:self.player.pause()
        else:self.player.play()
    def seek(self,time_us):self.player.setPosition(round(time_us/1000))
    def stop(self):self.player.stop()
