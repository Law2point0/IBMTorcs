import queue

chatbot_queue = queue.Queue()
chatbot_request_queue = queue.Queue()
commentary_queue = queue.Queue()

server_data = dict()

run_chatbot, run_commentary, run_telemetry, run_rb = False, False, False, False