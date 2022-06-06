__all__ = ['CaptureHook', 'CapturePub', 'out_err', 'out_stream', 'CaptureShell']

from fastcore.utils import *
from IPython.core.interactiveshell import InteractiveShell
from IPython.core.displayhook import DisplayHook
from IPython.core.displaypub import DisplayPublisher
from io import StringIO

from .fastshell import FastInteractiveShell


class CaptureHook(DisplayHook):
    "Called when displaying a result"
    def __call__(self, result=None):
        if result is None: return
        self.fill_exec_result(result)
        self.shell._result(result)


class CapturePub(DisplayPublisher):
    "Called when adding an output"
    #def __init__(self,parent=None,shell=None): self.parent,self.shell = parent,shell
    def publish(self, data, metadata=None, **kwargs): self.shell.add_out(data, metadata, typ='display_data')


def out_err(ename, evalue, traceback): return dict(ename=str(ename), evalue=str(evalue), output_type='error', traceback=traceback)
def out_stream(text): return dict(name='stdout', output_type='stream', text=text.splitlines(False))


class CaptureShell(FastInteractiveShell):
    def __init__(self):
        super().__init__(displayhook_class=CaptureHook, display_pub_class=CapturePub)
        InteractiveShell._instance = self
        self.out,self.count = [],1
        self.run_cell('%matplotlib inline')

    def enable_gui(self, gui=None): pass
    def _showtraceback(self, etype, evalue, stb: str): self.out.append(out_err(etype, evalue, stb))
    def add_out(self, data, meta, typ='execute_result', **kwargs): self.out.append(dict(data=data, metadata=meta, output_type=typ, **kwargs))

    def add_exec(self, result, meta, typ='execute_result'):
        fd = {k:v.splitlines(True) for k,v in result.items()}
        self.add_out(fd, meta, execution_count=self.count)
        self.count += 1

    def _result(self, result): self.add_exec(*self.display_formatter.format(result))

    def _stream(self, std):
        text = std.getvalue()
        if text: self.out.append(out_stream(text))

    def run(self, code:str, stdout=True, stderr=True):
        self.out.clear()
        self.sys_stdout,self.sys_stderr = sys.stdout,sys.stderr
        if stdout: stdout = sys.stdout = StringIO()
        if stderr: stderr = sys.stderr = StringIO()
        try:
            res = self.run_cell(code).result
            self._stream(stdout)
            return [*self.out]
        finally: sys.stdout,sys.stderr = self.sys_stdout,self.sys_stderr

