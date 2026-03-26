from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual import events
import queue
import datetime
from shared import chatbot_queue, chatbot_request_queue, commentary_queue, SECRET_QUIT_PHRASE


def get_formatted_timestamp():
  timestamp = datetime.datetime.now().strftime("%H:%M:%S")
  return f"[dim]{timestamp}[/dim]"


class IBMTorcsApp(App):
  def compose(self) -> ComposeResult:
    self.messages = VerticalScroll(id="messages")
    yield self.messages

    self.input = Input(placeholder="Prompt the race engineer... (type 'quit' to quit)")
    yield self.input

  async def on_mount(self):
    self.input.focus()
    self.set_interval(0.1, self.process_queues)

  async def add_message(self, text):
    await self.messages.mount(Static(text))
    self.messages.scroll_end()

  async def process_queues(self):
    while not chatbot_queue.empty():
      msg = chatbot_queue.get_nowait()
      await self.add_message(f"{get_formatted_timestamp()} [cyan]Race Engineer[/cyan]: {msg}")

    while not commentary_queue.empty():
      msg = commentary_queue.get_nowait()
      await self.add_message(f"{get_formatted_timestamp()} [magenta]Live Commentary[/magenta]: {msg}")

  async def on_input_submitted(self, event: Input.Submitted):
    text = event.value
  
    if text == "quit":
      chatbot_request_queue.put(SECRET_QUIT_PHRASE)
      await self.add_message(f"{get_formatted_timestamp()}  > {text}\nQuiting...")
      await self.action_quit()
      return
    elif text != "":
      await self.add_message(f"{get_formatted_timestamp()}  > {text}")
      event.input.value = ""
      chatbot_request_queue.put(text)


"""

import threading
import race_engineer

if __name__ == "__main__":
  chatbot_thread = threading.Thread(target=race_engineer.race_engineer_thread)
  chatbot_thread.start()

  app = IBMTorcsApp()
  app.run() # Blocking btw
"""