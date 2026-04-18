# Building

## Prerequisites
 - Python 3.8+
 - [Ollama](https://ollama.com/download) (For running granite models locally)
 - IBM's TORCS fork or [TORCS](https://sourceforge.net/projects/torcs/) however some code is designed to work with the IBM F1 car.

## Installation
1. Install dependencies with pip by running `pip install -r requirements` in the project root. You may need to prefix this with `python -m ` (Windows) or `python3 -m ` (MacOS/Linux) if pip isn't a recognized command. You can optionally create a virtual environment if you don't want to install these dependencies globally.
2. (Recommended) Download Granite Micro 4.0 through Ollama by running `ollama pull hf.co/ibm-granite/granite-4.0-micro-GGUF:Q4_K_M'`. This is so it doesn't download the model on first prompt instead.

## Running
1. Ensure Ollama's background task is running either by opening and closing it or checking if it's running in system tray.
2. Open a terminal in the `code/` directory.
3. Run `python run.py --help` on Windows or `python3 run.py --help` on MacOS or Linux.