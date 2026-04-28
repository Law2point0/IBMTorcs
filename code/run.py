import sys
import os
import threading
from training import train
from runtime import console_app
from runtime import torcs_client
from runtime import inference_client
from runtime import race_engineer
from runtime import procedural_commentary
from runtime import shared

sys.path.insert(0, os.path.dirname(__file__))

HELP = f"Usage: run.py [args ...]\n\t--help: Display this message\n\t--rb: Run with the Rules Based Client (More Consistent) \n\t--chatbot: Run with the Race Engineer/chatbot\n\t--commentary: Run with the live procedural commentary\n\t--telemetry: Save lap & track data from the race\n\t--train: Only run the reinforcement learning mode"

drive_thread = threading.Thread(target=torcs_client.torcs_client_thread)
chatbot_thread = threading.Thread(target=race_engineer.race_engineer_thread)
commentary_thread = threading.Thread(target=procedural_commentary.procedural_commentary_thread)


def main():
  app = console_app.IBMTorcsApp(shared.run_chatbot)

  if shared.run_rb:
    drive_thread = threading.Thread(target=torcs_client.torcs_client_thread)
  else:
    drive_thread = threading.Thread(target=inference_client.inference_client_thread)

  drive_thread.start()
  
  if shared.run_chatbot:
    chatbot_thread.start()
  
  if shared.run_commentary:
    commentary_thread.start()

  app.run()

  os._exit(0)


if __name__ == "__main__":
  argv = sys.argv[1:]

  if '--rb' in argv:
    argv.remove('--rb')
    shared.run_rb = True
  if '--chatbot' in argv:
    argv.remove('--chatbot')
    shared.run_chatbot = True
  if '--commentary' in argv:
    argv.remove('--commentary')
    shared.run_commentary = True
  if '--telemetry' in argv:
    argv.remove('--telemetry')
    shared.run_telemetry = True
    os.makedirs("telemetry", exist_ok=True)
  if '--train' in argv:
    train.train()
  
  if len(argv) != 0:
    print(HELP)
  else:
    main()
