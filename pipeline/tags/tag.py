#!/usr/bin/env python3
"""Assign syllabus topic codes to each question.

Scored keyword matching, scoped to the component's own topic list (a Paper 1
question can only be 1.x). Evidence is the question text plus its mark scheme,
which often names the technique more explicitly than the question does.
Returns a ranked list, because real questions frequently span two subtopics.
"""
import json, re, sys, collections

# weight 3 = near-decisive, 2 = strong, 1 = weak corroboration
TOPICS = {
"1.1": ("Quadratics", {3:["discriminant","completing the square","repeated root","quadratic in"],
                       2:["complete the square","quadratic equation","quadratic inequality","real roots","distinct roots"],
                       1:["simultaneous","vertex","factoris"]}),
"1.2": ("Functions", {3:["inverse function","one-one","composite function","domain of","range of"],
                      2:["f -1","fg(x)","gf(x)","reflection in the line y = x","codomain"],
                      1:["translation","stretch","transformation","domain","range","sketch the graph of y ="]}),
"1.3": ("Coordinate geometry", {3:["equation of the circle","centre of the circle","perpendicular bisector","midpoint of"],
                                2:["gradient of the line","equation of the line","radius","tangent to the circle","coordinates of the point of intersection"],
                                1:["perpendicular","parallel","straight line","distance between"]}),
"1.4": ("Circular measure", {3:["arc length","sector","radian"],
                             2:["shaded region","perimeter of the region","area of the sector"],
                             1:["arc","angle in radians"]}),
"1.5": ("Trigonometry", {3:["tan x","sin x","cos x","sin 2","cos 2","tan 2","trigonometric equation"],
                         2:["identity","trigonometric","degrees","interval 0","exact value of","solve the equation"],
                         1:["amplitude","period","sketch"]}),
"1.6": ("Series", {3:["arithmetic progression","geometric progression","binomial expansion","sum to infinity","common ratio","common difference"],
                   2:["first term","nth term","sum of the first","coefficient of x","expansion of"],
                   1:["convergent","progression","series"]}),
"1.7": ("Differentiation", {3:["stationary point","dy/dx","rate of change","increasing function","decreasing function","second derivative"],
                            2:["gradient of the curve","tangent to the curve","normal to the curve","maximum","minimum","differentiate"],
                            1:["chain rule","gradient"]}),
"1.8": ("Integration", {3:["volume of revolution","area of the region","definite integral","integrate","constant of integration"],
                        2:["rotated through","about the x-axis","about the y-axis","area enclosed","find the equation of the curve"],
                        1:["integral"]}),

"3.1": ("Algebra", {3:["partial fractions","remainder theorem","factor theorem","modulus","|x","divided by"],
                    2:["quotient","remainder","expansion of","ascending powers","valid for"],
                    1:["polynomial","cubic","quartic"]}),
"3.2": ("Logarithmic and exponential functions", {3:["logarithm","exponential","straight line graph","ln y =","lg y","laws of logarithms"],
                                                  2:["log","natural logarithm","lg","gradient and intercept","e x","in indices"],
                                                  1:["ln","index","indices"]}),
"3.3": ("Trigonometry", {3:["r sin","r cos","double angle","cosec","sec","cot","compound angle"],
                         2:["identity","prove that","trigonometric equation","exact value","in the form r"],
                         1:["degrees","interval"]}),
"3.4": ("Differentiation", {3:["implicit","parametric","product rule","quotient rule","dy/dx"],
                            2:["stationary point","tangent","normal","differentiate","in terms of t"],
                            1:["gradient","derivative"]}),
"3.5": ("Integration", {3:["integration by parts","by parts","using the substitution","definite integral","trapezium"],
                        2:["integrate","area of the region","exact value of the integral","volume","evaluate the integral"],
                        1:["integral","integration"]}),
"3.6": ("Numerical solution of equations", {3:["iterative formula","iteration","converge","successive approximation"],
                                            2:["root of the equation","correct to 3 decimal places","sign change","show that the equation has"],
                                            1:["approximation"]}),
"3.7": ("Vectors", {3:["position vector","scalar product","direction vector","skew","unit vector"],
                    2:["vector","angle between","perpendicular to","point of intersection of the lines"],
                    1:["magnitude"]}),
"3.8": ("Differential equations", {3:["differential equation","separate the variables","separating the variables","dx/dt","dt =","rate of increase","rate of decrease"],
                                   2:["general solution","particular solution","proportional to","satisfy the","in terms of t"],
                                   1:["rate of","proportional"]}),
"3.9": ("Complex numbers", {3:["complex number","argand","argument of","modulus of z","conjugate"],
                            2:["arg(","|z","real and imaginary","locus","polar form"],
                            1:["imaginary"]}),

"4.1": ("Forces and equilibrium", {3:["equilibrium","coefficient of friction","normal component","frictional force","limiting","resultant of the","coplanar","three forces","remains at rest"],
                                   2:["in equilibrium","rough","resolve","about to slip","normal reaction","at rest","resultant"],
                                   1:["smooth","force","angle to the horizontal"]}),
"4.2": ("Kinematics of motion in a straight line", {3:["velocity-time graph","displacement-time","deceleration","comes to instantaneous rest"],
                                                    2:["velocity","acceleration","displacement","constant acceleration","travels"],
                                                    1:["speed","distance"]}),
"4.3": ("Momentum", {3:["momentum","coalesce","collide","after the collision"],
                     2:["impact","conservation of","two particles"],
                     1:["mass"]}),
"4.4": ("Newton's laws of motion", {3:["newton","connected particles","pulley","tow-bar","thrust","acceleration of the particle"],
                                    2:["inextensible string","inclined plane","tension","acceleration","driving force"],
                                    1:["resistance","weight"]}),
"4.5": ("Energy, work and power", {3:["work done","kinetic energy","potential energy","power","conservation of energy","work-energy","gain in kinetic","loss in kinetic","work done against"],
                                   2:["joules","watts","rate of working","total work"],
                                   1:["energy","driving force"]}),

"5.1": ("Representation of data", {3:["stem-and-leaf","box-and-whisker","histogram","cumulative frequency","standard deviation","interquartile"],
                                   2:["median","mean of","quartile","frequency","coded","class"],
                                   1:["data","spread"]}),
"5.2": ("Permutations and combinations", {3:["arrangements","permutation","how many different","selections","letters of the word"],
                                          2:["chosen from","in a line","order","committee","different ways"],
                                          1:["select"]}),
"5.3": ("Probability", {3:["tree diagram","conditional probability","independent events","mutually exclusive"],
                        2:["at random","exclusive","given that"],
                        1:["probability that","find the probability","chance"]}),
"5.4": ("Discrete random variables", {3:["probability distribution","expectation","binomial distribution","geometric distribution","var(x","geo(","first success","b(","on the nth"],
                                      2:["e(x","random variable x","distribution table","success","trials","independent trials"],
                                      1:["variance"]}),
"5.5": ("The normal distribution", {3:["normal distribution","standardis","continuity correction","approximation to the binomial"],
                                    2:["n(","mean and standard deviation","normally distributed","z ="],
                                    1:["approximation"]}),
}

BY_COMPONENT = collections.defaultdict(list)
for code in TOPICS:
    BY_COMPONENT[code.split(".")[0]].append(code)


def score(text, code):
    _, groups = TOPICS[code]
    s = 0
    for w, kws in groups.items():
        for kw in kws:
            if kw in text:
                s += w
    return s


def tag(q, ms_text=""):
    text = (q["text"] + " " + ms_text).lower()
    text = re.sub(r"\s+", " ", text)
    scored = [(score(text, c), c) for c in BY_COMPONENT[q["component"]]]
    scored.sort(reverse=True)
    top = [c for s, c in scored if s > 0][:3]
    best = scored[0]
    return {
        "topic": best[1] if best[0] > 0 else None,
        "topic_name": TOPICS[best[1]][0] if best[0] > 0 else None,
        "topic_score": best[0],
        "topics_all": top,
        "topic_margin": best[0] - (scored[1][0] if len(scored) > 1 else 0),
        "topic_confident": best[0] >= 5 and (len(scored) < 2 or best[0] >= scored[1][0] + 3),
    }


if __name__ == "__main__":
    Q = json.load(open(sys.argv[1]))
    M = json.load(open(sys.argv[2]))
    mk = {(m["series"], m["component"], m["variant"], m["q"]): m for m in M}
    for q in Q:
        m = mk.get((q["series"], q["component"], q["variant"], q["q"]))
        q.update(tag(q, m["ms_text"] if m else ""))
    json.dump(Q, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
    untagged = sum(1 for q in Q if not q["topic"])
    conf = sum(1 for q in Q if q["topic_confident"])
    print(f"tagged {len(Q)-untagged}/{len(Q)}  untagged={untagged}  confident={conf} ({conf/len(Q)*100:.0f}%)")
    for comp in "1345":
        c = collections.Counter(q["topic"] for q in Q if q["component"] == comp)
        print(f" comp {comp}: " + ", ".join(f"{k}:{v}" for k, v in sorted(c.items(), key=lambda x: str(x[0]))))
