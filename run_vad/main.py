import soundfile
from .vad import VAD
from .vad_data import VADData, VADState
import json

def load_audio(path):
    audio, sr = soundfile.read(path)

    # Ensure the sample rate is 16kHz
    assert sr == 16000, f"Sample rate must be 16000, got {sr}"

    return audio


def run_vad(audio,
            start_frame_num_thresh=5,
            start_frame_rollback=10,
            end_frame_num_thresh=30,
            vad_unit_name="silero",
            rollback_end_frame=True
            ):
    """
    Run VAD on the given audio.

    Args:
        audio: numpy array with shape (samples, channels)
        start_frame_num_thresh: Start frame number threshold (default: 5)
        start_frame_rollback: Start frame rollback (default: 10)
        end_frame_num_thresh: End frame number threshold (default: 30)
        vad_unit_name: VAD unit to use [webrtcvad, slero] (default: silero)
        rollback_end_frame: whether to rollback the end frame (default: False)

    Returns:
        List of lists of tuples. Each inner list contains the speech segments for a channel.
        Each tuple contains the start and end time of a speech segment.
    """
    vad = VAD(start_frame_num_thresh=start_frame_num_thresh,
              start_frame_rollback=start_frame_rollback,
              end_frame_num_thresh=end_frame_num_thresh,
              vad_unit_name=vad_unit_name)
    vad.reset()

    # Convert to 16-bit PCM
    audio = (audio * 32767).astype("int16")

    results = []

    frame_rate_in_sec = vad.samples_per_frame / vad.sample_rate
    start_offset_in_sec = vad.start_frame_rollback * frame_rate_in_sec
    end_rollback_in_sec = vad.end_frame_num_thresh * frame_rate_in_sec if rollback_end_frame else 0

    for ch in range(audio.shape[1]):
        ch_audio = audio[:, ch]
        ch_results = []
        start_in_sec = -1
        vad.reset()
        for i in range(0, len(ch_audio), vad.samples_per_frame):
            frame = ch_audio[i:i + vad.samples_per_frame].tobytes()
            if len(frame) < vad.actual_frame_size_in_bytes:
                frame = frame.ljust(vad.actual_frame_size_in_bytes, b'\0')
            result = vad.process(frame)
            if result.state == VADState.Started:
                assert start_in_sec < 0, "VADState.Started while in another VADState.Started"
                start_in_sec = i / vad.sample_rate - start_offset_in_sec
                start_in_sec = 0 if start_in_sec < 0 else start_in_sec
                start_in_sec = round(start_in_sec, 3)
            elif result.state == VADState.Ended:
                assert start_in_sec >= 0, "VADState.Ended while not in VADState.Started"
                end_in_sec = i / vad.sample_rate
                end_in_sec = round(end_in_sec - end_rollback_in_sec, 3)
                if end_in_sec - start_in_sec > 0:
                    ch_results.append((start_in_sec, end_in_sec))
                start_in_sec = -1
        if start_in_sec >= 0:
            end_in_sec = len(ch_audio) / vad.sample_rate
            end_in_sec = round(end_in_sec - end_rollback_in_sec, 3)
            if end_in_sec - start_in_sec > 0:
                ch_results.append((start_in_sec, end_in_sec))
            start_in_sec = -1
        results.append(ch_results)
    return results

def main():
    import argparse

    parser = argparse.ArgumentParser("Run VAD on an audio file")

    parser.add_argument("--input", "-i", help="Path to the input audio file", required=True)
    parser.add_argument("--vad_unit", "-u", help="VAD unit to use [webrtcvad, slero] (default: silero)", default="silero")
    parser.add_argument("--start_frame_num_thresh", "-s", help="Start frame number threshold (default: 3)", type=int, default=5)
    parser.add_argument("--start_frame_rollback", "-r", help="Start frame rollback (default: 10)", type=int, default=10)
    parser.add_argument("--end_frame_num_thresh", "-e", help="End frame number threshold (default: 30)", type=int, default=30)
    parser.add_argument("--vad_unit_options", help="VAD unit options", type=str, default="silero")
    parser.add_argument("--rollback_end_frame", help="Whether end frames are rolled back (default: True)", type=bool, default=True)
    parser.add_argument("output", help="Path to the output JSON file")

    args = parser.parse_args()

    audio = load_audio(args.input)
    results = run_vad(audio,
                      start_frame_num_thresh=args.start_frame_num_thresh,
                      start_frame_rollback=args.start_frame_rollback,
                      end_frame_num_thresh=args.end_frame_num_thresh,
                      vad_unit_name=args.vad_unit,
                      rollback_end_frame=args.rollback_end_frame)
    json.dump(results, open(args.output, "w"))

if __name__ == "__main__":
    main()
