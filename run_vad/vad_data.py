from enum import Enum
from dataclasses import dataclass, field
from typing import List

class VADState(Enum):
    """VAD の状態を表す列挙型."""
    Idle = 0,     """VAD が音声を検出していない状態."""
    Started = 1,  """VAD が音声を検出し始めた状態."""
    Ended = 2,    """VAD が音声の終了を検出した状態."""
    Continue = 3, """VAD が音声を検出し続けている状態."""

@dataclass
class VADData:
    state: VADState = VADState.Idle
    data: List[bytes] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"VADData(state={self.state.name}, packets=[{len(self.data)}frames])"
