"""Owned synthetic MPEG4 self-test fixture, not downloaded/user media.

Generated earlier by approved local FFmpeg7.1.5 testsrc2/setsar,48x32,5fps,1s,
SAR4:3,noaudio. Exact fixture reused; not a full decoder corpus. Encoded source
avoids opaque binary publishing. Materialization never overwrites or cleans paths.
"""
import base64
from hashlib import sha256
from fractions import Fraction
from pathlib import Path
import tempfile
from fonesi_edit.media.validation import ExpectedStream

SIZE = 2478
SHA256 = 'f643fb7c7f55b4d53d1cfe88c6aebee4b4c5b1d2c13185415662344ff4552ad8'
DATA = (
    b'AAAAHGZ0eXBpc29tAAACAGlzb21pc28ybXA0MQAAAAhmcmVlAAAGIG1kYXQAAAGzABAHAAABthGBNguGsBoPADh8JIHSqp08'
    b'H3lAN1lWXl6sv+wmSFw+HharSp/8WYSKv/UZ9u4o9/XDwHgYD0HgIIcG4DFoKoGWBlIMBosA2ClBugwfjkQAYcAwgB+DDkGU'
    b'qVwUwIgfjgGXLA+BjozCH5WwDwMDOAeBsGD4dDoHgf7cdJwQdYxOqAOH4IKT46A8Xl7GlQGgZSolbVqB1mlnh+rYxnK8ZB8P'
    b'QeB/sQeB/uQYtB4KApB4OApB4H+xBEaBuAwGweBgPQcAYDB+Cm6WAygHAdKgRQeDgKRyCsBVlh0LAYEIGCAXAxcJDbQ6Edth'
    b'O2PvA3S8deBhABhylCAyPy5UXN4q8zdHqeFpf4tLy9P6JQ8HjcogheGgMIQMAeB8SB40rA8xo8Bg/8CihfEivff8wnHmp6EM'
    b'v+0nHwglwlar+1+stMJu/t+I4+uqDLY1HgPAQUIPAQTIktVkfA0HOeZbTNyhBBm2G2FbFUNqlapkQ/K1TOVG0z728ubxRuV4'
    b'LgIacEAAxNiUR9D7zadUPlUyF6dOlH6XSxUXFxckjJeXp26iVJGG21GfbUFnv64iBxoP/gwkiWrEEDokD0fCUPgRUjBZQQdE'
    b'YIDY+CGDKGGt9aIKtS0xqbQ++3pYkV6WXXD4GbVApmQeAgfQPj6JwZoAwQhGAPEYGUiWmEHQZI2CGCkTCMCkBwH0ittu4Bov'
    b'HCpL8f/o+aT+jQlj/wg58yYDwH8eAckBk4jgoC4GqtsDvkmAd0uBgNyCTWP/CAmEn46SfH8Ssqi8fpy5MJHGBI/9tsstTfVt'
    b'ND4yQkCCnYEr6dphr37vsqi3IWAwf0dAq76WNVJFVo76DKVBYsH4gA+F/4thiBEB4CBxBlAMOSwGWBi0GBELFIIIMpBgNiCH'
    b'wMIAMBroMH4MWqVwVQKYDYgAxWWB8DAJGglA8BA7g8BBAiGxqseAcHOeZbTNyiSCjYZVJ1WqGVSdMrHrStMz6o2mWvfUXP8U'
    b'blePgNDsHgf6kHgf7MGHIPBQF4PBwF4PA/04KZgGUA4D4PAwIYOBCBgRQVXSwGLAcCCVAi8BwBgggywMpLDpIEBoDbYMB8SU'
    b'8ZBBEIdjwRh4CnLmCzQUfwhAcZHgHQYcKmP+tEFWWsMak2Jvs7fFyfSy6YGVYMAcCkEZJ9kuxhTo+EpLqhMq40lTj9pJ8Az+'
    b'A3C72iSPGmfpdHKVIlUeo5CAXeUsmMHgIH8FCPQQi8S2ADGsA9gls+aH4MH1ojVWwJA8CClLhJV6OmS3S4c9SeBxclYa0eh4'
    b'PS3YqBZvAACxGUFWDNA8HAWjwHiP/MHi/+8AtRgzQPBwFo8B4j/zB4v/vALYXUHApx6Dw//n8HB2LR0HgIJcHg4DdIDw8BWC'
    b'kB4uAXFrGMAqthiDAgg8JARg8R/1g+ZAKiSYRRkE7GMBg2PJBFGQTqDAeB4T/hB4iAVB8z/vfwAAAbZTwIhSZcqVeUdha8fi'
    b'XFQH/geEYCaMRx22fv/1X9T/us5BCGQMAeDwH+KDwH+ODBDB4D+/BggiWDUGoQwDaAdRJBh+PwQAaCSDD8IYII+BlSoGoB6o'
    b'v8EISC4vVeLveLhKLi5UPR9B80PIJSjHgwlAxcDBCCEDCUPghKghKi718AcqEoIJeXCV4IQMB8vLvD6QSx/FW0v+pBQ2VWr1'
    b'UPfiOCGrAI0AALE7AAABtlWAiFPd8Dw8Hxdqse2qYIyjL7OWL9nK4ntQciGSTUdFheJI/pf8u8qxUPlUVf+DcEgDtglDz6oD'
    b'+Ah4B+ghrWekqzi6e/OKWy//1Yi8g9hd7vVQG1IHG6XDvQY5vwAAsTsAAAG2V8CIVfw+BQ/n1asuHmWApVVvU0qZB1o79WoU'
    b'0efUznWt53hj9Ev2QSPCR4D+T9EkeBDrReO+xWqEif/AOSVTQZnCaTfbOWl+X1vgZrxcoHs8o/Ol6kGZUgyYGaAL3wAAsTsA'
    b'AAG2WYCIVdAmS1rBCOj8SqPB/uqOfilRblqrJVDOVhpEdBQjoIVL1Q7L8H9A8zR56X0A4p+B1TgGtHQ6HuWOLvq/+8P8ilQq'
    b'U+EeqaOx1yVbzSm9EZo/vwAAsTsAAANqbW9vdgAAAGxtdmhkAAAAAAAAAAAAAAAAAAAD6AAAA+gAAQAAAQAAAAAAAAAAAAAA'
    b'AAEAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgAAApV0cmFr'
    b'AAAAXHRraGQAAAADAAAAAAAAAAAAAAABAAAAAAAAA+gAAAAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAABAAAAAAAA'
    b'AAAAAAAAAABAAAAAAEAAAAAgAAAAAAAkZWR0cwAAABxlbHN0AAAAAAAAAAEAAAPoAAAAAAABAAAAAAINbWRpYQAAACBtZGhk'
    b'AAAAAAAAAAAAAAAAAAAoAAAAKABVxAAAAAAALWhkbHIAAAAAAAAAAHZpZGUAAAAAAAAAAAAAAABWaWRlb0hhbmRsZXIAAAAB'
    b'uG1pbmYAAAAUdm1oZAAAAAEAAAAAAAAAAAAAACRkaW5mAAAAHGRyZWYAAAAAAAAAAQAAAAx1cmwgAAAAAQAAAXhzdGJsAAAA'
    b'7HN0c2QAAAAAAAAAAQAAANxtcDR2AAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAADAAIABIAAAASAAAAAAAAAABE0xhdmM2MS4x'
    b'OS4xMDEgbXBlZzQAAAAAAAAAAAAAAAAAGP//AAAAYmVzZHMAAAAAA4CAgFEAAQAEgICAQyARAAAAAAMNQAAAMMAFgICAMQAA'
    b'AbABAAABtYkTAAABAAAAASAAxPggHYgALQGEBBRDAAABskxhdmM2MS4xOS4xMDEGgICAAQIAAAAQcGFzcAAAAAQAAAADAAAA'
    b'FGJ0cnQAAAAAAAMNQAAAMMAAAAAYc3R0cwAAAAAAAAABAAAABQAACAAAAAAUc3RzcwAAAAAAAAABAAAAAQAAABxzdHNjAAAA'
    b'AAAAAAEAAAABAAAABQAAAAEAAAAoc3RzegAAAAAAAAAAAAAABQAABEMAAACtAAAAZQAAAGYAAABdAAAAFHN0Y28AAAAAAAAA'
    b'AQAAACwAAABhdWR0YQAAAFltZXRhAAAAAAAAACFoZGxyAAAAAAAAAABtZGlyYXBwbAAAAAAAAAAAAAAAACxpbHN0AAAAJKl0'
    b'b28AAAAcZGF0YQAAAAEAAAAATGF2ZjYxLjcuMTAz'
)
EXPECTED = (ExpectedStream(0,'video','mpeg4',Fraction(0),Fraction(1),Fraction(1,100),
                          width=48,height=32,frame_rate=Fraction(5)),)


def materialize_fixture(root:Path)->Path:
    if not isinstance(root,Path) or not root.is_absolute():raise ValueError('Explicit app self-test parent required')
    # Root must be the controller's cooperating app-data namespace. No mkdir of
    # arbitrary parent tree, adoption, global install, or pathname delete fallback.
    if type(DATA) is not bytes or len(DATA)>4096:raise ValueError('Packaged fixture text exceeds bound')
    data=base64.b64decode(DATA,validate=True)
    if len(data)!=SIZE or sha256(data).hexdigest()!=SHA256:raise ValueError('Packaged self-test fixture mismatch')
    directory=Path(tempfile.mkdtemp(prefix='pair-selftest-',dir=root))
    path=directory/'fixture.mp4'
    with path.open('xb') as stream:
        stream.write(data)
        stream.flush()
    return path  # Retain owned tiny fixture; cleanup is a separate ownership gate.
