"""Functions from the `jax.lax` module."""

from __future__ import annotations

from typing import Any, Callable, TypeVar

import numpy as onp

from jumpy import is_jax_installed, ndarray
from jumpy.core import is_jitted, which_np

try:
    import jax
    import jax.numpy as jnp
except ImportError:
    jax, jnp = None, None


__all__ = ["cond", "fori_loop", "scan", "top_k", "while_loop"]

Carry = TypeVar("Carry")
X = TypeVar("X")
Y = TypeVar("Y")


def cond(
    pred, true_fun: Callable[..., bool], false_fun: Callable[..., bool], *operands: Any
):
    """Conditionally apply true_fun or false_fun to operands."""
    if is_jitted():
        return jax.lax.cond(pred, true_fun, false_fun, *operands)
    else:
        if pred:
            return true_fun(operands)
        else:
            return false_fun(operands)


def fori_loop(lower: int, upper: int, body_fun: Callable[[X], X], init_val: X) -> X:
    """Call body_fun over range from lower to upper, starting with init_val."""
    if is_jitted():
        return jax.lax.fori_loop(lower, upper, body_fun, init_val)
    else:
        val = init_val
        for _ in range(lower, upper):
            val = body_fun(val)
        return val


def scan(
    f: Callable[[Carry, X], tuple[Carry, Y]],
    init: Carry,
    xs: X,
    length: int | None = None,
    reverse: bool = False,
    unroll: int = 1,
) -> tuple[Carry, Y]:
    """Scan a function over leading array axes while carrying along state."""
    if not is_jax_installed:
        raise NotImplementedError("This function requires the jax module")

    if is_jitted():
        return jax.lax.scan(f, init, xs, length, reverse, unroll)
    else:
        xs_flat, xs_tree = jax.tree_util.tree_flatten(xs)
        carry = init
        ys = []
        maybe_reversed = reversed if reverse else lambda x: x
        for i in maybe_reversed(range(length)):
            xs_slice = [x[i] for x in xs_flat]
            carry, y = f(carry, jax.tree_util.tree_unflatten(xs_tree, xs_slice))
            ys.append(y)
        stacked_y = jax.tree_util.tree_map(lambda *y: onp.stack(y), *maybe_reversed(ys))
        return carry, stacked_y


def top_k(operand: ndarray, k: int) -> tuple[ndarray, ndarray]:
    """Returns top k values and their indices along the last axis of operand."""
    if which_np(operand) is jnp:
        return jax.lax.top_k(operand, k)
    else:
        top_ind = onp.argpartition(operand, -k)[-k:]
        sorted_ind = top_ind[onp.argsort(-operand[top_ind])]
        return operand[sorted_ind], sorted_ind


def while_loop(
    cond_fun: Callable[[X], Any], body_fun: Callable[[X], X], init_val: X
) -> X:
    """Call body_fun while cond_fun is true, starting with init_val."""
    if is_jitted():
        return jax.lax.while_loop(cond_fun, body_fun, init_val)
    else:
        val = init_val
        while cond_fun(val):
            val = body_fun(val)
        return val