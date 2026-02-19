import sys
import torcs_jm_par
import race_engineer
import threading

run_chatbot = True
run_commentary = False

driving_thread = threading.Thread(target=torcs_jm_par.drive_loop)

HELP = "Usage: python run.py [args ...]\n\t--help: Display this message\n\t--no-chatbot: Run without the Race Engineer/chatbot\n\t--no-commentary: Run without the live procedural commentary\n\t--only-racebot: Only run the racebot"


def main():
  if not run_commentary and not run_chatbot:
    torcs_jm_par.drive_loop()
  else:
    try:
      print('Press Ctrl+C to stop the program after the race has finished.')

      driving_thread.start()

      if run_chatbot:
        while True:
          prompt = input('Prompt: ')
          data = torcs_jm_par.telemetry
          race_engineer.prompt_model(prompt, data)
    except KeyboardInterrupt:
      print('Exiting...')

      driving_thread.join()


if __name__ == '__main__':
  argv = sys.argv
  argv.remove('run.py')

  if '--no-chatbot' in argv:
    argv.remove('--no-chatbot')
    run_chatbot = False
  if '--no-commentary' in argv:
    argv.remove('--no-commentary')
    run_commentary = False
  if '--only-racebot' in argv:
    argv.remove('--only-racebot')
    run_chatbot = False
    run_commentary = False
  
  if len(argv) != 0:
    print(HELP)
  else:
    main()