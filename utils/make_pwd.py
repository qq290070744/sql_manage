import random
import re
import string


def make_pwd():
    count1 = 8
    i = 0
    passwds = []
    while i < count1:
        tmp = random.sample(string.ascii_letters + string.digits, 8)
        passwd = ''.join(tmp)
        if re.search('[0-9]', passwd) and re.search('[A-Z]', passwd) and re.search('[a-z]', passwd):
            passwds.append(passwd)
            i += 1
    return passwd
