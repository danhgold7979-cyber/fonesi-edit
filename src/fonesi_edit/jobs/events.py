"""Allowlisted diagnostics: no caller text, exception repr or raw tool output."""
from dataclasses import dataclass
from enum import Enum
import json


class EventCode(str, Enum):
    QUEUE_PAUSED = 'QUEUE_PAUSED'
    QUEUE_RESUMED = 'QUEUE_RESUMED'
    CANCEL_REQUESTED = 'CANCEL_REQUESTED'
    CANCELED_BEFORE_RUN = 'CANCELED_BEFORE_RUN'
    PROCESS_EXIT = 'PROCESS_EXIT'
    PROCESS_TIMEOUT = 'PROCESS_TIMEOUT'
    RETIREMENT_UNKNOWN = 'RETIREMENT_UNKNOWN'
    VALIDATION_REJECTED = 'VALIDATION_REJECTED'
    INPUT_UNAVAILABLE = 'INPUT_UNAVAILABLE'
    OUTPUT_CONFLICT = 'OUTPUT_CONFLICT'
    STORAGE_FAILURE = 'STORAGE_FAILURE'
    CONFIGURATION_REQUIRED = 'CONFIGURATION_REQUIRED'
    PROVIDER_OUTCOME_UNKNOWN = 'PROVIDER_OUTCOME_UNKNOWN'


class EventStage(str, Enum):
    QUEUE = 'QUEUE'
    PROBE = 'PROBE'
    DECODE = 'DECODE'
    PUBLISH = 'PUBLISH'
    DOWNLOAD = 'DOWNLOAD'
    TRANSLATE = 'TRANSLATE'


@dataclass(frozen=True)
class Event:
    code: EventCode
    stage: EventStage
    exit_code: int | None = None

    def __post_init__(self):
        if type(self.code) is not EventCode or type(self.stage) is not EventStage:
            raise ValueError('Enumerated diagnostic code/stage required')
        if self.exit_code is not None and (self.code is not EventCode.PROCESS_EXIT or
            type(self.exit_code) is not int or not -(2**31) <= self.exit_code < 2**32):
            raise ValueError('Bounded process exit code required')
        if self.code is EventCode.PROCESS_EXIT and self.exit_code is None:
            raise ValueError('Process exit code missing')
        if self.code in {EventCode.QUEUE_PAUSED, EventCode.QUEUE_RESUMED,
                         EventCode.CANCEL_REQUESTED, EventCode.CANCELED_BEFORE_RUN} and self.stage is not EventStage.QUEUE:
            raise ValueError('Queue event stage mismatch')

    def canonical(self):
        return json.dumps({'code':self.code.value,'stage':self.stage.value,'exit_code':self.exit_code},
                          sort_keys=True,separators=(',',':'),allow_nan=False)

    @classmethod
    def parse(cls, text):
        if type(text) is not str or len(text)>256:
            raise ValueError('Bounded diagnostic required')
        def unique(pairs):
            result={}
            for key,value in pairs:
                if key in result:raise ValueError('Duplicate diagnostic key')
                result[key]=value
            return result
        obj=json.loads(text,object_pairs_hook=unique)
        if type(obj) is not dict or set(obj)!={'code','stage','exit_code'}:
            raise ValueError('Exact diagnostic fields required')
        result=cls(EventCode(obj['code']),EventStage(obj['stage']),obj['exit_code'])
        if result.canonical()!=text:raise ValueError('Canonical diagnostic required')
        return result


LABELS = {
    EventCode.QUEUE_PAUSED: ('information','Đã tạm dừng tác vụ chờ'),
    EventCode.QUEUE_RESUMED: ('information','Đã tiếp tục tác vụ chờ'),
    EventCode.CANCEL_REQUESTED: ('information','Đã ghi yêu cầu hủy; chưa xác nhận dừng'),
    EventCode.CANCELED_BEFORE_RUN: ('canceled','Đã hủy tác vụ chưa chạy'),
    EventCode.PROCESS_EXIT: ('process_failure','Tiến trình kết thúc với mã lỗi'),
    EventCode.PROCESS_TIMEOUT: ('process_failure','Tiến trình vượt thời gian cho phép'),
    EventCode.RETIREMENT_UNKNOWN: ('unknown_outcome','Chưa xác nhận tiến trình đã dừng'),
    EventCode.VALIDATION_REJECTED: ('invalid_output','Đầu ra không đạt kiểm tra'),
    EventCode.INPUT_UNAVAILABLE: ('configuration','Nguồn đầu vào chưa khả dụng'),
    EventCode.OUTPUT_CONFLICT: ('configuration','Tên đầu ra đã tồn tại hoặc thay đổi'),
    EventCode.STORAGE_FAILURE: ('storage','Không xác nhận được thao tác lưu trữ'),
    EventCode.CONFIGURATION_REQUIRED: ('configuration','Cần kiểm tra cấu hình trước khi chạy'),
    EventCode.PROVIDER_OUTCOME_UNKNOWN: ('unknown_outcome','Chưa xác định kết quả yêu cầu dịch vụ'),
}


def describe(event):
    if type(event) is not Event:raise ValueError('Typed event required')
    category,label=LABELS[event.code]
    return category, label+(f' ({event.exit_code})' if event.exit_code is not None else '')
