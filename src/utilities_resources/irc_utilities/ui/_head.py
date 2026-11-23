import os
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher.py")
src = open(p).read()
print(src[:3400])

