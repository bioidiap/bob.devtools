import sys

# couple of imports to see if packages are working
import numpy
import pkg_resources


def test_pytorch():
    import torch

    from torchvision.models import DenseNet

    model = DenseNet()
    t = torch.randn(1, 3, 224, 224)
    out = model(t)
    assert out.shape[1] == 1000


def _check_package(name, pyname=None):
    "Checks if a Python package can be `require()`'d"

    pyname = pyname or name
    print(f"Checking Python setuptools integrity for {name} (pyname: {pyname})")
    pkg_resources.require(pyname)


def test_setuptools_integrity():

    _check_package("pytorch", "torch")
    _check_package("torchvision")


# test if pytorch installation is sane
test_pytorch()
test_setuptools_integrity()
