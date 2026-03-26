import sys
import console_app
import threading
import torcs_client
import race_engineer
import os

run_chatbot, run_commentary = False, False

HELP = f"Usage: python3 run.py [args ...]\n\t--help: Display this message\n\t--chatbot: Run with the Race Engineer/chatbot\n\t--commentary: Run with the live procedural commentary\n"

drive_thread = threading.Thread(target=torcs_client.drive_loop)
chatbot_thread = threading.Thread(target=race_engineer.race_engineer_thread)
#commentary_thread = 

def main():
  app = console_app.IBMTorcsApp(run_chatbot)

  drive_thread.start()
  chatbot_thread.start()

  app.run()

  os._exit(0)


if __name__ == "__main__":
  argv = sys.argv[1:]

  if '--chatbot' in argv:
    argv.remove('--chatbot')
    run_chatbot = True
  if '--commentary' in argv:
    argv.remove('--commentary')
    run_commentary = True
  
  if len(argv) != 0:
    print(HELP)
  else:
    main()