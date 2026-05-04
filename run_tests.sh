#!/bin/bash
export PYTHONPATH=$PYTHONPATH:.
xvfb-run python3 -m unittest discover -s gui/tests/
