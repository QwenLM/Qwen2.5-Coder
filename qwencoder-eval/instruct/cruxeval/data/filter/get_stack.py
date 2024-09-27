# Copyright (c) Meta Platforms, Inc. and affiliates.

# Taken from https://gist.github.com/crusaderky/cf0575cfeeee8faa1bb1b3480bc4a87a

import sys
from ctypes import POINTER, py_object, Structure, c_ssize_t, c_void_p, sizeof
from typing import Any, Iterator, Optional, Sequence, Union


__all__ = ("OpStack", )


class Frame(Structure):
    _fields_ = (
        ("ob_refcnt", c_ssize_t),
        ("ob_type", c_void_p),
        ("ob_size", c_ssize_t),
        ("f_back", c_void_p),
        ("f_code", c_void_p),
        ("f_builtins", POINTER(py_object)),
        ("f_globals", POINTER(py_object)),
        ("f_locals", POINTER(py_object)),
        ("f_valuestack", POINTER(py_object)),
        ("f_stacktop", POINTER(py_object)),
    )

if sys.flags.debug:
    Frame._fields_ = (
        ("_ob_next", POINTER(py_object)),
        ("_ob_prev", POINTER(py_object)),
    ) + Frame._fields_

PTR_SIZE = sizeof(POINTER(py_object))
F_VALUESTACK_OFFSET = sizeof(Frame) - 2 * PTR_SIZE
F_STACKTOP_OFFSET = sizeof(Frame) - PTR_SIZE


class OpStack(Sequence[Any]):
    __slots__ = ("_frame", "_len")

    def __init__(self, frame):
        self._frame = Frame.from_address(id(frame))
        stack_start_addr = c_ssize_t.from_address(id(frame) + F_VALUESTACK_OFFSET).value
        stack_top_addr = c_ssize_t.from_address(id(frame) + F_STACKTOP_OFFSET).value
        self._len = (stack_top_addr - stack_start_addr) // PTR_SIZE
        # print('size stack?', self._len)

    def __repr__(self) -> str:
        if not self:
            return "<OpStack> (empty)>"
        return "<OpStack ({})>\n- {}\n".format(
            len(self),
            "\n- ".join(repr(o) for o in reversed(self)),
        )

    def __len__(self):
        return self._len

    def _preproc_slice(self, idx: Optional[int], default: int) -> int:
        if idx is None:
            return default
        if idx < -self._len or idx >= self._len:
            raise IndexError(idx)
        if idx < 0:
            return idx + self._len
        return idx

    def __getitem__(self, item: Union[int, slice]) -> Any:
        if isinstance(item, int):
            if item < -self._len or item >= self._len:
                raise IndexError(item)
            if item < 0:
                return self._frame.f_stacktop[item]
            return self._frame.f_valuestack[item]

        if isinstance(item, slice):
            item = slice(
                self._preproc_slice(item.start, 0),
                self._preproc_slice(item.stop, self._len),
                item.step
            )
            return self._frame.f_valuestack[item]

        raise TypeError(item)

    def __iter__(self) -> Iterator[Any]:
        for i in range(self._len):
            yield self._frame.f_valuestack[i]

    def __reversed__(self) -> Iterator[Any]:
        for i in range(self._len - 1, -1, -1):
            yield self._frame.f_valuestack[i]