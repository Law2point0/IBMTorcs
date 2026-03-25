import sys
import torcs_client
import race_engineer
import threading

run_chatbot = False
run_commentary = False

driving_thread = threading.Thread(target=torcs_client.drive_loop)

HELP = "Usage: python run.py [args ...]\n\t--help: Display this message\n\t--chatbot: Run with the Race Engineer/chatbot\n\t--commentary: Run with the live procedural commentary\n"


def main():
  if not run_commentary and not run_chatbot:
    torcs_client.drive_loop()
  else:
    try:
      driving_thread.start()

      if run_chatbot:
        while True:
          prompt = input('Prompt: ')
          data = torcs_client.telemetry
          race_engineer.prompt_model(prompt, data)
    except KeyboardInterrupt:
      print('Exiting...')

      driving_thread.join()


if __name__ == '__main__':
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