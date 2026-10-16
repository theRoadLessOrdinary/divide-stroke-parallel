#!/usr/bin/env python3
"""
Divide Stroke into Parallel Paths

Replaces each selected path with n parallel paths that together cover the
same band its stroke covered. A path with a 24 wide stroke divided into 2
becomes two paths, each with a 12 wide stroke, running 6 to either side of
the original line.

The new paths keep the original's style apart from the stroke width, and are
numbered left to right as seen travelling along the original path.

Where the original bends tighter than a new path's distance from it, that
new path cannot stay parallel and comes to a point there. A message says so
when it happens.
"""
import math

import inkex
from inkex import EffectExtension, PathElement
from inkex.paths import Move, ZoneClose

NODETYPES = "sodipodi:nodetypes"
MAX_DEPTH = 10
MAX_TURN = math.radians(45)


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def add(a, b, k=1.0):
    return (a[0] + k * b[0], a[1] + k * b[1])


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def length(v):
    return math.hypot(v[0], v[1])


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def unit(v):
    n = length(v)
    return (v[0] / n, v[1] / n) if n > 1e-12 else None


def normal(t):
    return (-t[1], t[0])


def point_at(seg, t):
    p0, p1, p2, p3 = seg
    a, b, c = lerp(p0, p1, t), lerp(p1, p2, t), lerp(p2, p3, t)
    return lerp(lerp(a, b, t), lerp(b, c, t), t)


def split(seg, t=0.5):
    p0, p1, p2, p3 = seg
    a, b, c = lerp(p0, p1, t), lerp(p1, p2, t), lerp(p2, p3, t)
    d, e = lerp(a, b, t), lerp(b, c, t)
    m = lerp(d, e, t)
    return (p0, a, d, m), (m, e, c, p3)


def start_tangent(seg):
    p0, p1, p2, p3 = seg
    return unit(sub(p1, p0)) or unit(sub(p2, p0)) or unit(sub(p3, p0))


def end_tangent(seg):
    p0, p1, p2, p3 = seg
    return unit(sub(p3, p2)) or unit(sub(p3, p1)) or unit(sub(p3, p0))


def tangent_at(seg, t):
    left, right = split(seg, t)
    return end_tangent(left) or start_tangent(right)


def start_curvature(seg):
    p0, p1, p2, _ = seg
    d1 = sub(p1, p0)
    n = length(d1)
    if n < 1e-9:
        return 0.0
    d2 = add(sub(p2, p1), d1, -1.0)
    return (2.0 / 3.0) * cross(d1, d2) / n**3


def end_curvature(seg):
    _, p1, p2, p3 = seg
    d1 = sub(p3, p2)
    n = length(d1)
    if n < 1e-9:
        return 0.0
    d2 = add(d1, sub(p2, p1), -1.0)
    return (2.0 / 3.0) * cross(d1, d2) / n**3


class Offsetter:
    """Offsets cubic segments sideways by a fixed distance."""

    def __init__(self, dist, tol):
        self.dist = dist
        self.tol = tol
        self.pinched = False

    def piece(self, seg):
        """One cubic standing in for the offset of seg, or None."""
        t0, t1 = start_tangent(seg), end_tangent(seg)
        if t0 is None or t1 is None:
            return None
        p0, p1, p2, p3 = seg
        f0 = 1.0 - self.dist * start_curvature(seg)
        f1 = 1.0 - self.dist * end_curvature(seg)
        if f0 < 0 or f1 < 0:
            self.pinched = True
            f0, f1 = max(f0, 0.0), max(f1, 0.0)
        q0 = add(p0, normal(t0), self.dist)
        q3 = add(p3, normal(t1), self.dist)
        return (q0, add(q0, sub(p1, p0), f0), add(q3, sub(p3, p2), -f1), q3)

    def good(self, seg, out):
        t0, t1 = start_tangent(seg), end_tangent(seg)
        turn = math.atan2(cross(t0, t1), t0[0] * t1[0] + t0[1] * t1[1])
        if abs(turn) > MAX_TURN:
            return False
        for t in (0.25, 0.5, 0.75):
            tan = tangent_at(seg, t)
            if tan is None:
                continue
            nrm = normal(tan)
            want = add(point_at(seg, t), nrm, self.dist)
            off = sub(point_at(out, t), want)
            if abs(off[0] * nrm[0] + off[1] * nrm[1]) > self.tol:
                return False
        return True

    def offset(self, seg, depth=0):
        """A list of cubics following seg at the offset distance."""
        out = self.piece(seg)
        if out is None:
            return []
        if depth >= MAX_DEPTH or self.good(seg, out):
            return [out]
        a, b = split(seg)
        return self.offset(a, depth + 1) + self.offset(b, depth + 1)


def fmt(v):
    return f"{v:.6f}".rstrip("0").rstrip(".") if "." in f"{v:.6f}" else f"{v:.6f}"


def pt(p):
    return f"{fmt(p[0])},{fmt(p[1])}"


def subpaths(elem):
    """The element's subpaths as (list of cubic segments, closed)."""
    closed = []
    for cmd in elem.path.to_absolute():
        if isinstance(cmd, Move):
            closed.append(False)
        elif isinstance(cmd, ZoneClose) and closed:
            closed[-1] = True
    result = []
    for i, nodes in enumerate(elem.path.to_superpath()):
        is_closed = closed[i] if i < len(closed) else False
        segs = []
        for a, b in zip(nodes, nodes[1:]):
            seg = (tuple(a[1]), tuple(a[2]), tuple(b[0]), tuple(b[1]))
            if length(sub(seg[3], seg[0])) > 1e-9 or length(sub(seg[1], seg[0])) > 1e-9:
                segs.append(seg)
        if is_closed and segs:
            first, last = segs[0][0], segs[-1][3]
            if length(sub(first, last)) > 1e-9:
                segs.append((last, last, first, first))
        if segs:
            result.append((segs, is_closed))
    return result


def offset_d(subs, offsetter):
    """Path data for all subpaths offset by the offsetter's distance."""
    out = []
    for segs, is_closed in subs:
        pieces = []
        for seg in segs:
            pieces.extend(offsetter.offset(seg))
        if not pieces:
            continue
        out.append("M " + pt(pieces[0][0]))
        at = pieces[0][0]
        for q0, q1, q2, q3 in pieces:
            # Corner in the original: bridge the gap between the two sides.
            if length(sub(q0, at)) > 1e-6:
                out.append("L " + pt(q0))
            out.append(f"C {pt(q1)} {pt(q2)} {pt(q3)}")
            at = q3
        if is_closed:
            out.append("Z")
    return " ".join(out)


class DivideStrokeParallel(EffectExtension):
    def add_arguments(self, pars):
        pars.add_argument("--n", type=int, default=2)

    def effect(self):
        n = self.options.n
        if n < 2:
            raise inkex.AbortExtension("The number of parallel paths must be 2 or more.")
        paths = [e for e in self.svg.selection if isinstance(e, PathElement)]
        if not paths:
            raise inkex.AbortExtension("Select one or more paths, then run this again.")

        pinched = []
        for elem in paths:
            elem_id = elem.get_id()
            if elem.get("inkscape:original-d") is not None:
                raise inkex.AbortExtension(
                    f"{elem_id}: has a path effect, which this does not handle."
                )
            style = elem.specified_style()
            width = self.svg.to_dimensionless(style.get("stroke-width", "1"))
            if style.get("stroke", "none") == "none" or width <= 0:
                raise inkex.AbortExtension(
                    f"{elem_id}: has no stroke, so there is no width to divide."
                )
            subs = subpaths(elem)
            if not subs:
                continue

            parent = elem.getparent()
            at = parent.index(elem)
            step = width / n
            for i in range(n):
                offsetter = Offsetter(-width / 2.0 + step * (i + 0.5), width * 0.0005)
                new = elem.copy()
                new.set("id", self.svg.get_unique_id(f"{elem_id}-{i + 1}-"))
                new.set(NODETYPES, None)
                new.set("d", offset_d(subs, offsetter))
                new.style["stroke-width"] = fmt(step)
                parent.insert(at + i, new)
                if offsetter.pinched and elem_id not in pinched:
                    pinched.append(elem_id)
            elem.delete()

        if pinched:
            inkex.errormsg(
                "{}: bends tighter than some of the new paths sit from the "
                "original line, so those paths come to a point at the bend "
                "instead of staying parallel.".format(", ".join(pinched))
            )


if __name__ == "__main__":
    DivideStrokeParallel().run()
