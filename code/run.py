import sys
import threading
import os
import console_app
import torcs_client
import race_engineer
import procedural_commentary
import shared


HELP = f"Usage: run.py [args ...]\n\t--help: Display this message\n\t--chatbot: Run with the Race Engineer/chatbot\n\t--commentary: Run with the live procedural commentary\n\t--telemetry: Save lap & track data from the race"

drive_thread = threading.Thread(target=torcs_client.torcs_client_thread)
chatbot_thread = threading.Thread(target=race_engineer.race_engineer_thread)
commentary_thread = threading.Thread(target=procedural_commentary.procedural_commentary_thread)


def main():
  app = console_app.IBMTorcsApp(shared.run_chatbot)

  drive_thread.start()
  
  if shared.run_chatbot:
    chatbot_thread.start()
  
  if shared.run_commentary:
    commentary_thread.start()

  app.run()

  os._exit(0)


if __name__ == "__main__":
  argv = sys.argv[1:]

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
  
  if len(argv) != 0:
    print(HELP)
  else:
    main()