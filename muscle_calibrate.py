from Muscle_Driver import muscle

mi = muscle.muscle_interface()
print("What channel do you want to read?")
ans = int(input())
while True:
    print(str(mi.ads.read_adc(ans, gain=1)))