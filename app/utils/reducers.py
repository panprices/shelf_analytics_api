from typing import Dict, TypeVar, List, Callable


T = TypeVar("T")


def _reduce_to_dict_by_key(
    key_extractor: Callable[[T], str]
) -> Callable[[Dict, T], Dict]:
    def reducer(result: Dict[str, List[T]], value: T):
        key = key_extractor(value)
        if key not in result:
            result[key] = []

        result[key].append(value)
        return result

    return reducer
