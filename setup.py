from setuptools import setup, find_packages

setup(
    name='pgfinder',
    version='0.0.1',
    url='https://github.com/Mesnage-Org/pgfinder',
    author='pgfinder Team',
    packages=find_packages(),    
    install_requires=['hide_code>=0.6.0',
                      'ipysheet>=0.4.4',
                      'ipywidgets>=7.6.3',
                      'jupyterlab>=3.0.15',
                      'numpy>=1.20.3', 
                      'pandas>=1.2.4', 
                      'pysqlite3'],
)