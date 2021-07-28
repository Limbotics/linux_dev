import rpyc
from rpyc.utils.server import ThreadedServer
import threading
import time

class MyService(rpyc.Service):

    def __init__(self):
        self.channel_0 = 0
        self.channel_1 = 0

        print("init completed")

    # My service
    def exposed_echo(self, text):
        print(text)
        
    def exposed_channel_0_value(self):
        return self.channel_0

    def exposed_channel_1_value(self):
        return self.channel_1       

# def main_thread():
#     while(True):
#         print("Hello! Press 1 to send a down pulse, 2 for a down hold (1 second), 3 for up hold (1 second)")
#         ans = input()
#         if ans == 1:
#             channel_0 = 10000
#             time.sleep(0.3)
#             channel_0 = 0

if __name__ == "__main__":

    # UI_thread = threading.Thread(main_thread, args=())
    # UI_thread.start()

    server = ThreadedServer(MyService, port = 18812)
    server.start()

    