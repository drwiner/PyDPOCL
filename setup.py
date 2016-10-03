from distutils.core import setup
from setuptools import find_packages

setup(name='Bat-leth',
	  version = '1.0',
	  py_modules = ['Planner', 'Plannify', 'Element', 'ElementGraph', 'PlanElementGraph', 'Graph', 'Flaws',
					'OrderingGraph','Relax','Ground','clockdeco',
					'pddlToGraphs', 'Restrictions'],
	  packages = find_packages())

