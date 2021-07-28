import rpyc
from rpyc.utils.server import ThreadedServer
import threading
import time

class MyService(rpyc.Service):

    # My service
    def exposed_echo(self, text):
        print(text)
        
    def exposed_channel_0_value(self):
        return self.channel_0

    def exposed_channel_1_value(self):
        return self.channel_1       

    def on_connect(self, conn):
        # code that runs when a connection is created
        # (to init the service, if needed)
        self.channel_0 = 5
        self.channel_1 = 13

        print("init completed")

        UI_thread = threading.Thread(target=self.main_thread, args=())
        UI_thread.start()

    def on_disconnect(self, conn):
        # code that runs after the connection has already closed
        # (to finalize the service, if needed)
        pass

    def get_question(self):  # while this method is not exposed
        return "what is the airspeed velocity of an unladen swallow?"

    def main_thread(self):
        while(True):
            print("Hello! Press 1 to send a down pulse, 2 for a down hold (1 second), 3 for up hold (1 second)")
            ans = input()
            if ans == 1:
                channel_0 = 10000
                time.sleep(10)
                channel_0 = 0

if __name__ == "__main__":

    server = ThreadedServer(MyService, port = 18812)
    server.start()

    