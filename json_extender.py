from json import JSONEncoder, JSONDecoder
import cirq
import numpy as np
import openfermion as of
from typing import Any

CIRQ_TYPES = (cirq.Qid, cirq.Gate, cirq.Operation, cirq.Moment, cirq.AbstractCircuit)

OF_TYPES = (of.SymbolicOperator,)


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
        elif isinstance(obj, CIRQ_TYPES):
            return {
                TYPE_FLAG: obj.__class__.__name__,
                ARGS_FLAG: cirq.to_json(obj, indent=4),
            }

        elif isinstance(obj, OF_TYPES):
            return {TYPE_FLAG: obj.__class__.__name__, ARGS_FLAG: str(obj)}

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


def get_type(s: str) -> Any:
    try:
        assert getattr(np, s).__name__ == "ndarray"
        return np.array
    except:
        pass
    try:
        return getattr(cirq, s)
    except:
        pass
    try:
        return getattr(of, s)
    except:
        pass
    try:
        return complex
    except:
        pass
    raise ValueError("{} is an unknown type".format(s))
