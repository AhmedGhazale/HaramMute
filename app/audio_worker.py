import numpy as np
import torch
from torchaudio.pipelines import HDEMUCS_HIGH_MUSDB_PLUS
from time import time
from PyQt6.QtCore import  pyqtSignal, QObject
import sounddevice as sd

HARDCODED_INPUT = "CABLE Output (VB-Audio Virtual , MME"

class AudioWorker(QObject):
    """Handles the heavy lifting: Model loading and Audio Stream."""
    finished = pyqtSignal()
    log_signal = pyqtSignal(str)
    timing_signal = pyqtSignal(float, float)
    model_loaded = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.stream = None
        self.is_running = False
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = None

        # Current Config
        self.block_size = 4048
        self.max_buffer_size = 16000
        self.back = 1024
        self.output_device_idx = None
        self.buffer = None

    def load_model(self):
        self.log_signal.emit(f"Loading model on {self.device} (please don't start until the model is ready)")
        self.log_signal.emit(f"if this is first time opening the app the model will be downloaded (!300 MB)")

        bundle = HDEMUCS_HIGH_MUSDB_PLUS
        self.model = bundle.get_model().to(self.device).eval()
        self.log_signal.emit("Model loaded successfully.(you can now start the service)")
        self.model_loaded.emit()  # ✅ SIGNAL HERE

    def extract_vocals(self, chunk):
        # Update buffer
        self.buffer = np.concatenate([self.buffer, chunk], axis=0)
        self.buffer = self.buffer[-self.max_buffer_size:, :]

        x = torch.from_numpy(self.buffer.T).unsqueeze(0).to(self.device)

        with torch.no_grad():
            s = time()
            out = self.model(x)
            e = time()
            # Optionally log latency (careful with spamming)
            # self.log_signal.emit(f"Infer: {(e-s)*1000:.2f}ms")
            processing_ms = (e - s) * 1000
            block_ms = (self.block_size / 41000) * 1000
            self.timing_signal.emit(processing_ms, block_ms)

        vocals = out[0][3].cpu().numpy().T.astype(np.float32)
        # Apply the BACK offset logic
        vocals = vocals[-self.block_size - self.back: -self.back if self.back > 0 else None, :]
        return vocals

    def audio_callback(self, indata, outdata, frames, time_info, status):
        if status:
            self.log_signal.emit(f"Status Error: {status}")
        try:
            vocals = self.extract_vocals(indata)
            if vocals.shape[0] < frames:
                pad = np.zeros((frames - vocals.shape[0], 2), dtype=np.float32)
                vocals = np.concatenate([vocals, pad], axis=0)
            else:
                vocals = vocals[:frames]
            outdata[:] = vocals
        except Exception as e:
            outdata[:] = np.zeros_like(indata)

    def start_stream(self):
        self.buffer = np.zeros([self.max_buffer_size, 2]).astype(np.float32)
        try:
            self.stream = sd.Stream(
                device=(HARDCODED_INPUT, self.output_device_idx),
                samplerate=44100,
                channels=2,
                dtype="float32",
                blocksize=self.block_size,
                callback=self.audio_callback
            )
            self.stream.start()
            self.is_running = True
            self.log_signal.emit("Stream started.")
        except Exception as e:
            self.log_signal.emit(f"Start Error: {e}")

    def stop_stream(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
        self.is_running = False
        self.log_signal.emit("Stream stopped.")
