from json import JSONEncoder, JSONDecoder
import cirq
import numpy as np
import openfermion as of
from typing import Any

CIRQ_TYPES = (cirq.Qid, cirq.Gate, cirq.Operation, cirq.Moment, cirq.AbstractCircuit)

OF_TYPES = (of.SymbolicOperator,)


TYPE_FLAG = "type"
DATA_FLAG = "data"
KWARGS_FLAG = "kwargs"


class ExtendedJSONEncoder(JSONEncoder):
    def default(self, obj: dict) -> str:
        if isinstance(obj, *CIRQ_TYPES):
            return {
                TYPE_FLAG: cirq.json_cirq_type(obj),
                DATA_FLAG: cirq.to_json(obj, indent=4),
            }
        elif isinstance(obj, np.ndarray):
            return {
                TYPE_FLAG: obj.__class__.__name__,
                KWARGS_FLAG: {"dtype": str(obj.dtype)},
                DATA_FLAG: obj.tolist(),
            }
        elif isinstance(obj, *OF_TYPES):
            return {TYPE_FLAG: obj.__class__.__name__, DATA_FLAG: str(obj)}
        return super().default(obj)


class ExtendedJSONDecoder(JSONDecoder):
    def __init__(self):
        JSONDecoder.__init__(self, object_hook=self.object_hook)

    def object_hook(self, dct: dict) -> Any:
        if TYPE_FLAG in dct:
            t = get_type(dct[TYPE_FLAG])
            return t(dct[DATA_FLAG], **dct[KWARGS_FLAG])
        return dct


def get_type(s: str) -> Any:
    try:
        return getattr(np, s)
    except:
        pass
    try:
        return cirq.cirq_type_from_json(s)
    except:
        pass
    try:
        return getattr(of, s)
    except:
        raise ValueError("{} is an unknown type".format(s))
