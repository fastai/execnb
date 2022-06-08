.ONESHELL:
SHELL := /bin/bash
SRC = $(wildcard nbs/*.ipynb)

nbprocess: $(SRC)
	nbprocess_export
	touch nbprocess

sync:
	nbprocess_update

deploy: docs
	nbprocess_ghp_deploy

serve:
	nbprocess_sidebar
	cd nbs && quarto preview

docs: .FORCE
	nbprocess_export
	nbprocess_quarto

test:
	nbprocess_test

release: pypi conda_release
	nbdev_bump_version

conda_release:
	fastrelease_conda_package --mambabuild --upload_user fastai

pypi: dist
	twine upload --repository pypi dist/*

dist: clean
	python setup.py sdist bdist_wheel

clean:
	rm -rf dist
	

install: install_quarto
	pip install -e ".[dev]"

install_quarto: .FORCE
	./install_quarto.sh

.FORCE:
