"""
atmosphere_mr.py — Trixel Atmosphere Rasterization

Executes atmospheric effects like Flares. This focuses on rendering 
and compositing math decoupled from paletting or brush shapes.
It will eventually handle Glows, Rays, and Second Flares mathematically.
"""

from typing import Optional
import math

from brush_models_mr import FlareAsset, GradientAsset
from engine_mr import SurfaceBuffer
from trixel_brush_adapter import AssetRegistry


from brush_models_mr import FlareAsset, GradientAsset
from engine_mr import SurfaceBuffer
from trixel_brush_adapter import AssetRegistry


def sample_gradient_rgba(gradient: GradientAsset, t: float) -> tuple[int, int, int, float]:
    """Sample RGBA from a GradientAsset. Returns (R, G, B, A) where R,G,B in 0-255 and A in 0.0-1.0."""
    if not gradient.segments:
        return (0, 0, 0, 0.0)
    t = max(0.0, min(1.0, t))
    for seg in gradient.segments:
        if seg.l <= t <= seg.r:
            width = seg.r - seg.l
            frac = 0.0 if width <= 0.0 else (t - seg.l) / width
            r = int(seg.rgba0[0]*255 + (seg.rgba1[0] - seg.rgba0[0]) * 255 * frac)
            g = int(seg.rgba0[1]*255 + (seg.rgba1[1] - seg.rgba0[1]) * 255 * frac)
            b = int(seg.rgba0[2]*255 + (seg.rgba1[2] - seg.rgba0[2]) * 255 * frac)
            a = seg.rgba0[3] + (seg.rgba1[3] - seg.rgba0[3]) * frac
            return (r, g, b, a)
    s = gradient.segments[-1]
    return (int(s.rgba1[0]*255), int(s.rgba1[1]*255), int(s.rgba1[2]*255), s.rgba1[3])


def _sample_special(name: str, t: float) -> tuple[int, int, int, float]:
    """Handle built-in GFlare gradients like %white, %random, %white_grad."""
    name = name.strip()
    if name == "%white":
        return (255, 255, 255, 1.0)
    elif name == "%random":
        v = int((math.sin(t * 12345.678) * 43758.5453) % 1.0 * 255) # deterministic hash
        return (v, v, v, 1.0)
    elif name in ("%white_grad", "%blue_grad", "%red_grad"):
        a = max(0.0, 1.0 - t)
        if name == "%blue_grad":  return (0, 50, 255, a)
        if name == "%red_grad":   return (255, 0, 0, a)
        return (255, 255, 255, a)
    # fallback
    return (255, 255, 255, 1.0)


def sample_flare_gradient(registry: AssetRegistry, name: str, t: float) -> tuple[int, int, int, float]:
    if name.startswith("%"):
        return _sample_special(name, t)
    grad = registry.gradients.get(name.strip())
    if not grad:
        return (200, 200, 200, 0.5) # visibly broken missing gradient
    return sample_gradient_rgba(grad, t)


def _blend_flare_pixel(buf: SurfaceBuffer, x: int, y: int, r: int, g: int, b: int, alpha_val: float, blend_mode: str) -> None:
    if alpha_val <= 0: return
    base = (y * buf.width + x) * 4
    dst_r = buf.data[base]
    dst_g = buf.data[base + 1]
    dst_b = buf.data[base + 2]
    
    if blend_mode in ("ADDITION", "SCREEN"):
        # simple additive composite
        out_r = min(255, dst_r + int(r * alpha_val))
        out_g = min(255, dst_g + int(g * alpha_val))
        out_b = min(255, dst_b + int(b * alpha_val))
        buf.data[base]   = out_r
        buf.data[base+1] = out_g
        buf.data[base+2] = out_b
        buf.data[base+3] = 255
    else:
        # normal over composite
        sa = alpha_val
        da = buf.data[base+3] / 255.0
        out_a = sa + da * (1.0 - sa)
        if out_a > 0.001:
            inv = da * (1.0 - sa) / out_a
            buf.data[base]   = int(r * sa / out_a + dst_r * inv)
            buf.data[base+1] = int(g * sa / out_a + dst_g * inv)
            buf.data[base+2] = int(b * sa / out_a + dst_b * inv)
            buf.data[base+3] = int(out_a * 255)


def render_flare_glow(
    buf: SurfaceBuffer, registry: AssetRegistry, flare: FlareAsset, cx: float, cy: float, scale: float = 1.0,
) -> None:
    radius = flare.glow_radius * scale
    if radius <= 0: return
    opacity = flare.glow_opacity / 100.0
    r_int = int(math.ceil(radius))
    
    for dy in range(-r_int, r_int + 1):
        y = int(cy) + dy
        if y < 0 or y >= buf.height: continue
        for dx in range(-r_int, r_int + 1):
            x = int(cx) + dx
            if x < 0 or x >= buf.width: continue
            
            d = math.hypot(dx, dy)
            if d > radius: continue
            
            t_rad = d / radius
            ang = math.atan2(dy, dx)
            if ang < 0: ang += 2 * math.pi
            t_ang = ang / (2 * math.pi)

            rr, rg, rb, ra = sample_flare_gradient(registry, flare.glow_radial, t_rad)
            ar, ag, ab, aa = sample_flare_gradient(registry, flare.glow_angular, t_ang)
            
            r = int(rr * ar / 255.0)
            g = int(rg * ag / 255.0)
            b = int(rb * ab / 255.0)
            alpha_val = ra * aa * opacity
            
            _blend_flare_pixel(buf, x, y, r, g, b, alpha_val, flare.glow_blend)


def render_flare_rays(
    buf: SurfaceBuffer, registry: AssetRegistry, flare: FlareAsset, cx: float, cy: float, scale: float = 1.0,
) -> None:
    radius = flare.rays_radius * scale
    if radius <= 0: return
    opacity = flare.rays_opacity / 100.0
    N = flare.rays_count
    if N <= 0 or opacity <= 0: return
    
    thickness = max(0.01, flare.rays_thickness / 100.0)
    rays = []
    base_rot = flare.rays_rotation * math.pi / 180.0
    
    for i in range(N):
        t_ang = i / float(N) if N > 1 else 0.0
        r_sz, g_sz, b_sz, a_sz = sample_flare_gradient(registry, flare.rays_size, t_ang)
        len_mult = (r_sz / 255.0) 
        angle = base_rot + t_ang * 2 * math.pi
        rays.append((angle, len_mult))

    r_int = int(math.ceil(radius))
    for dy in range(-r_int, r_int + 1):
        y = int(cy) + dy
        if y < 0 or y >= buf.height: continue
        for dx in range(-r_int, r_int + 1):
            x = int(cx) + dx
            if x < 0 or x >= buf.width: continue
            
            d = math.hypot(dx, dy)
            if d > radius: continue
            
            ang = math.atan2(dy, dx)
            if ang < 0: ang += 2 * math.pi
            
            ray_intensity = 0.0
            for r_ang, r_len_mult in rays:
                if r_len_mult <= 0: continue
                da = abs(ang - r_ang)
                if da > math.pi: da = 2 * math.pi - da
                
                spike_width = (2 * math.pi / N) * thickness * 0.5
                if da > spike_width: continue
                
                ray_max_d = radius * r_len_mult
                if d > ray_max_d: continue
                
                intensity = (1.0 - da / spike_width) * (1.0 - d / ray_max_d)
                ray_intensity = max(ray_intensity, intensity)
            
            if ray_intensity <= 0: continue
            
            t_rad = d / radius
            t_ang = ang / (2 * math.pi)
            rr, rg, rb, ra = sample_flare_gradient(registry, flare.rays_radial, t_rad)
            ar, ag, ab, aa = sample_flare_gradient(registry, flare.rays_angular, t_ang)
            
            r = int(rr * ar / 255.0)
            g = int(rg * ag / 255.0)
            b = int(rb * ab / 255.0)
            alpha_val = ra * aa * opacity * ray_intensity
            
            _blend_flare_pixel(buf, x, y, r, g, b, alpha_val, flare.rays_blend)


def render_flare_secondaries(
    buf: SurfaceBuffer, registry: AssetRegistry, flare: FlareAsset, cx: float, cy: float, scale: float = 1.0,
) -> None:
    radius = flare.sec_radius * scale
    if radius <= 0: return
    opacity = flare.sec_opacity / 100.0
    if opacity <= 0: return

    n_ghosts = 6
    base_rot = flare.sec_rotation * math.pi / 180.0
    
    for i in range(n_ghosts):
        t = i / float(n_ghosts - 1) if n_ghosts > 1 else 0.5 
        r_sz, _, _, a_sz = sample_flare_gradient(registry, flare.sec_size, t)
        ghost_scale = max(0.05, (r_sz / 255.0) * 0.5) 
        
        ghost_r = radius * ghost_scale
        if ghost_r <= 0: continue
        
        dist_along = (t - 0.5) * 4.0 * radius 
        gx = cx + math.cos(base_rot) * dist_along
        gy = cy + math.sin(base_rot) * dist_along
        
        r_int = int(math.ceil(ghost_r))
        for dy in range(-r_int, r_int + 1):
            y = int(gy) + dy
            if y < 0 or y >= buf.height: continue
            for dx in range(-r_int, r_int + 1):
                x = int(gx) + dx
                if x < 0 or x >= buf.width: continue
                
                d = math.hypot(dx, dy)
                if d > ghost_r: continue
                
                t_rad = d / ghost_r
                ang = math.atan2(dy, dx)
                if ang < 0: ang += 2 * math.pi
                t_ang = ang / (2 * math.pi)
                
                rr, rg, rb, ra = sample_flare_gradient(registry, flare.sec_radial, t_rad)
                ar, ag, ab, aa = sample_flare_gradient(registry, flare.sec_angular, t_ang)
                
                r = int(rr * ar / 255.0)
                g = int(rg * ag / 255.0)
                b = int(rb * ab / 255.0)
                alpha_val = ra * aa * opacity
                
                _blend_flare_pixel(buf, x, y, r, g, b, alpha_val, flare.sec_blend)


def render_flare(
    buf: SurfaceBuffer, registry: AssetRegistry, flare_name: str, cx: float, cy: float, scale: float = 1.0,
) -> None:
    """Entry point: Renders glow, rays, and second flares exactly like GFlare."""
    flare = registry.flares.get(flare_name)
    if not flare:
        print(f"Atmosphere: Flare {flare_name!r} not found in registry.flares.")
        return
    
    render_flare_glow(buf, registry, flare, cx, cy, scale)
    render_flare_rays(buf, registry, flare, cx, cy, scale)
    render_flare_secondaries(buf, registry, flare, cx, cy, scale)
