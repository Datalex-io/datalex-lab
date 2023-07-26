from setuptools import setup, find_packages
from version import __version__

setup(
  name='dlx-hello-world',
  version=__version__,
  description="A funky hello world",
  author='Alexandre Bergere & Christophe Lemonnier',
  author_email='alexandre.bergere@datalex.io',
  install_requires=[],
  extras_require={
    "dev": [
      "pytest==6.2.5",
      "build==0.5.1",
      "twine==3.4.2"
    ]
  },
  packages=find_packages(),
)