from distutils.core import setup
from setuptools import find_packages

setup(name='Planner',
	  version = '1.0',
	  py_modules = ['Planner', 'Element', 'ElementGraph', 'PlanElementGraph', 'Graph', 'Flaws', 'OrderingGraph',
					'pddlToGraphs', 'Restrictions'],
	  packages = find_packages())

