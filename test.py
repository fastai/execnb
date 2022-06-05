from execnb import *

s = CaptureShell()
cmds = """import matplotlib.pyplot as plt
plt.plot([1,2])
print('1')
2
from nbdev.showdoc import show_doc
show_doc(bool)
raise Exception"""
for cmd in cmds.splitlines(): print(s.run(cmd),'\n')

