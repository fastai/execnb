__all__ = ['CaptureHook', 'CapturePub', 'out_err', 'out_stream', 'out_exec', 'CaptureShell']


from fastcore.utils import *
from IPython.core.interactiveshell import InteractiveShell
from IPython.core.displayhook import DisplayHook
from IPython.core.displaypub import DisplayPublisher
from io import StringIO

from .fastshell import FastInteractiveShell


class CaptureHook(DisplayHook):
    "Called when displaying a result"
    def __init__(self, parent, shell, cache_size, outputs=None):
        super().__init__(parent=parent, shell=shell, cache_size=cache_size)
        self.outputs = [] if outputs is None else outputs

    def __call__(self, result=None):
        if result is None: return
        self.fill_exec_result(result)
        format_dict, md_dict = self.shell.display_formatter.format(result)
        self.outputs.append({ 'data': format_dict, 'metadata': md_dict })

class CapturePub(DisplayPublisher):
    "Called when adding an output"
    def __init__(self,parent=None,shell=None): self.outputs = []
    def publish(self, data, metadata=None, source=None, *, transient=None, update=False):
        self.outputs.append({'data':data, 'metadata':metadata, 'transient':transient, 'update':update})


def out_err(ename, evalue, traceback): return dict(ename=ename, evalue=evalue, output_type='error', traceback=traceback)
def out_stream(text): return dict(name='stdout', output_type='stream', text=text.splitlines(False))
def out_exec(res):
    d = {'text/plain': f'{res}'.splitlines(True)}
    return dict(data=d, execution_count=1, metadata={}, output_type='execute_result')


class CaptureShell(FastInteractiveShell):
    def __init__(self):
        super().__init__(displayhook_class=CaptureHook, display_pub_class=CapturePub)
        InteractiveShell._instance = self
        self.outputs = self.display_pub.outputs
        self.run_cell('%matplotlib inline')

    def enable_gui(self, gui=None): pass
    def _showtraceback(self, etype, evalue, stb: str): self.outputs.append(out_err(etype, evalue, stb))
    def _result(self, result): self.outputs.append(out_exec(result))
    def _stream(self, std):
        text = std.getvalue()
        if text: self.outputs.append(out_stream(text))

    def run(self, code:str, stdout=True, stderr=True):
        self.outputs.clear()
        self.sys_stdout,self.sys_stderr = sys.stdout,sys.stderr
        if stdout: stdout = sys.stdout = StringIO()
        if stderr: stderr = sys.stderr = StringIO()
        try:
            res = self.run_cell(code).result
            self._stream(stdout)
            if res is not None: self._result(res)
            return self.outputs
        finally: sys.stdout,sys.stderr = self.sys_stdout,self.sys_stderr

