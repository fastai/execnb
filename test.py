from execnb import *

s = CaptureShell()
cmds = ["""import matplotlib.pyplot as plt
plt.figure(figsize=(1,1))
plt.plot([1,2])""",
    "print('1')\n2",
    "from nbdev.showdoc import show_doc\nshow_doc(bool)",
    "raise Exception"
]

for cmd in cmds: print(s.run(cmd),'\n')
assert s.result==2

