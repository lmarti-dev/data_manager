from json import JSONDecoder, JSONEncoder
from typing import Any

import numpy as np

# don't need these libraries but they're useful for me.
try:
    import cirq

    CIRQ_TYPES = (
        cirq.Qid,
        cirq.Gate,
        cirq.Operation,
        cirq.Moment,
        cirq.AbstractCircuit,
        cirq.PauliSum,
        cirq.PauliString,
    )
    CIRQ_IMPORTED = True
except ImportError:
    CIRQ_IMPORTED = False


try:
    import openfermion as of

    OF_TYPES = (of.SymbolicOperator,)
    OF_IMPORTED = True
except ImportError:
    OF_IMPORTED = False


try:
    import sympy

    SYMPY_IMPORTED = True
except ImportError:
    SYMPY_IMPORTED = False

TYPE_FLAG = "type"
ARGS_FLAG = "args"
KWARGS_FLAG = "kwargs"


class ExtendedJSONEncoder(JSONEncoder):
    def default(self, obj: Any) -> dict:
        if isinstance(obj, complex):
            return {
                TYPE_FLAG: "complex",
                KWARGS_FLAG: {"real": obj.real, "imag": obj.imag},
            }
        elif isinstance(obj, np.ndarray):
            return {
                TYPE_FLAG: obj.__class__.__name__,
                ARGS_FLAG: obj.tolist(),
                KWARGS_FLAG: {"dtype": str(obj.dtype)},
            }
        elif CIRQ_IMPORTED and isinstance(obj, CIRQ_TYPES):
            return {
                TYPE_FLAG: obj.__class__.__name__,
                ARGS_FLAG: cirq.to_json(obj, indent=4),
            }

        elif (OF_IMPORTED and isinstance(obj, OF_TYPES)) or (
            SYMPY_IMPORTED and isinstance(obj, sympy.Symbol)
        ):
            return {TYPE_FLAG: obj.__class__.__name__, ARGS_FLAG: str(obj)}

        elif isinstance(obj, np.longdouble):
            # welp
            return {
                TYPE_FLAG: "np.longdouble",
                ARGS_FLAG: float(obj),
            }
        return super().default(obj)


class ExtendedJSONDecoder(JSONDecoder):
    def __init__(self):
        JSONDecoder.__init__(self, object_hook=self.object_hook)

    def object_hook(self, dct: dict) -> Any:
        if TYPE_FLAG in dct:
            t = get_type(dct[TYPE_FLAG])
            args = []
            kwargs = {}
            if ARGS_FLAG in dct:
                args.append(dct[ARGS_FLAG])
            if KWARGS_FLAG in dct:
                kwargs.update(dct[KWARGS_FLAG])
            return t(*args, **kwargs)
        return dct


# A+ type hinting
def try_get_attr(cls: np.__class__, obj: Any):
    try:
        return getattr(cls, obj)
    except Exception:
        pass


def get_type(s: str) -> Any:
    try:
        # make it fail fast if needed
        # somehow getattr(__builtins__, "complex") raises an error. why?
        assert s == "complex"
        return complex
    except Exception:
        pass
    try:
        assert s == "float128"
        return np.float128
    except Exception:
        pass
    try:
        # hate this
        assert getattr(np, s).__name__ == "ndarray"
        return np.array
    except Exception:
        pass
    # the attr is the class with desired constructor
    if CIRQ_IMPORTED:
        try:
            getattr(cirq, s)
            return lambda x: cirq.read_json(json_text=x)
        # TODO: figure out which errors would show up
        except Exception:
            pass
    if SYMPY_IMPORTED:
        return try_get_attr(sympy, s)
    if OF_IMPORTED:
        return try_get_attr(of, s)
    raise TypeError("{} is an unknown type".format(s))
