"""Tiny numpy z-buffer renderer for documentation images.

No OpenGL/display needed, so it runs anywhere (including CI). Orthographic
camera, flat shading, plus an outline pass on depth and normal edges so the
pictures read like clean technical illustrations.
"""
from __future__ import annotations

from math import cos, radians, sin

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def _tris(shape, tol):
    verts, faces = shape.tessellate(tol, 0.3)
    if not faces:
        return np.zeros((0, 3, 3))
    v = np.array([[p.X, p.Y, p.Z] for p in verts])
    return v[np.array(faces)]


def _camera(elev, azim):
    e, a = radians(elev), radians(azim)
    fwd = -np.array([cos(e) * cos(a), cos(e) * sin(a), sin(e)])  # view dir
    up0 = np.array([0, 0, 1.0])
    right = np.cross(fwd, up0)
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    return right, up, fwd


def render(items, path, elev=22, azim=-60, title=None, tol=0.4, px=1000,
           ss=2, margin=0.06):
    """items: list of (shape, (r,g,b)) in world coordinates."""
    right, up, fwd = _camera(elev, azim)
    light = -fwd * 0.6 + up * 0.5 - right * 0.4
    light /= np.linalg.norm(light)

    tris, cols, ids = [], [], []
    for k, (shape, rgb) in enumerate(items):
        t = _tris(shape, tol)
        if not len(t):
            continue
        tris.append(t)
        cols.append(np.tile(np.array(rgb, float), (len(t), 1)))
        ids.append(np.full(len(t), k))
    T = np.concatenate(tris)
    C = np.concatenate(cols)
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    ln = np.linalg.norm(n, axis=1)
    ok = ln > 1e-9
    T, C, n = T[ok], C[ok], n[ok] / ln[ok, None]
    # two-sided lighting
    facing = np.where((n @ fwd)[:, None] > 0, -n, n)
    shade = 0.38 + 0.62 * np.clip(facing @ light, 0, 1)
    C = np.clip(C * shade[:, None], 0, 1)

    # project
    P = T.reshape(-1, 3)
    sx, sy, sz = P @ right, P @ up, P @ fwd
    W = px * ss
    lo = np.array([sx.min(), sy.min()])
    hi = np.array([sx.max(), sy.max()])
    span = (hi - lo).max() * (1 + 2 * margin)
    ctr = (lo + hi) / 2
    X = ((sx - ctr[0]) / span + 0.5) * W
    Y = (0.5 - (sy - ctr[1]) / span) * W
    X, Y, Z = X.reshape(-1, 3), Y.reshape(-1, 3), sz.reshape(-1, 3)

    zbuf = np.full((W, W), np.inf)
    img = np.ones((W, W, 3))
    nbuf = np.zeros((W, W, 3))
    for i in range(len(X)):
        x, y, z = X[i], Y[i], Z[i]
        x0, x1 = int(max(0, np.floor(x.min()))), int(min(W - 1, np.ceil(x.max())))
        y0, y1 = int(max(0, np.floor(y.min()))), int(min(W - 1, np.ceil(y.max())))
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(d) < 1e-12:
            continue
        w0 = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / d
        w1 = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / d
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            continue
        zz = w0 * z[0] + w1 * z[1] + w2 * z[2]
        sub = zbuf[y0:y1 + 1, x0:x1 + 1]
        upd = inside & (zz < sub)
        sub[upd] = zz[upd]
        img[y0:y1 + 1, x0:x1 + 1][upd] = C[i]
        nbuf[y0:y1 + 1, x0:x1 + 1][upd] = n[i]

    # outlines: depth discontinuities + normal creases
    fin = np.isfinite(zbuf)
    zf = np.where(fin, zbuf, zbuf[fin].max() + 1000 if fin.any() else 0)
    edge = np.zeros((W, W), bool)
    thr = span * 0.004
    for dy, dx in ((0, 1), (1, 0)):
        a = zf[: W - dy, : W - dx]
        b = zf[dy:, dx:]
        e = np.abs(a - b) > thr
        na = nbuf[: W - dy, : W - dx]
        nb = nbuf[dy:, dx:]
        e |= (np.sum(na * nb, axis=-1) < 0.85) & fin[: W - dy, : W - dx] & fin[dy:, dx:]
        edge[: W - dy, : W - dx] |= e
    img[edge] = img[edge] * 0.25

    im = Image.fromarray((img * 255).astype(np.uint8)).resize((px, px), Image.LANCZOS)
    if title:
        dr = ImageDraw.Draw(im)
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", 26)
        except OSError:
            font = ImageFont.load_default()
        dr.text((24, 18), title, fill=(40, 40, 40), font=font)
    im.save(path)
