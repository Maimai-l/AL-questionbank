"""Topic keyword tables for CAIE 9231 Further Mathematics.

Component -> paper:
  1 = Further Pure Mathematics 1   (75 marks)
  2 = Further Pure Mathematics 2   (75 marks)
  3 = Further Mechanics            (50 marks)
  4 = Further Probability & Statistics (50 marks)
"""

TOPICS = {
"1.1": ("Roots of polynomial equations", {
    3: ["roots of the equation", "symmetric function", "sum of the roots", "product of the roots",
        "substitution to obtain an equation", "alpha beta gamma"],
    2: ["cubic equation", "quartic", "whose roots are", "sigma alpha", "new equation"],
    1: ["polynomial", "roots"]}),
"1.2": ("Rational functions and graphs", {
    3: ["asymptote", "oblique asymptote", "sketch the graph of y =", "rational function"],
    2: ["stationary point", "set of values that y can take", "range of values of y", "curve has"],
    1: ["sketch", "graph"]}),
"1.3": ("Summation of series", {
    3: ["method of differences", "sum of the series", "standard results for", "sigma r",
        "converge", "telescop"],
    2: ["partial fractions", "in terms of n", "limit as n tends", "series"],
    1: ["summation"]}),
"1.4": ("Matrices (FP1)", {
    3: ["determinant", "inverse of the matrix", "singular", "eigenvalue", "eigenvector",
        "characteristic equation", "invariant"],
    2: ["matrix", "transformation", "2 x 2", "3 x 3", "linear transformation"],
    1: ["column vector"]}),
"1.5": ("Polar coordinates", {
    3: ["polar", "r = a", "theta =", "area of the region bounded by the curve and"],
    2: ["cardioid", "tangent at the pole", "half-line"],
    1: ["sketch the curve"]}),
"1.6": ("Vectors (FP1)", {
    3: ["vector product", "cross product", "equation of the plane", "shortest distance",
        "common perpendicular", "skew"],
    2: ["scalar product", "perpendicular distance", "line of intersection", "angle between the plane"],
    1: ["vector", "position vector"]}),
"1.7": ("Proof by induction", {
    3: ["induction", "inductive", "prove by mathematical induction", "true for n = k"],
    2: ["divisible by", "hence prove", "for all positive integers"],
    1: ["prove"]}),

"2.1": ("Hyperbolic functions", {
    3: ["sinh", "cosh", "tanh", "hyperbolic", "artanh", "arsinh", "arcosh"],
    2: ["osborne", "logarithmic form"],
    1: ["exponential form"]}),
"2.2": ("Matrices (FP2)", {
    3: ["eigenvalue", "eigenvector", "diagonalis", "cayley", "hamilton", "characteristic equation"],
    2: ["matrix", "determinant", "inverse of the matrix", "power of the matrix"],
    1: ["transformation"]}),
"2.3": ("Differentiation (FP2)", {
    3: ["maclaurin", "arc length", "surface area of revolution", "derivative of",
        "implicit", "parametric"],
    2: ["differentiate", "series expansion", "in ascending powers"],
    1: ["gradient", "tangent"]}),
"2.4": ("Integration (FP2)", {
    3: ["reduction formula", "arc length", "surface of revolution", "improper integral",
        "approximation to the area"],
    2: ["integrate", "evaluate the integral", "exact value of the integral", "in terms of n"],
    1: ["integral"]}),
"2.5": ("Complex numbers (FP2)", {
    3: ["de moivre", "nth roots", "argand", "root of unity", "modulus-argument",
        "cos n", "sin n"],
    2: ["complex number", "arg(", "|z", "locus", "polar form", "exponential form"],
    1: ["imaginary"]}),
"2.6": ("Differential equations (FP2)", {
    3: ["integrating factor", "complementary function", "particular integral",
        "second order differential equation", "auxiliary equation"],
    2: ["differential equation", "general solution", "particular solution", "substitution"],
    1: ["dy/dx", "d2y/dx2"]}),

"3.1": ("Motion of a projectile", {
    3: ["projectile", "trajectory", "angle of projection", "range on a horizontal plane",
        "equation of the path", "horizontal range"],
    2: ["greatest height", "horizontal component", "vertical component",
        "speed of projection", "angle of elevation"],
    1: ["projected", "time of flight"]}),
"3.2": ("Equilibrium of a rigid body", {
    3: ["centre of mass", "moment about", "rigid body", "topple", "uniform lamina",
        "hinge", "about to tilt"],
    2: ["equilibrium", "rod", "hinged", "reaction at", "suspended"],
    1: ["uniform"]}),
"3.3": ("Circular motion", {
    3: ["circular motion", "angular speed", "conical pendulum", "vertical circle",
        "radius of the circle", "banked"],
    2: ["rotating", "string of length", "horizontal circle", "omega"],
    1: ["circle"]}),
"3.4": ("Hooke's law", {
    3: ["hooke", "modulus of elasticity", "elastic string", "natural length",
        "elastic potential energy", "spring"],
    2: ["extension", "stretched", "compressed", "stiffness"],
    1: ["elastic"]}),
"3.5": ("Linear motion under a variable force", {
    3: ["variable force", "resistance proportional", "dv/dt", "v dv/dx",
        "terminal velocity", "resisting force", "resistance of magnitude",
        "air resistance", "resistive force", "force of magnitude mkv",
        "proportional to the square of the speed", "proportional to its speed"],
    2: ["acceleration is", "in terms of x", "in terms of t", "differential equation",
        "separate the variables"],
    1: ["velocity"]}),
"3.6": ("Momentum (FM)", {
    3: ["impulse", "coefficient of restitution", "oblique impact", "restitution",
        "smooth sphere"],
    2: ["momentum", "collision", "collide", "rebound", "impact"],
    1: ["mass"]}),

"4.1": ("Continuous random variables", {
    3: ["probability density function", "cumulative distribution function",
        "p.d.f", "c.d.f", "median of the distribution"],
    2: ["continuous random variable", "e(x", "var(x", "expectation", "f(x) ="],
    1: ["density"]}),
"4.2": ("Inference using normal and t-distributions", {
    3: ["confidence interval", "t-distribution", "paired sample", "two-sample",
        "pooled estimate", "sample mean", "population mean"],
    2: ["null hypothesis", "alternative hypothesis", "unbiased estimate", "critical value",
        "test statistic"],
    1: ["sample mean"]}),
"4.3": ("Chi-squared tests", {
    3: ["chi", "goodness of fit", "contingency table", "expected frequency",
        "degrees of freedom", "observed frequency", "yates", "combine classes",
        "fits the data", "model is suitable", "test for independence"],
    2: ["independence", "expected value", "row total", "column total",
        "at the 5% significance level", "at the 10% significance level"],
    1: ["frequency"]}),
"4.4": ("Non-parametric tests", {
    3: ["wilcoxon", "sign test", "rank sum", "signed-rank", "non-parametric"],
    2: ["ranks", "median of the population", "paired"],
    1: ["median"]}),
"4.5": ("Probability generating functions", {
    3: ["probability generating function", "p.g.f", "g(t)", "generating function"],
    2: ["sum of independent random variables", "mean and variance from"],
    1: ["derivative at t = 1"]}),
}

# component -> topic codes it may use
COMPONENT_TOPICS = {
    "1": ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7"],
    "2": ["2.1", "2.2", "2.3", "2.4", "2.5", "2.6"],
    "3": ["3.1", "3.2", "3.3", "3.4", "3.5", "3.6"],
    "4": ["4.1", "4.2", "4.3", "4.4", "4.5"],
}

COMPONENT_NAME = {
    "1": "Further Pure Mathematics 1",
    "2": "Further Pure Mathematics 2",
    "3": "Further Mechanics",
    "4": "Further Probability & Statistics",
}

PAPER_TOTAL = {"1": 75, "2": 75, "3": 50, "4": 50}
