from nbdev.read import read_nb
from nbdev.sync import *
from execnb import *

nb = read_nb('tests/clean.ipynb')
s = CaptureShell()

for cell in nb.cells:
    if cell.cell_type!='code': continue
    outs = s.run(cell.source)
    if outs:
        cell.outputs = outs
        for o in outs:
            if 'execution_count' in o: cell['execution_count'] = o['execution_count']

write_nb(nb, 'tests/foo.ipynb')

