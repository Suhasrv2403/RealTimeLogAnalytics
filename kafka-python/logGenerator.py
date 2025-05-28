import random
import datetime
import time

log_status = ["put","get","auth","rmi"]



while True:
    status = random.choice(log_status)
    user_number = random.randint(1,100)
    log = str(datetime.datetime.now()) +"|"+ status +"|"+"User" + str(user_number)
    print(log)
    time.sleep(10)


