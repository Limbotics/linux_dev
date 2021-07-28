import rpyc
from rpyc.utils.server import ThreadedServer
import threading
import time

class MyService(rpyc.Service):

    def __init__(self):
        self.channel_0 = 0
        self.channel_1 = 0

        #Start the user interface thread
        user_interface_thread = threading.Thread(target=self.main_thread, args=())
        user_interface_thread.start()
        
    # My service
    def exposed_echo(self, text):
        print(text)
        
    def exposed_channel_0_value(self):
        return self.channel_0

    def exposed_channel_1_value(self):
        return self.channel_1

    def main_thread(self):
        while(True):
            print("Hello! Press 1 to send a down pulse, 2 for a down hold (1 second), 3 for up hold (1 second)")
            ans = input()
            if ans == 1:
                self.channel_0 = 10000
                time.sleep(0.3)
                self.channel_0 = 0

if __name__ == "__main__":
    server = ThreadedServer(MyService, port = 18812)
    server.start()