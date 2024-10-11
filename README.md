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

You can run the VAD on an audio file by running the following command:
```bash
run_vad -i input.wav output.json
```

The results will be saved in a JSON file.
It's simply like:
```json
[
    # the start and end time of the first channel.
    [
        [0.0, 0.3], [1.2, 1.5], ...  
    ],
    # the start and end time of the second channel.
    [
        [0.4, 0.5], [1.6, 1.8], ...
    ]
]
```
The values are in seconds.

### Options

You can choose the algorithm to use by specifying the `--vad_unit` or `-u` option.
The default is `silero`.

The following algorithms are available:
- `silero`: [Silero VAD](https://github.com/snakers4/silero-vad) (default)
- `webrtcvad`: [py-webrtcvad](https://github.com/wiseman/py-webrtcvad)

Currently, you cannot specify the detailed parameters for each algorithm.


