# Copyright (c) IPython Development Team.
# Modifications by Jeremy Howard
# Distributed under the terms of the Modified BSD License.

import os, sys, warnings
from IPython.core.interactiveshell import InteractiveShell, InteractiveShellABC
from IPython.core.autocall import ZMQExitAutocall
from IPython.core.magic import magics_class, line_magic, Magics
from IPython.utils.process import system
from traitlets import Instance, Type, Any, default, observe

@magics_class
class KernelMagics(Magics):
    @line_magic
    def edit(self, parameter_s='', last_call=['','']): pass

    @line_magic
    def clear(self, arg_s): pass

    @line_magic
    def less(self, arg_s): pass

    more = line_magic('more')(less)

    # Man calls a pager, so we also need to redefine it
    if os.name == 'posix':
        @line_magic
        def man(self, arg_s): pass

    @line_magic
    def autosave(self, arg_s): pass

class FastInteractiveShell(InteractiveShell):
    data_pub_class = Any()
    kernel = Any()
    parent_header = Any()
    exiter = Instance(ZMQExitAutocall)

    @default('exiter')
    def _default_exiter(self): return ZMQExitAutocall(self)

    @observe('exit_now')
    def _update_exit_now(self, change):
        "stop eventloop when exit_now fires"
        if change['new']:
            if hasattr(self.kernel, 'io_loop'):
                loop = self.kernel.io_loop
                loop.call_later(0.1, loop.stop)
            if self.kernel.eventloop:
                exit_hook = getattr(self.kernel.eventloop, 'exit_hook', None)
                if exit_hook: exit_hook(self.kernel)

    keepkernel_on_exit = None

    def init_environment(self):
        "Configure the user's environment."
        env = os.environ
        env['TERM'] = 'xterm-color'
        env['CLICOLOR'] = '1'
        env['PAGER'] = 'cat'
        env['GIT_PAGER'] = 'cat'

    def init_data_pub(self): pass

    @property
    def data_pub(self):
        if not hasattr(self, '_data_pub'):
            warnings.warn("InteractiveShell.data_pub is deprecated outside IPython parallel.", DeprecationWarning, stacklevel=2)
            self._data_pub = self.data_pub_class(parent=self)
            self._data_pub.session = self.display_pub.session
            self._data_pub.pub_socket = self.display_pub.pub_socket
        return self._data_pub

    @data_pub.setter
    def data_pub(self, pub): self._data_pub = pub

    def ask_exit(self):
        "Engage the exit actions."
        self.exit_now = (not self.keepkernel_on_exit)
        payload = dict( source='ask_exit', keepkernel=self.keepkernel_on_exit,)
        self.payload_manager.write_payload(payload)

    def set_next_input(self, text, replace=False):
        "Send the specified text to the frontend to be presented at the next input cell."
        payload = dict( source='set_next_input', text=text, replace=replace,)
        self.payload_manager.write_payload(payload)

    def set_parent(self, parent):
        "Set the parent header for associating output with its triggering input"
        self.parent_header = parent
        self.displayhook.set_parent(parent)
        self.display_pub.set_parent(parent)
        if hasattr(self, '_data_pub'): self.data_pub.set_parent(parent)
        try: sys.stdout.set_parent(parent)
        except AttributeError: pass
        try: sys.stderr.set_parent(parent)
        except AttributeError: pass

    def get_parent(self): return self.parent_header

    def init_magics(self):
        super().init_magics()
        self.register_magics(KernelMagics)
        self.magics_manager.register_alias('ed', 'edit')

    def init_virtualenv(self): pass

    def system_piped(self, cmd):
        "Call the given cmd in a subprocess, piping stdout/err "
        if cmd.rstrip().endswith('&'): raise OSError("Background processes not supported.")
        if sys.platform == 'win32':
            cmd = self.var_expand(cmd, depth=1)
            from IPython.utils._process_win32 import AvoidUNCPath
            with AvoidUNCPath() as path:
                if path is not None: cmd = 'pushd %s &&%s' % (path, cmd)
                self.user_ns['_exit_code'] = system(cmd)
        else: self.user_ns['_exit_code'] = system(self.var_expand(cmd, depth=1))

    system = system_piped

InteractiveShellABC.register(FastInteractiveShell)

