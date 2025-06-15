# Alphabet of Powers (`ltrs`) Examples

This page showcases various examples of using the `ltrs` calculator, demonstrating different features and capabilities. All examples assume the default base 10 unless otherwise specified by a `/setbase` command.

## Basic Operations

```
aop(base=10)> a * b
c
aop(base=10)> c / a
b
aop(base=10)> b^3  # (10^2)^3 = 10^6
f
aop(base=10)> 2a * 5c # (2*10) * (5*1000) = 20 * 5000 = 100000
e
```

## Word Evaluations

```
aop(base=10)> cat  # c(3) + a(1) + t(20) = 24
x
aop(base=10)> dog  # d(4) + o(15) + g(7) = 26
z
aop(base=10)> alphabet # 1+12+16+8+1+2+5+20 = 65
AlphaZone(10^65)
```

## Using Functions

Angles for trigonometric functions are in radians.

```
aop(base=10)> sqrt(d)  # sqrt(10^4) = 10^2
b
aop(base=10)> log(c)   # log10(10^3)
3
aop(base=10)> ln(#e)
1
aop(base=10)> log2(16a) # log2(16*10) = log2(160)
7.321928095
aop(base=10)> sin(#pi / 2)
1
aop(base=10)> cos(0)
1
aop(base=10)> tan(#pi / 4)
1
```

## Working with Variables

```
aop(base=10)> radius = 2.5b # radius = 2.5 * 10^2 = 250
2.5 * b
aop(base=10)> area = #pi * radius^2
196349.5408
aop(base=10)> /vars
Current Variables:
Variable | Value
---------|----------------
area     | 196349.5408
radius   | 2.5 * b
```

## Changing Base

```
aop(base=10)> /setbase 2
Base changed to 2
Variables have been cleared.
aop(base=2)> a * b   # 2^1 * 2^2 = 2^3
c
aop(base=2)> c + 0   # Numerical value of c in base 2
8
aop(base=2)> 10 + 10 # Numerical addition
20
```

## Graphing Examples

(Requires `matplotlib` installed: `pip install matplotlib numpy`)

Plotting a simple parabola:

```
aop(base=10)> /graph x^2 for x from -5 to 5
```

(A plot window will appear)

Plotting an AoP expression with y-axis log scale:

```
aop(base=10)> /graph b^x for x from 0 to 3 --logy
```

(Shows `100^x` as a straight line on a semi-log plot)

Plotting a sine wave using AoP constants for the range:

```
aop(base=10)> /graph sin(t) for t from 0 to #pi * 2
```

Plotting with an existing variable:

```
aop(base=10)> my_offset = a
a
aop(base=10)> /graph x^2 + my_offset for x from -10 to 10
```

## Saving and Loading Variables

```
aop(base=10)> val1 = a^2 * b
d
aop(base=10)> val2 = #e + #phi
4.336260118
aop(base=10)> /savevars my_session
Variables saved to my_session.json
aop(base=10)> /clear val1
Variables 'val1' cleared.
aop(base=10)> /vars
Current Variables:
Variable | Value
---------|-------------
val2     | 4.336260118
aop(base=10)> /loadvars my_session
Loaded 2 variables from my_session.json.
aop(base=10)> /vars
Current Variables:
Variable | Value
---------|-------------
val1     | d
val2     | 4.336260118
```

More examples can be found in the main `README.md` file.
