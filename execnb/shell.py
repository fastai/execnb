"""A shell for running notebook code without a notebook server"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/02_shell.ipynb.

# %% ../nbs/02_shell.ipynb 2
from __future__ import annotations

from fastcore.utils import *
from fastcore.script import call_parse
from fastcore.ansi import ansi2html

import multiprocessing,types,traceback,signal
try:
    if sys.platform == 'darwin': multiprocessing.set_start_method("fork")
except RuntimeError: pass # if re-running cell

from IPython.core.interactiveshell import InteractiveShell, ExecutionInfo, ExecutionResult
from IPython.core.displayhook import DisplayHook
from IPython.utils.capture import capture_output
from IPython.utils.text import strip_ansi
from IPython.core.completer import IPCompleter,provisionalcompleter
from IPython.core.hooks import CommandChainDispatcher
from IPython.core.completerlib import module_completer
from IPython.utils.strdispatch import StrDispatch
from IPython.display import display as disp, HTML

from base64 import b64encode
from html import escape
try: from matplotlib_inline.backend_inline import set_matplotlib_formats
except ImportError: set_matplotlib_formats = None


from .nbio import *
from .nbio import _dict2obj

# %% auto 0
__all__ = ['CaptureShell', 'format_exc', 'render_outputs', 'find_output', 'out_exec', 'out_stream', 'out_error', 'exec_nb',
           'SmartCompleter']

# %% ../nbs/02_shell.ipynb
class _CustDisplayHook(DisplayHook):
    def write_output_prompt(self): pass
    def write_format_data(self, data, md_dict): pass
    def log_output(self, format_dict): pass

@patch
def __repr__(self: ExecutionInfo): return f'cell: {self.raw_cell}; id: {self.cell_id}'

@patch
def __repr__(self: ExecutionResult): return f'result: {self.result}; err: {self.error_in_exec}; info: <{self.info}>'

# %% ../nbs/02_shell.ipynb
class CaptureShell(InteractiveShell):
    displayhook_class = _CustDisplayHook

    def __init__(self, path:str|Path=None, mpl_format='retina', history=False, timeout:Optional[int]=None):
        super().__init__()
        self.history_manager.enabled = history
        self.timeout = timeout
        self.result,self.exc = None,None
        if path: self.set_path(path)
        self.display_formatter.active = True
        if not IN_NOTEBOOK: InteractiveShell._instance = self
        if set_matplotlib_formats:
            self.enable_matplotlib("inline")
            self._run("from matplotlib_inline.backend_inline import set_matplotlib_formats")
            self._run(f"set_matplotlib_formats('{mpl_format}')")

    def _run(self, raw_cell, store_history=False, silent=False, shell_futures=True, cell_id=None,
                 stdout=True, stderr=True, display=True):
        # TODO what if there's a comment?
        semic = raw_cell.rstrip().endswith(';')
        with capture_output(display=display, stdout=stdout, stderr=stderr) as c:
            result = super().run_cell(raw_cell, store_history, silent, shell_futures=shell_futures, cell_id=cell_id)
        return AttrDict(result=result, stdout='' if semic else c.stdout, stderr=c.stderr,
                        display_objects=c.outputs, exception=result.error_in_exec, quiet=semic)
    
    def set_path(self, path):
        "Add `path` to python path, or `path.parent` if it's a file"
        path = Path(path)
        if path.is_file(): path = path.parent
        self._run(f"import sys; sys.path.insert(0, '{path.as_posix()}')")
    
    def enable_gui(self, gui=None): pass

# %% ../nbs/02_shell.ipynb
@patch
def run_cell(self:CaptureShell, raw_cell, store_history=False, silent=False, shell_futures=True, cell_id=None,
             stdout=True, stderr=True, display=True, timeout=None):
    if not timeout: timeout = self.timeout
    if timeout:
        def handler(*args): raise TimeoutError()
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(timeout)
    try: return self._run(raw_cell, store_history, silent, shell_futures, cell_id=cell_id,
                          stdout=stdout, stderr=stderr, display=display)
    finally:
        if timeout: signal.alarm(0)

# %% ../nbs/02_shell.ipynb
def format_exc(e):
    "Format exception `e` as a string list"
    return traceback.format_exception(type(e), e, e.__traceback__)

# %% ../nbs/02_shell.ipynb
def _out_stream(text, name): return dict(name=name, output_type='stream', text=text.splitlines(True))
def _out_exc(e):
    ename = type(e).__name__
    tb = traceback.extract_tb(e.__traceback__)#.format()
    return dict(ename=str(ename), evalue=str(e), output_type='error', traceback=format_exc(e))

def _format_mimedata(k, v):
    "Format mime-type keyed data consistently with Jupyter"
    if k.startswith('text/'): return v.splitlines(True)
    if k.startswith('image/') and isinstance(v, bytes):
        v = b64encode(v).decode()
        return v+'\n' if not v.endswith('\n') else v
    return v

def _mk_out(data, meta, output_type='display_data'):
    fd = {k:_format_mimedata(k,v) for k,v in data.items()}
    return dict(data=fd, metadata=meta, output_type=output_type)

def _out_nb(o, fmt):
    res = []
    if o.stdout: res.append(_out_stream(o.stdout, 'stdout'))
    if o.stderr: res.append(_out_stream(o.stderr, 'stderr'))
    if o.exception: res.append(_out_exc(o.exception))
    r = o.result.result
    for x in o.display_objects: res.append(_mk_out(x.data, x.metadata))
    if r is not None and not o.quiet:
        res.append(_mk_out(*fmt.format(r), 'execute_result'))
    if 'execution_count' not in o: o['execution_count']=None
    for p in res:
        if p["output_type"]=="execute_result": p['execution_count'] = o['execution_count']
    return res

# %% ../nbs/02_shell.ipynb
@patch
def run(self:CaptureShell,
        code:str, # Python/IPython code to run
        stdout=True, # Capture stdout and save as output?
        stderr=True, # Capture stderr and save as output?
       timeout:Optional[int]=None): # Shell command will time out after {timeout} seconds
    "Run `code`, returning a list of all outputs in Jupyter notebook format"
    res = self.run_cell(code, stdout=stdout, stderr=stderr, timeout=timeout)
    self.result = res.result.result
    self.exc = res.exception
    return _out_nb(res, self.display_formatter)

# %% ../nbs/02_shell.ipynb
@patch
async def run_async(self:CaptureShell,
        code: str,  # Python/IPython code to run
        stdout=True,  # Capture stdout and save as output?
        stderr=True,  # Capture stderr and save as output?
        timeout:Optional[int]=None): # Shell command will time out after {timeout} seconds
    return self.run(code, stdout=stdout, stderr=stderr, timeout=timeout)

# %% ../nbs/02_shell.ipynb
def _pre(s, xtra=''): return f"<pre {xtra}><code>{escape(s)}</code></pre>"
def _strip(s): return strip_ansi(escape(s))

def render_outputs(outputs, ansi_renderer=_strip, include_imgs=True, pygments=False):
    try:
        from mistletoe import markdown, HTMLRenderer
        from mistletoe.contrib.pygments_renderer import PygmentsRenderer
    except ImportError: return print('mistletoe not found -- please install it')
    renderer = PygmentsRenderer if pygments else HTMLRenderer
    def render_output(out):
        otype = out['output_type']
        if otype == 'stream':
            txt = ansi_renderer(''.join(out['text']))
            xtra = '' if out['name']=='stdout' else "class='stderr'"
            return f"<pre {xtra}><code>{txt}</code></pre>"
        elif otype in ('display_data','execute_result'):
            data = out['data']
            _g = lambda t: ''.join(data[t]) if t in data else None
            if d := _g('text/html'): return d
            if d := _g('application/javascript'): return f'<script>{d}</script>'
            if d := _g('text/markdown'): return markdown(d, renderer=renderer)
            if d := _g('text/latex'): return f'<div class="math">${d}$</div>'
            if include_imgs:
                if d := _g('image/jpeg'): return f'<img src="data:image/jpeg;base64,{d}"/>'
                if d := _g('image/png'): return f'<img src="data:image/png;base64,{d}"/>'
            if d := _g('text/plain'): return _pre(d)
            if d := _g('image/svg+xml'): return d
            
        return ''
    
    return '\n'.join(map(render_output, outputs))

# %% ../nbs/02_shell.ipynb
@patch
def cell(self:CaptureShell, cell, stdout=True, stderr=True):
    "Run `cell`, skipping if not code, and store outputs back in cell"
    if cell.cell_type!='code': return
    self._cell_idx = cell.idx_ + 1
    outs = self.run(cell.source)
    if outs: cell.outputs = _dict2obj(outs)

# %% ../nbs/02_shell.ipynb
def find_output(outp, # Output from `run`
                ot='execute_result' # Output_type to find
               ):
    "Find first output of type `ot` in `CaptureShell.run` output"
    return first(o for o in outp if o['output_type']==ot)

# %% ../nbs/02_shell.ipynb
def out_exec(outp):
    "Get data from execution result in `outp`."
    out = find_output(outp)
    if out: return '\n'.join(first(out['data'].values()))

# %% ../nbs/02_shell.ipynb
def out_stream(outp):
    "Get text from stream in `outp`."
    out = find_output(outp, 'stream')
    if out: return ('\n'.join(out['text'])).strip()

# %% ../nbs/02_shell.ipynb
def out_error(outp):
    "Get traceback from error in `outp`."
    out = find_output(outp, 'error')
    if out: return '\n'.join(out['traceback'])

# %% ../nbs/02_shell.ipynb
def _false(o): return False

@patch
def run_all(self:CaptureShell,
            nb, # A notebook read with `nbclient` or `read_nb`
            exc_stop:bool=False, # Stop on exceptions?
            preproc:callable=_false, # Called before each cell is executed
            postproc:callable=_false, # Called after each cell is executed
            inject_code:str|None=None, # Code to inject into a cell
            inject_idx:int=0 # Cell to replace with `inject_code`
           ):
    "Run all cells in `nb`, stopping at first exception if `exc_stop`"
    if inject_code is not None: nb.cells[inject_idx].source = inject_code
    for cell in nb.cells:
        if not preproc(cell):
            self.cell(cell)
            postproc(cell)
        if self.exc and exc_stop: raise self.exc from None

# %% ../nbs/02_shell.ipynb
@patch
def execute(self:CaptureShell,
            src:str|Path, # Notebook path to read from
            dest:str|None=None, # Notebook path to write to
            exc_stop:bool=False, # Stop on exceptions?
            preproc:callable=_false, # Called before each cell is executed
            postproc:callable=_false, # Called after each cell is executed
            inject_code:str|None=None, # Code to inject into a cell
            inject_path:str|Path|None=None, # Path to file containing code to inject into a cell
            inject_idx:int=0 # Cell to replace with `inject_code`
):
    "Execute notebook from `src` and save with outputs to `dest"
    nb = read_nb(src)
    self._fname = src
    self.set_path(Path(src).parent.resolve())
    if inject_path is not None: inject_code = Path(inject_path).read_text()
    self.run_all(nb, exc_stop=exc_stop, preproc=preproc, postproc=postproc,
                 inject_code=inject_code, inject_idx=inject_idx)
    if dest: write_nb(nb, dest)

# %% ../nbs/02_shell.ipynb
@patch
def prettytb(self:CaptureShell, 
             fname:str|Path=None): # filename to print alongside the traceback
    "Show a pretty traceback for notebooks, optionally printing `fname`."
    fname = fname if fname else self._fname
    _fence = '='*75
    cell_intro_str = f"While Executing Cell #{self._cell_idx}:" if self._cell_idx else "While Executing:"
    cell_str = f"\n{cell_intro_str}\n{format_exc(self.exc)}"
    fname_str = f' in {fname}' if fname else ''
    return f"{type(self.exc).__name__}{fname_str}:\n{_fence}\n{cell_str}\n"

# %% ../nbs/02_shell.ipynb
@call_parse
def exec_nb(
    src:str, # Notebook path to read from
    dest:str='', # Notebook path to write to
    exc_stop:bool=False, # Stop on exceptions?
    inject_code:str=None, # Code to inject into a cell
    inject_path:str=None, # Path to file containing code to inject into a cell
    inject_idx:int=0 # Cell to replace with `inject_code`
):
    "Execute notebook from `src` and save with outputs to `dest`"
    CaptureShell().execute(src, dest, exc_stop=exc_stop, inject_code=inject_code,
                           inject_path=inject_path, inject_idx=inject_idx)

# %% ../nbs/02_shell.ipynb
class SmartCompleter(IPCompleter):
    def __init__(self, shell, namespace=None, jedi=False):
        if namespace is None: namespace = shell.user_ns
        super().__init__(shell, namespace)
        self.use_jedi = jedi
        sdisp = StrDispatch()
        self.custom_completers = sdisp
        import_disp = CommandChainDispatcher()
        import_disp.add(types.MethodType(module_completer, shell))
        sdisp.add_s('import', import_disp)
        sdisp.add_s('from', import_disp)

    def __call__(self, c):
        if not c: return []
        with provisionalcompleter():
            return [o.text.rpartition('.')[-1]
                    for o in self.completions(c, len(c))
                    if o.type not in ('magic', 'path')]

# %% ../nbs/02_shell.ipynb
@patch
def complete(self:CaptureShell, c):
    if not hasattr(self, '_completer'): self._completer = SmartCompleter(self)
    return self._completer(c)
