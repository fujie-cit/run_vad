# run_vad
Running Voice Activity Detection on an audio file.

## Requirements

- Python 3.6 or later
- numpy
- torch
- torchaudio
- webrtcvad

## Installation

from GitHub:

```bash
pip install git+https://github.com/fujie-cit/run_vad.git
```

from local repository:

```bash
pip install -e .
```

## Usage

### As a command line tool

You can run the VAD on an audio file by running the following command:
```bash
run_vad -i input.wav output.json
```

The results will be saved in a JSON file.
It's simply like:
```json
[
    [[0.0, 0.3], [1.2, 1.5], ...],
    [[0.4, 0.5], [1.6, 1.8], ...],
]
```

The JSON file contains a list of lists.
Each list corresponds to a channel in the audio file.
Each element in the list is a list of two numbers, which are the start and end times of the detected speech segment in seconds.

The format of this JSON file is compatible with the [VAP](https://github.com/ErikEkstedt/VAP/tree/main/vap/data) data.

#### Options

You can choose the algorithm to use by specifying the `--vad_unit` or `-u` option.
The default is `silero`.

The following algorithms are available:
- `silero`: [Silero VAD](https://github.com/snakers4/silero-vad) (default)
- `webrtcvad`: [py-webrtcvad](https://github.com/wiseman/py-webrtcvad)

Currently, you cannot specify the detailed parameters for each algorithm.

### As a Python module

You can also use the VAD as a Python module.

```python
from run_vad import run_vad
import soundfile as sf

audio, sr = sf.read('input.wav')

results = run_vad(audio, sr)
```

#### Parameters

- `audio`: numpy.ndarray
  - The audio data.
  - The shape should be `(n_samples, n_channels)`.
- start_frame_num_thresh
  - Start frame number threshold (default: 5)
- start_frame_rollback
  - Start frame rollback (default: 10)
- end_frame_num_thresh
  - End frame number threshold (default: 30)
- vad_unit_name
  - The name of VAD algorithm to use, webrtcvad or slero (default: silero)

