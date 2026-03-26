import queue

SECRET_QUIT_PHRASE = "__QUIT__"

chatbot_queue = queue.Queue()
chatbot_request_queue = queue.Queue()
commentary_queue = queue.Queue()

server_data = dict()