import sys
from console_app import IBMTorcsApp
import threading
from torcs_client import drive_loop

run_chatbot, run_commentary = False, False

HELP = "Usage: python run.py [args ...]\n\t--help: Display this message\n\t--chatbot: Run with the Race Engineer/chatbot\n\t--commentary: Run with the live procedural commentary\n"

drive_thread = threading.Thread(target=drive_loop)
#commentary_thread = 

def main():
  pass


if __name__ == "__main__":
  argv = sys.argv
  argv.remove('run.py')

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