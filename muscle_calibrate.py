from Muscle_Driver import muscle

mi = muscle.muscle_interface()

while True:
    print(str(mi.ads.read_adc(1, gain=1)))