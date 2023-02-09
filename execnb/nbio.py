# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_nbio.ipynb.

# %% auto 0
__all__ = ['NbCell', 'dict2nb', 'read_nb', 'new_nb', 'mk_cell', 'nb2dict', 'nb2str', 'write_nb']

# %% ../nbs/01_nbio.ipynb 2
from fastcore.basics import *
from fastcore.imports import *

import ast,functools
from pprint import pformat,pprint
from json import loads,dumps

# %% ../nbs/01_nbio.ipynb 6
def _read_json(self, encoding=None, errors=None):
    return loads(Path(self).read_text(encoding=encoding, errors=errors))

# %% ../nbs/01_nbio.ipynb 13
class NbCell(AttrDict):
    def __init__(self, idx, cell):
        super().__init__(cell)
        self.idx_ = idx
        if 'source' in self: self.set_source(self.source)

    def set_source(self, source):
        self.source = ''.join(source)
        if '_parsed_' in self: del(self['_parsed_'])

    def parsed_(self):
        if self.cell_type!='code' or self.source.strip()[:1] in ['%', '!']: return
        if '_parsed_' not in self: 
            try: self._parsed_ = ast.parse(self.source).body
            # you can assign the result of ! to a variable in a notebook cell
            # which will result in a syntax error if parsed with the ast module.
            except SyntaxError: return
        return self._parsed_

    def __hash__(self): return hash(self.source) + hash(self.cell_type)
    def __eq__(self,o): return self.source==o.source and self.cell_type==o.cell_type

# %% ../nbs/01_nbio.ipynb 15
def _dict2obj(d, list_func=list, dict_func=AttrDict):
    "Convert (possibly nested) dicts (or lists of dicts) to `AttrDict`"
    if isinstance(d, list): return list(map(_dict2obj, d))
    if not isinstance(d, dict): return d
    return dict_func(**{k:_dict2obj(v) for k,v in d.items()})

def dict2nb(js=None, **kwargs):
    "Convert dict `js` to an `AttrDict`, "
    nb = _dict2obj(js or kwargs)
    nb.cells = [NbCell(*o) for o in enumerate(nb.cells)]
    return nb

# %% ../nbs/01_nbio.ipynb 20
def read_nb(path):
    "Return notebook at `path`"
    res = dict2nb(_read_json(path, encoding='utf-8'))
    res['path_'] = str(path)
    return res

# %% ../nbs/01_nbio.ipynb 26
def new_nb(cells=None, meta=None, nbformat=4, nbformat_minor=5):
    "Returns an empty new notebook"
    return dict2nb(cells=cells or [],metadata=meta or {},nbformat=nbformat,nbformat_minor=nbformat_minor)

# %% ../nbs/01_nbio.ipynb 28
def mk_cell(text,  # `source` attr in cell
            cell_type='code',  # `cell_type` attr in cell
            **kwargs):  # any other attrs to add to cell
    "Create an `NbCell` containing `text`"
    assert cell_type in {'code', 'markdown', 'raw'}
    if 'metadata' not in kwargs: kwargs['metadata']={}
    return NbCell(0, dict(cell_type=cell_type, source=text, directives_={}, **kwargs))

# %% ../nbs/01_nbio.ipynb 31
def nb2dict(d, k=None):
    "Convert parsed notebook to `dict`"
    if k=='source': return d.splitlines(keepends=True)
    if isinstance(d, list): return list(map(nb2dict,d))
    if not isinstance(d, dict): return d
    return dict(**{k:nb2dict(v,k) for k,v in d.items() if k[-1] != '_'})

# %% ../nbs/01_nbio.ipynb 34
def nb2str(nb):
    "Convert `nb` to a `str`"
    if isinstance(nb, (AttrDict,list)): nb = nb2dict(nb)
    return dumps(nb, sort_keys=True, indent=1, ensure_ascii=False) + "\n"

# %% ../nbs/01_nbio.ipynb 37
def write_nb(nb, path):
    "Write `nb` to `path`"
    new = nb2str(nb)
    path = Path(path)
    old = Path(path).read_text(encoding="utf-8") if path.exists() else None
    if new!=old:
        with open(path, 'w', encoding='utf-8') as f: f.write(new)
