import time
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FlowSegment:
    start: float
    end: Optional[float] = None
    break_reason: Optional[str] = None


@dataclass
class SessionAnalytics:
    start_time: float
    end_time: Optional[float] = None
    flow_segments: List[FlowSegment] = field(default_factory=list)
    break_events: List[str] = field(default_factory=list)

    def start_flow(self, now: float):
        # avoid starting twice
        if self.flow_segments and self.flow_segments[-1].end is None:
            return
        self.flow_segments.append(FlowSegment(start=now))

    def end_flow(self, now: float, reason: str):
        if not self.flow_segments:
            return
        seg = self.flow_segments[-1]
        if seg.end is None:
            seg.end = now
            seg.break_reason = reason
            self.break_events.append(reason)

    def finish_session(self):
        self.end_time = time.time()
