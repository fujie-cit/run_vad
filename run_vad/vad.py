from typing import List, Dict, Tuple
from enum import Enum
from .vad_unit.base import VADUnitBase
from .vad_unit.silero import VADUnitSilero
from .vad_data import VADState, VADData
from .vad_unit.webrtcvad import VADUnitWebRTC

AVAILABLE_VAD_UNITS: Dict[str, VADUnitBase] = {
    'silero': VADUnitSilero,
    'webrtcvad': VADUnitWebRTC,
}

class VAD:
    def __init__(self,
        sample_rate: int = 16000,
        sample_width: int = 2,
        samples_per_frame: int = 160,
        start_frame_num_thresh: int = 5,
        start_frame_rollback: int = 10,
        end_frame_num_thresh: int = 30,
        vad_unit_name: str = 'webrtcvad',
        vad_unit_params: dict = {},):

        self.sample_rate = sample_rate
        self.sample_width = sample_width
        self.samples_per_frame = samples_per_frame
        self.start_frame_num_thresh = start_frame_num_thresh
        self.start_frame_rollback = start_frame_rollback
        self.end_frame_num_thresh = end_frame_num_thresh

        self.vad_unit = AVAILABLE_VAD_UNITS[vad_unit_name](**vad_unit_params)

        # VAD Unit とのパラメータの整合性をチェック
        # サンプリング周波数とサンプル幅は一致していなければいけない
        assert self.sample_rate == self.vad_unit.sample_rate, f"Sample rate mismatch: {self.sample_rate} != {self.vad_unit.sample_rate}"
        assert self.sample_width == self.vad_unit.sample_width, f"Sample width mismatch: {self.sample_width} != {self.vad_unit.sample_width}"
        # フレームサイズは VAD Unit のものの方が大きく，整数倍である必要がある
        assert self.samples_per_frame <= self.vad_unit.samples_per_frame, f"Samples per frame mismatch: {self.samples_per_frame} > {self.vad_unit.samples_per_frame}"
        assert self.vad_unit.samples_per_frame % self.samples_per_frame == 0, f"Samples per frame is not a multiple of {self.samples_per_frame}"

        # フレームサイズ（バイト単位）
        self.actual_frame_size_in_bytes = self.sample_width * self.samples_per_frame

        # VAD Unitに与えるフレーム長（こちらのフレーム長基準）
        self.vad_unit_frame_ratio = self.vad_unit.samples_per_frame // self.samples_per_frame
        # VAD Unitに与えるフレームのためのバッファ
        self.vad_unit_frame_buffer: List[bytes] = []

        # 1フレーム前の VAD Unit の結果
        self.prev_vad_unit_result = False
        # VAD Unit の結果のカウント
        # 非音声区間時はTrueのカウント，音声区間時はFalseのカウント
        self.vad_unit_result_count = 0
        # VAD の状態
        self.vad_state = VADState.Idle
        # 返却値のためのバッファ
        self.vad_result_buffer: List[bytes] = []

    def reset(self):
        """VAD の状態をリセットする."""
        self.vad_unit_frame_buffer.clear()
        self.prev_vad_unit_result = False
        self.vad_unit_result_count = 0
        self.vad_state = VADState.Idle
        self.vad_result_buffer.clear()

    def process(self, audio_data: bytes) -> VADData:
        """音声データを処理し，VAD の状態を返す."""
        assert len(audio_data) == self.actual_frame_size_in_bytes, f"Data size is invalid: {len(audio_data)} != {self.actual_frame_size_in_bytes}"

        # フレームをバッファに追加
        self.vad_unit_frame_buffer.append(audio_data)
        # バッファがフレーム数に達したら VAD Unit に処理を依頼
        # その後，バッファをクリア
        if len(self.vad_unit_frame_buffer) == self.vad_unit_frame_ratio:
            vad_result = self.vad_unit.process(b''.join(self.vad_unit_frame_buffer))
            self.vad_unit_frame_buffer.clear()
        else:
            vad_result = self.prev_vad_unit_result
        self.prev_vad_unit_result = vad_result

        self.vad_result_buffer.append(audio_data)
        if len(self.vad_result_buffer) > self.start_frame_rollback:
            self.vad_result_buffer.pop(0)

        if self.vad_state == VADState.Idle:
            if vad_result:
                self.vad_unit_result_count += 1
            else:
                self.vad_unit_result_count = 0
            if self.vad_unit_result_count >= self.start_frame_num_thresh:
                return_value = VADData(VADState.Started, self.vad_result_buffer.copy())
                self.vad_result_buffer.clear()
                self.vad_unit_count = 0
                self.vad_state = VADState.Continue
            else:
                return_value = VADData(VADState.Idle, [])
        elif self.vad_state == VADState.Continue:
            if vad_result:
                self.vad_unit_result_count = 0
            else:
                self.vad_unit_result_count += 1
            if self.vad_unit_result_count >= self.end_frame_num_thresh:
                return_value = VADData(VADState.Ended, self.vad_result_buffer.copy())
                self.vad_result_buffer.clear()
                self.vad_unit_count = 0
                self.vad_state = VADState.Idle
            else:
                return_value = VADData(VADState.Continue, self.vad_result_buffer.copy())
                self.vad_result_buffer.clear()
        else:
            raise ValueError(f"Invalid VAD state: {self.vad_state}")
        return return_value

