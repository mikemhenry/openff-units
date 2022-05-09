"""
Core classes for OpenFF Units
"""

import uuid
import warnings

import pint
from pint.measurement import _Measurement
from pint.quantity import _Quantity
from pint.unit import _Unit

from openff.units.utilities import get_defaults_path

__all__ = [
    "DEFAULT_UNIT_REGISTRY",
    "Quantity",
    "Measurement",
    "Unit",
]

DEFAULT_UNIT_REGISTRY = pint.UnitRegistry(get_defaults_path())
"""The default unit registry provided by OpenFF Units"""

MD_UNITS = {
    "[length]": DEFAULT_UNIT_REGISTRY.nanometer,
    "[mass]": DEFAULT_UNIT_REGISTRY.unified_atomic_mass_unit,
    "[temperature]": DEFAULT_UNIT_REGISTRY.kelvin,
    "[time]": DEFAULT_UNIT_REGISTRY.picosecond,
    "[substance]": DEFAULT_UNIT_REGISTRY.mol,
    "[current]": DEFAULT_UNIT_REGISTRY.e / DEFAULT_UNIT_REGISTRY.picosecond,
}


def _unpickle_quantity(cls, *args):
    """Rebuild quantity upon unpickling using the application registry."""
    return pint._unpickle(DEFAULT_UNIT_REGISTRY.Quantity, *args)


def _unpickle_unit(cls, *args):
    """Rebuild unit upon unpickling using the application registry."""
    return pint._unpickle(DEFAULT_UNIT_REGISTRY.Unit, *args)


def _unpickle_measurement(cls, *args):
    """Rebuild measurement upon unpickling using the application registry."""
    return pint._unpickle(DEFAULT_UNIT_REGISTRY.Measurement, *args)


class Unit(_Unit):
    """A unit of measure."""

    _REGISTRY = DEFAULT_UNIT_REGISTRY

    def __reduce__(self):
        return _unpickle_unit, (Unit, self._units)

    def get_compatible_md_units(self) -> "Unit":
        iterable = iter(self.dimensionality.items())

        dim, exp = next(iterable)
        print(dim, exp)
        out_units = MD_UNITS[dim] ** exp
        for dim, exp in iterable:
            print(dim, exp)
            out_units *= MD_UNITS[dim] ** exp
        return out_units


class Quantity(_Quantity):
    """A value with associated units."""

    _REGISTRY = DEFAULT_UNIT_REGISTRY

    def __reduce__(self):
        return _unpickle_quantity, (Quantity, self.magnitude, self._units)

    def __dask_tokenize__(self):
        return uuid.uuid4().hex

    @staticmethod
    def _dask_finalize(results, func, args, units):
        values = func(results, *args)
        return Quantity(values, units)

    def to_md_units(self) -> "Quantity":
        """Convert the quantity to Da/nm/ps/e units"""
        return self.to(self.units.get_compatible_md_units())

    def ito_md_units(self):
        """Convert the quantity to Da/nm/ps/e units"""
        self.ito(self.units.get_compatible_md_units())


class Measurement(_Measurement):
    """A value with associated units and uncertainty."""

    _REGISTRY = DEFAULT_UNIT_REGISTRY

    def __reduce__(self):
        return _unpickle_measurement, (Measurement, self.magnitude, self._units)

    def __dask_tokenize__(self):
        return uuid.uuid4().hex

    @staticmethod
    def _dask_finalize(results, func, args, units):
        values = func(results, *args)
        return Measurement(values, units)


DEFAULT_UNIT_REGISTRY.Unit = Unit
DEFAULT_UNIT_REGISTRY.Quantity = Quantity
DEFAULT_UNIT_REGISTRY.Measurement = Measurement

pint.set_application_registry(DEFAULT_UNIT_REGISTRY)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    Quantity([])
