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

        self.default_0 = 500
        self.max_0 = 1500

        self.default_1 = 1000
        self.max_1 = 13000

        self.channel_0 = self.default_0
        self.channel_1 = self.default_1

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
            print("Hello! Press 1 to send a down pulse, 2 for a down hold (1 second), 4 for continuous close")
            ans = int(input())
            if ans == 1:
                #Write a down pulse to channel 0
                self.send_pulse(self.default_0, self.max_0, 0.3)
                # self.channel_0 = self.max_0
                # time.sleep(0.3)
                # self.channel_0 = self.default_0
            elif ans == 2:
                #Write a down hold to channel 0
                self.send_pulse(self.default_0, self.max_0, 0.5)
                self.channel_0 = self.max_0
                time.sleep(2)
                self.channel_0 = self.default_0
            elif ans == 4:
                #Write a continuous pulse from min to max over 10 seconds, then max to min over 10 again
                self.channel_0 = self.default_0
                loop_time = 10
                self.send_pulse(self.default_0, self.max_0, loop_time)
                self.channel_0 = self.max_0
                time.sleep(loop_time)
                self.send_pulse(self.max_0, self.default_0, loop_time)
                self.channel_0 = self.default_0

    def send_pulse(self, start, fin, delta_t):
        c = time.time()
        while ((time.time() - c) < delta_t):
                    self.channel_0 = (((time.time() - c)/delta_t) - start/(start-fin) ) * (fin - start)
                    print(str(self.channel_0))

if __name__ == "__main__":

    server = ThreadedServer(MyService, port = 18812)
    server.start()

    