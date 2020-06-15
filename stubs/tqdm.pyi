from typing import Any, Iterator, Iterable, TypeVar

T = TypeVar("T")

def tqdm(iterator: Iterable[T], *args: Any, **kwargs: Any) -> Iterator[T]: ...
