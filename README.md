# 🎧 HaramMute  
**Real-time Music filtring using AI**

![cover](assets/cover.png)

HaramMute is a lightweight desktop application that performs **real-timeMusic filtring** using **AI**.  
It runs quietly in the **system tray**, processes live audio streams, and is designed to be packaged as a **standalone executable** using PyInstaller.

The app is built with **PyQt6**, **sounddevice**, and **PyTorch + torchaudio**, with CUDA acceleration when available.

---
## 🧠 How it works

1. Audio is captured from a **virtual input device** (VB-Cable).
2. Audio is buffered and passed to AI model in small blocks.
3. Only the **vocals output** is extracted.
4. Processed audio is streamed to a selected **output device**.
5. Heavy work (model loading & inference) runs outside the UI thread.

---
## 🚀 Getting Started

This section covers the **quickest ways to start using HaramMute on Windows**, whether you prefer a **ready-to-use executable** or running the app **from source**.


### 🪟 Windows

Before you begin, make sure you have:  **VB-Audio Virtual Cable** insatalled.

Download VB-Cable if you don’t have it:  
👉 https://vb-audio.com/Cable/
---

### 📦 Option 1: Download Pre-Built Application (Recommended)

This is the **fastest way** to get started.  
you can go the the [Releases](https://github.com/AhmedGhazale/HaramMute/releases) page. or download the suitable version here:
* **cpu version** : [Here](https://drive.google.com/file/d/181IzkqJ5JZ43DNLj9uik6N5hjEUjwTtg/view?usp=sharing)
*  **cuda version** : [Here](https://drive.google.com/file/d/10q4QrfysxY_IyCx8zr0Z3iHJuDUUVEj6/view?usp=sharing)
### 🧪 Option 2: Run From Source (Developers / Advanced Users)
Choose this option if you want to:
* Modify the code
* Experiment with audio parameters
* Build your own executable

#### 1️⃣ Clone the repository
```bash
git clone https://github.com/AhmedGhazale/HaramMute
cd HaramMute
```
#### 2️⃣ Create a virtual environment(Optional)
```bash
python -m venv .venv
.venv\Scripts\activate
```

#### 3️⃣ Install dependencies
* install pytorch (refere to https://pytorch.org/)
* then install other requirements:
```bash
pip install -r requirements.txt
```
#### 4️⃣ Run the application
Always run the app as a module:
```bash
python -m app.main
```

#### 🛠 Optional: Build Your Own Executable

If you want to package the app yourself:
```bash
pyinstaller build.spec
```
The executable will be created in: $root/dist/HaramMute.exe

---   
## ▶️How to Run HaramMute

HaramMute is designed to run quietly in the background as a **system tray application** while processing audio in real time.

---

### 1️⃣ Launch the Application

- Start the application by running **HaramMute.exe** (pre-built version)  
  **or**
- From source:
  ```bash
  python -m app.main
On launch, the window will appear and the app will also place an icon in the system tray.

### 2️⃣ Wait for the Model to Load
The AI loads automatically in the background.
On the first run, the model may need to be downloaded and cached.
During this time:
* Logs will show model loading status
* The Start Service button is disabled

Once the model is ready, the Start Service button becomes clickable.

### 3️⃣ Select an Output Device
Choose the desired output audio device from the dropdown menu.
The input device is fixed and must be set externally (e.g. VB-Cable).

### 4️⃣ Set VB-Cable as the System Output Device (Windows)

Before starting the service, you must configure **Windows system audio** to route sound through VB-Cable:

1. Right-click the **speaker icon** in the Windows taskbar
2. Open **Sound settings**
3. Under **Output**, select: **CABLE Input (VB-Audio Virtual Cable)**

This step ensures that all system audio is routed into HaramMute through the virtual cable and can be processed by the AI model.

> ⚠️ If this step is skipped, HaramMute will not receive any audio to process.
### 5️⃣ Adjust Audio Parameters (Optional)
You may adjust these before starting the service:
* Block Size – Controls latency vs stability.
* Max Buffer Size – Controls temporal context.
* Back Offset – Compensates for model lookahead.

Default values are recommended for most systems.

### 6️⃣ Understand Performance Metrics
The UI displays real-time performance information to help you evaluate system stability:
* **Processing Time (ms)**: Time the Demucs model takes to process one audio block.

* **Block Time (ms)**:Duration of the current audio block, calculated as:
```
Block Time = Block Size / Sample Rate × 1000
```
* **Real-Time Factor (RTF)**: Indicates whether processing can keep up with live audio:

```
RTF = Processing Time / Block Time
```
| RTF Value | Meaning |
|----------|---------|
| `< 0.7` | Safe |
| `0.7 – 0.9` | Borderline |
| `≥ 1.0` | Audio dropouts |

**IMPORTANT** : If the RTF reaches or exceeds 1.0, increase the block size or reduce system load.
### 7️⃣ Start the Service
Click Start Service to begin real-time audio processing.
The app will start capturing audio, processing it with ai, and streaming the result to the output device.
Performance metrics (processing time, block time, RTF) update live in the UI.

### 8️⃣ Run in the Background
Closing the window will minimize the app to the system tray
The service continues running until you stop it or exit the app from the tray menu

### 9️⃣ Stop or Exit
Click Stop Service to stop audio processing
Use the system tray menu to exit the application completely

---
## ❗Troubleshooting

### 🔇 No Audio Output
- Make sure the correct **output device** is selected
- Verify that the **input device** (e.g. VB-Cable) is set correctly at the system level
- Ensure the service is started and the model has finished loading

---

### 🎧 Audio Glitches or Dropouts
- Check the **Real-Time Factor (RTF)**  
  - If `RTF ≥ 1.0`, the system cannot keep up in real time
- Increase the **Block Size**
- Reduce GPU load by closing other applications
- Ensure CUDA is being used if available

---

### 🧲 Application Closes When Window Is Closed
- This is expected behavior  
- The app minimizes to the **system tray**
- Check the tray area for the application icon

---

### 🐌 High Latency
- Reduce **Block Size** (if RTF allows)
- Reduce **Back Offset**
- Ensure audio sample rate matches system settings

---

### 🚫 Start Service Button Is Disabled
- The model is still loading
- On first run, the model may be downloading
- Wait until the log shows that the model is ready

---

### 🧠 Model Loading Takes a Long Time
- First-time model download can take several minutes
- Model weights are cached locally after the first run
- Subsequent launches should load much faster

