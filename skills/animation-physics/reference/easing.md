# Easing Functions — Mathematical Reference

## Common GSAP Easings

### Linear
```
progress = t
```
Constant speed. No acceleration.

### Power1 (Ease)
```
progress = t²
```
Slow start, fast end. Gentle deceleration.

### Power2 (Ease)
```
progress = t³
```
More pronounced deceleration.

### Power2.inOut
```
if t < 0.5:
    progress = 2 * t²
else:
    progress = 1 - (-2 * t + 2)² / 2
```
Accelerate in first half, decelerate in second half.

### Power3.inOut
```
if t < 0.5:
    progress = 4 * t³
else:
    progress = 1 - (-2 * t + 2)³ / 2
```
More aggressive acceleration/deceleration.

### Back
```
progress = c1 * t³ + c1 * t² + t
where c1 = 1.70158
```
Overshoots target, then settles.

### Elastic
```
progress = (2^(-10*t)) * sin((t*10 - 0.75) * (2π/3)) + 1
```
Bouncy, spring-like motion.

## Time→Progress Lookup Table (power2.inOut)

| Time (s) | Duration | t | Progress | ΔY (270px total) |
|----------|----------|---|----------|------------------|
| 0.000 | 0.300 | 0.000 | 0.000 | 0px |
| 0.030 | 0.300 | 0.100 | 0.020 | 5px |
| 0.060 | 0.300 | 0.200 | 0.080 | 22px |
| 0.090 | 0.300 | 0.300 | 0.180 | 49px |
| 0.120 | 0.300 | 0.400 | 0.320 | 86px |
| 0.150 | 0.300 | 0.500 | 0.500 | 135px |
| 0.180 | 0.300 | 0.600 | 0.680 | 184px |
| 0.210 | 0.300 | 0.700 | 0.820 | 221px |
| 0.240 | 0.300 | 0.800 | 0.920 | 248px |
| 0.270 | 0.300 | 0.900 | 0.980 | 265px |
| 0.300 | 0.300 | 1.000 | 1.000 | 270px |

## Scale Interpolation

For uniform scale from `s1` to `s2`:
```
currentScale = s1 + (s2 - s1) * progress
```

Example (1.0 → 0.833):
| Progress | Scale |
|----------|-------|
| 0.00 | 1.000 |
| 0.25 | 0.958 |
| 0.50 | 0.917 |
| 0.75 | 0.875 |
| 1.00 | 0.833 |

## Velocity Calculation

Instantaneous velocity at time t:
```
velocity = derivative(progress) / duration
```

For power2.inOut, peak velocity occurs at t=0.5 (midpoint):
```
peak_velocity ≈ 2 × total_distance / duration
             ≈ 2 × 270px / 0.3s
             ≈ 1800 px/s
```

Average velocity:
```
avg_velocity = total_distance / duration
             = 270px / 0.3s
             = 900 px/s
```

## Visual Perception Thresholds

| Velocity | Perception |
|----------|------------|
| < 100 px/s | Slow, noticeable crawl |
| 100-400 px/s | Comfortable, readable |
| 400-800 px/s | Fast but smooth |
| 800-1200 px/s | Quick, motion blur territory |
| > 1200 px/s | Very fast, may need motion cues |

## Duration Guidelines

| Animation Type | Recommended Duration |
|---------------|---------------------|
| Micro-interaction (button hover) | 0.1-0.2s |
| Page transition | 0.3-0.5s |
| Modal open/close | 0.2-0.3s |
| Complex choreography | 0.5-1.0s |
| Loading indicator | 1.0-2.0s (loop) |

**Rule of thumb:** Duration should match the cognitive load. Quick actions = fast animation. Complex transitions = longer animation.
