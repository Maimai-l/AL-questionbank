# Roots of polynomial equations

<!-- Cambridge International AS  A Level Further Mathematics Coursebook (Lee Mckelvey Martin Crozier) .pdf p13-27 -->

<!-- page 13 -->

<div style="text-align: center;"><img src="imgs/img_in_image_box_6_6_1186_770.jpg" alt="Image" width="96%" /></div>


# Chapter 1 Roots of polynomial equations

In this chapter you will learn how to:

recall and use the relations between the roots and coefficients of polynomial equations

use a substitution to obtain an equation whose roots are related in a simple way to those of the original equation.

<div style="text-align: center;"><img src="imgs/img_in_image_box_5_1135_1178_1567.jpg" alt="Image" width="95%" /></div>

<!-- page 14 -->

## PREREQUISITE KNOWLEDGE


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Where it comes from</td><td style='text-align: center; word-wrap: break-word;'>What you should be able to do</td><td style='text-align: center; word-wrap: break-word;'>Check your skills</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>AS &amp; A Level Mathematics Pure Mathematics 1, Chapter 2</td><td style='text-align: center; word-wrap: break-word;'>Use simple substitutions to make another variable the subject.</td><td style='text-align: center; word-wrap: break-word;'>1 Rewrite the following equations in terms of the new variable.
 $ a x^{2} - 3x + 5 = 0 $,  $ y = x - 2 $
 $ b x^{3} + 2x^{2} - 4 = 0 $,  $ y = \frac{2}{x} $
 $ c x^{3} - 3x + 7 = 0 $,  $ y = \frac{1}{x+1} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>AS &amp; A Level Mathematics Probability &amp; Statistics 1, Chapter 2</td><td style='text-align: center; word-wrap: break-word;'>Work with basic sigma notation, such as  $ \Sigma x $ and  $ \Sigma x^{2} $.</td><td style='text-align: center; word-wrap: break-word;'>2 Evaluate the following.
 $ a \sum_{r=1}^{10} r $
 $ b \sum_{r=1}^{10} 3 $
 $ c \sum_{r=1}^{10} (r+2) $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>AS &amp; A Level Mathematics Pure Mathematics 1, Chapter 6</td><td style='text-align: center; word-wrap: break-word;'>Work with basic recurrence relations.</td><td style='text-align: center; word-wrap: break-word;'>3 Write the first six terms for the following relations.
 $ a u_{n+1} = 3u_n + 2 $,  $ u_1 = 1 $
 $ b u_{n+2} = 2u_{n+1} - u_n + 5 $,  $ u_1 = 1 $,  $ u_2 = 1 $</td></tr></table>

## What are polynomials?

Polynomials are algebraic expressions made up of one or more variables and a sum of terms involving non-negative integer powers of variables. For example,  $ 2x^{2}-3xy+5x $ is a polynomial, but neither  $ 3x^{\frac{1}{2}} $ nor  $ \frac{5}{y} $ are polynomials. Engineers use polynomials to ensure that a new building can withstand the force of an earthquake. Medical researchers use them to model the behaviour of bacterial colonies.

We already know how to divide a polynomial by a linear term and identify the quotient and any remainder. We have worked with simpler polynomials when completing the square of a quadratic or finding the discriminant. Now we will extend this knowledge to work with higher powers. We will also use algebraic manipulation to understand the conditions for complex solutions and to combine polynomials with summation notation and recurrence relations.

In this chapter, we will look at ways to find characteristics of polynomials, finding the sum and product of roots as well as other properties linked to their roots.

### 1.1 Quadratics

To begin with, let us look back at the quadratic equation  $ ax^{2} + bx + c = 0 $. If we write this in the form  $ x^{2} + \frac{b}{a}x + \frac{c}{a} = 0 $, then we can compare it to the form  $ (x - \alpha)(x - \beta) = 0 $. This shows that the sum of the roots is  $ \alpha + \beta = -\frac{b}{a} $, and the product of the roots is  $ \alpha\beta = \frac{c}{a} $, as shown in Key point 1.1. Hence, we can say that  $ x^{2} - (\alpha + \beta)x + \alpha\beta = 0 $.

<!-- page 15 -->

<div style="text-align: center;"><img src="imgs/img_in_image_box_39_147_76_178.jpg" alt="Image" width="3%" /></div>


### KEY POINT 1.1

If we write a quadratic equation in the form  $ x^2 + \frac{b}{a}x + \frac{c}{a} = 0 $, the sum of the roots is  $ \alpha + \beta = -\frac{b}{a} $. The product of the roots of the quadratic equation is  $ \alpha\beta = \frac{c}{a} $.

### WORKED EXAMPLE 1.1

The quadratic equation  $ x^{2}-2px+p=0 $ is such that one root is three times the value of the other root. Find p.

## Answer

 $$ \alpha+3\alpha=2p $$ 

Using  $ \alpha + \beta = -\frac{b}{a} $

 $$ p=2\alpha $$ 

 $$ \alpha\times3\alpha=p $$ 

Using  $ \alpha\beta=\frac{c}{a} $

 $$ p=3\alpha^{2} $$ 

 $$ \frac{p}{3}=\left(\frac{p}{2}\right)^{2} $$ 

Equate the two results.

 $$ 4p-3p^{2}=0 $$ 

Cross multiply.

 $$ p=\frac{4}{3} $$ 

Factorise and omit the case when p = 0.

Using $\alpha + \beta = -\frac{b}{a}$ and $\alpha\beta = \frac{c}{a}$, we can begin to define many other results, but first we must introduce some new notation. The sum of the roots can be written as $\Sigma\alpha = \alpha + \beta$ and the product can be written as $\Sigma\alpha\beta = \alpha\beta$.

Let us consider how to determine the value of $\alpha^{2} + \beta^{2}$. The natural first step is to expand $(\alpha + \beta)^{2} = \alpha^{2} + \beta^{2} + 2\alpha\beta$. Hence, we can say that $\alpha^{2} + \beta^{2} = (\Sigma\alpha)^{2} - 2\Sigma\alpha\beta$. We denote $\alpha^{2} + \beta^{2}$ as $\Sigma\alpha^{2}$.

Next, look at $(\alpha - \beta)^2$. Again, expanding the brackets is a good start. So $(\alpha - \beta)^2 = \alpha^2 + \beta^2 - 2\alpha\beta$. Hence, we can see that $(\alpha - \beta)^2 = \Sigma\alpha^2 - 2\Sigma\alpha\beta$.

We can write  $ \frac{1}{\alpha} + \frac{1}{\beta} $ as  $ \Sigma\frac{1}{\alpha} $. How do we find the sum of  $ \frac{1}{\alpha} + \frac{1}{\beta} $? First, combine the two fractions to get  $ \frac{\alpha + \beta}{\alpha\beta} $. We can see that this is  $ \frac{\Sigma\alpha}{\Sigma\alpha\beta} $. Similarly, we can write  $ \frac{1}{\alpha^2} + \frac{1}{\beta^2} $ as  $ \frac{1}{\alpha^2} $ and we can show  $ \frac{1}{\alpha^2} + \frac{1}{\beta^2} = \frac{\Sigma\alpha^2}{(\Sigma\alpha\beta)^2} $.

Note the difference between  $ (\Sigma\alpha)^2 $ and  $ \Sigma\alpha^2 $.



<div style="text-align: center;"><img src="imgs/img_in_image_box_861_974_901_1010.jpg" alt="Image" width="3%" /></div>


## TIP

<!-- page 16 -->

### WORKED EXAMPLE 1.2


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Find  $ \alpha^{3} + \beta^{3} $ in summation notation.</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Answer\n $ (\alpha + \beta)^{3} = \alpha^{3} + 3\alpha^{2}\beta + 3\alpha\beta^{2} + \beta^{3} $</td><td style='text-align: center; word-wrap: break-word;'>Use the binomial expansion for  $ (x + y)^{n} $.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ \alpha^{3} + \beta^{3} = (\alpha + \beta)^{3} - 3\alpha\beta(\alpha + \beta) $</td><td style='text-align: center; word-wrap: break-word;'>Rearrange and factorise.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ \Sigma\alpha^{3} = (\Sigma\alpha)^{3} - 3\Sigma\alpha\beta\Sigma\alpha $</td><td style='text-align: center; word-wrap: break-word;'>Sum for each possible root.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>Alternatively, use  $ -3\Sigma\alpha^{2}\beta $ in place of  $ -3\Sigma\alpha\beta\Sigma\alpha $. However, it is not as easy to calculate with this form.</td></tr></table>

Some of the results found can be written in alternative forms, using a recurrence relation such as  $ S_{n} = \alpha^{n} + \beta^{n} $. If we consider the quadratic equation  $ x^{2} + 5x + 7 = 0 $, we can see that  $ \alpha + \beta = -5 $. This result can also be viewed as  $ S_{1} = \alpha + \beta = -5 $. To determine the value of  $ \alpha^{2} + \beta^{2} $, we can approach this from another angle.

Given that $\alpha$ and $\beta$ are roots of the original equation, we can state that $\alpha^{2} + 5\alpha + 7 = 0$ and $\beta^{2} + 5\beta + 7 = 0$. Adding these together gives the result $(\alpha^{2} + \beta^{2}) + 5(\alpha + \beta) + 14 = 0$ or $S_{2} + 5S_{1} + 14 = 0$. Now we can work out the value of $S_{2}$ or $\alpha^{2} + \beta^{2}$. From $S_{2} + 5S_{1} + 14 = 0$ and $S_{1} = -5$ we have $S_{2} = \alpha^{2} + \beta^{2} = 11$. Note this could also have been found from $\alpha^{2} + \beta^{2} = (\Sigma\alpha)^{2} - 2\Sigma\alpha\beta = (-5)^{2} - 2(7) = 11$.

### WORKED EXAMPLE 1.3


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Given that  $ 2x^{2} + 3x - 2 = 0 $ has roots  $ \alpha $,  $ \beta $, find the values of  $ \alpha^{2} + \beta^{2} $ and  $ \alpha^{3} + \beta^{3} $.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Answer</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ 2\alpha^{2} + 3\alpha - 2 = 0 $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ 2\beta^{2} + 3\beta - 2 = 0 $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ \Rightarrow 2S_{2} + 3S_{1} - 4 = 0 $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ S_{1} = -\frac{3}{2} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ S_{2} = \alpha^{2} + \beta^{2} = \frac{17}{4} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ 2x^{2} + 3x - 2 = 0 $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ \Rightarrow 2x^{3} + 3x^{2} - 2x = 0 $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ \Rightarrow 2S_{3} + 3S_{2} - 2S_{1} = 0 $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ S_{3} = \alpha^{3} + \beta^{3} = -\frac{63}{8} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Add the two equations to get the recurrence form.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>State  $ S_{1} = -\frac{b}{a} $ from the original quadratic equation.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Substitute the  $ S_{1} $ value into the equation.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Multiply by x.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Add  $ 2\alpha^{3} + 3\alpha^{2} - 2\alpha = 0 $ and  $ 2\beta^{3} + 3\beta^{2} - 2\beta = 0 $.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Use the values of  $ S_{1} $ and  $ S_{2} $.</td></tr></table>

<!-- page 17 -->

1 Each of the following quadratic equations has roots  $ \alpha $,  $ \beta $. Find the values of  $ \alpha + \beta $ and  $ \alpha\beta $.

a  $ x^{2}+5x+9=0 $ b  $ x^{2}-4x+8=0 $ c  $ 2x^{2}+3x-7=0 $

2 Given that  $ 3x^{2} + 4x + 12 = 0 $ has roots  $ \alpha, \beta $, find:

a  $ \alpha + \beta $ and  $ \alpha\beta $

b  $ \alpha^{2} + \beta^{2} $

3  $ x^{2}-(2+p)x+(7+p)=0 $ has roots that differ by 1. Find the value of p given that p>0.

4 If $a+b=-3$ and $a^{2}+b^{2}=7$, find the value of $ab$ and, hence, write down a quadratic equation with roots $a$ and $b$.

P 5 If  $ x^{2} + bx + c = 0 $ has roots  $ \alpha $ and  $ \beta $, prove that:

a if  $ \alpha = 3\beta $, then  $ b^{2} = \frac{16}{3}c $

b if  $ \alpha = \beta - 2 $, then  $ b^2 = 4(c + 1) $.

PS 6 You are given the quadratic equation  $ px^2 + qx - 16 = 0 $, which has roots  $ \alpha $ and  $ \beta $. Given also that  $ \alpha + \beta = -\frac{1}{2} $ and  $ \alpha\beta = -8 $, find the values of  $ p $ and  $ q $.

7 The quadratic equation  $ x^{2}+2x-6=0 $ has roots  $ \alpha $ and  $ \beta $. Find the values of  $ (\alpha-\beta)^{2} $ and  $ \frac{1}{\alpha^{2}}+\frac{1}{\beta^{2}} $.

PS 8 A quadratic equation has roots  $ \alpha $ and  $ \beta $. Given that  $ \frac{1}{\alpha} + \frac{1}{\beta} = \frac{1}{2} $ and  $ \alpha^{2} + \beta^{2} = 12 $, find two possible quadratic equations that satisfy these values.

9 The quadratic equation  $ 3x^{2}+2x-4=0 $ has roots  $ \alpha $ and  $ \beta $. Find the values of  $ S_{1}, S_{2} $ and  $ S_{-1} $.

PS 10 You are given the quadratic equation  $ 4x^{2}-x+6=0 $ which has roots  $ \alpha $ and  $ \beta $.

a Find  $ \alpha^{2}+\beta^{2} $.

b Without solving the quadratic equation, state what your value for part a tells you about the roots.

### 1.2 Cubics

In this section we will be looking at cubic equations. We will use the same concepts as in Section 1.1, but this time the roots will be  $ \alpha, \beta $ and  $ \gamma $.

Beginning with  $ ax^{3} + bx^{2} + cx + d = 0 $, the first step is to divide by the constant a to get  $ x^{3} + \frac{b}{a}x^{2} + \frac{c}{a}x + \frac{d}{a} = 0 $.

Next, relate this to  $ (x - \alpha)(x - \beta)(x - \gamma) = 0 $ to establish the relation:

 $$ x^{3}-(\alpha+\beta+\gamma)x^{2}+(\alpha\beta+\alpha\gamma+\beta\gamma)x-\alpha\beta\gamma=0 $$ 

Then  $ \alpha + \beta + \gamma = -\frac{b}{a} $, which is known as  $ \Sigma\alpha $ or  $ S_1 $.

Other results are $\alpha\beta + \alpha\gamma + \beta\gamma = \frac{c}{a}$, written as $\Sigma\alpha\beta$, and $\alpha\beta\gamma = -\frac{d}{a}$, written as $\Sigma\alpha\beta\gamma$.

Recall from quadratics that  $ \Sigma\alpha^2 = (\Sigma\alpha)^2 - 2\Sigma\alpha\beta $. This is the same result for a cubic equation, where the term  $ (\Sigma\alpha)^2 = (\alpha + \beta + \gamma)^2 = \alpha^2 + \beta^2 + \gamma^2 + 2\alpha\beta + 2\alpha\gamma + 2\beta\gamma $, as shown in Key point 1.2.

<div style="text-align: center;"><img src="imgs/img_in_image_box_863_1022_902_1057.jpg" alt="Image" width="3%" /></div>


## TIP

Following on from the idea you saw in Worked example 1.3, if we consider the notation  $ S_{n} = \alpha^{n} + \beta^{n} + \gamma^{n} $ and then use it to represent our roots, just as with quadratic equations, we can use  $ S_{2} $ to represent  $ \alpha^{2} + \beta^{2} + \gamma^{2} $ and so on.

<!-- page 18 -->

<div style="text-align: center;"><img src="imgs/img_in_image_box_98_143_137_177.jpg" alt="Image" width="3%" /></div>


### KEY POINT 1.2

 $$ (\Sigma\alpha)^{2}=(\alpha+\beta+\gamma)^{2}=\alpha^{2}+\beta^{2}+\gamma^{2}+2\alpha\beta+2\alpha\gamma+2\beta\gamma $$ 

### WORKED EXAMPLE 1.4

Find the summation form for the results  $ \frac{1}{\alpha} + \frac{1}{\beta} + \frac{1}{\gamma} $ and  $ \frac{1}{\alpha^{2}} + \frac{1}{\beta^{2}} + \frac{1}{\gamma^{2}} $.

## Answer

 $$ \frac{1}{\alpha}+\frac{1}{\beta}+\frac{1}{\gamma}=\frac{\alpha\beta+\alpha\gamma+\beta\gamma}{\alpha\beta\gamma} $$ 

Combine the fractions.

 $$ \Rightarrow\Sigma\frac{1}{\alpha}=\frac{\Sigma\alpha\beta}{\Sigma\alpha\beta\gamma} $$ 

State the result.

 $$ \frac{1}{\alpha^{2}}+\frac{1}{\beta^{2}}+\frac{1}{\gamma^{2}}=\frac{\alpha^{2}\beta^{2}+\alpha^{2}\gamma^{2}+\beta^{2}\gamma^{2}}{\alpha^{2}\beta^{2}\gamma^{2}} $$ 

Combine the fractions, as before.

 $$ \Sigma\frac{1}{\alpha^{2}}=\frac{\Sigma(\alpha\beta)^{2}}{(\Sigma\alpha\beta\gamma)^{2}} $$ 

State the result.

All of the results derived for quadratic equations can also be written for cubics, but the algebra is more complicated. Try to convince yourself that for a cubic it is true that  $ \Sigma\alpha^3 = (\Sigma\alpha)^3 - 3\Sigma\alpha\beta\Sigma\alpha + 3\Sigma\alpha\beta\gamma $.

### WORKED EXAMPLE 1.5


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Given that  $ x^{3} + 2x^{2} + 5 = 0 $, find, using summation form, the values of  $ S_{1} $,  $ S_{2} $,  $ S_{3} $ and  $ S_{-1} $.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Answer</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ S_{1} = -2 $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ S_{2} = (\Sigma \alpha)^{2} - 2\Sigma \alpha\beta $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ \Rightarrow S_{2} = (-2)^{2} - 2 \times 0 = 4 $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ S_{3} = (\Sigma \alpha)^{3} - 3\Sigma \alpha\beta\Sigma \alpha + 3\Sigma \alpha\beta\gamma $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ S_{3} = (-2)^{3} - 3 \times (0) \times (-2) + 3 \times (-5) $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ S_{3} = -23 $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ S_{-1} = \frac{0}{-5} = 0 $</td></tr></table>

Worked example 1.5 uses the summation form, but there is a more efficient way of finding $S_{3}$ and higher powers.

<!-- page 19 -->

In Worked example 1.6 we will use the recurrence form to evaluate results such as $S_{3}$ and $S_{4}$.

Consider the equation  $ x^3 + 3x^2 + 6 = 0 $. Since  $ \alpha, \beta, \gamma $ all satisfy our cubics, we can see that  $ \alpha^3 + 3\alpha^2 + 6 = 0 $,  $ \beta^3 + 3\beta^2 + 6 = 0 $ and  $ \gamma^3 + 3\gamma^2 + 6 = 0 $.

Adding the three equations gives  $ \alpha^{3} + \beta^{3} + \gamma^{3} + 3(\alpha^{2} + \beta^{2} + \gamma^{2}) + 18 = 0 $ or  $ S_{3} + 3S_{2} + 18 = 0 $.

### WORKED EXAMPLE 1.6

For the cubic equation  $ 3x^{3} + 2x^{2} - 4x + 1 = 0 $, find the value of  $ S_{3} $.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td colspan="2">Answer</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ S_1 = -\frac{2}{3} $</td><td style='text-align: center; word-wrap: break-word;'>From  $ -\frac{b}{a} $.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ S_2 = \left(-\frac{2}{3}\right)^2 - 2 \times \left(-\frac{4}{3}\right) = \frac{28}{9} $</td><td style='text-align: center; word-wrap: break-word;'>Using  $ S_2 = (\Sigma \alpha)^2 - 2\Sigma \alpha\beta $.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ 3S_3 + 2S_2 - 4S_1 + 3 = 0 $</td><td style='text-align: center; word-wrap: break-word;'>We know that  $ 3\alpha^3 + 2\alpha^2 - 4\alpha + 1 = 0 $ and similar equations can be made for  $ \beta $ and  $ \gamma $. We add the three equations.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ S_3 = -\frac{107}{27} $</td><td style='text-align: center; word-wrap: break-word;'>Substitute for the final result.</td></tr></table>

We have already seen how to manipulate a polynomial to get a higher power result, such as obtaining $S_{3}$ from a quadratic equation. Imagine we want to obtain a value such as $S_{-2}$ from a cubic equation, using only recurrence methods.

The first step would be to multiply our cubic by  $ x^{-2} $ to give  $ ax + b + \frac{c}{x} + \frac{d}{x^2} = 0 $. The recurrence formula would then be  $ aS_1 + 3b + cS_{-1} + dS_{-2} = 0 $. Note the constant term, b, is multiplied by 3. Now we need to find only  $ S_1 $ and  $ S_{-1} $, and from the original equation this is straightforward.

### WORKED EXAMPLE 1.7


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td colspan="2">For the cubic equation  $ x^{3} - 3x^{2} + 4 = 0 $, find the value of  $ S_{-3} $.</td></tr><tr><td colspan="2">Answer</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ S_{-1} = \frac{0}{-4} = 0 $</td><td style='text-align: center; word-wrap: break-word;'>Recall that  $ S_{-1} = \frac{\Sigma \alpha \beta}{\Sigma \alpha \beta \gamma} $.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ x^{3} - 3x^{2} + 4 = 0 $</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ \Rightarrow 1 - \frac{3}{x} + \frac{4}{x^{3}} = 0 $</td><td style='text-align: center; word-wrap: break-word;'>Divide by  $ x^{3} $.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ 3 - 3S_{-1} + 4S_{-3} = 0 $</td><td style='text-align: center; word-wrap: break-word;'>Remember that the 1 is counted three times when adding the three equations for  $ \alpha $,  $ \beta $ and  $ \gamma $.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ S_{-3} = -\frac{3}{4} $</td><td style='text-align: center; word-wrap: break-word;'>Substitute values into the equation.</td></tr></table>

<!-- page 20 -->

We can generalise from Worked example 1.7. For a general cubic of the form  $ ax^3 + bx^2 + cx + d = 0 $, if we multiply by  $ x^n $ then our recurrence formula is  $ aS_{n+3} + bS_{n+2} + cS_{n+1} + dS_n = 0 $. Note that only constant terms get counted multiple times.

## EXERCISE 1B

1 Each of the following cubic equations has roots  $ \alpha $,  $ \beta $,  $ \gamma $. Find, for each case,  $ \alpha + \beta + \gamma $ and  $ \alpha\beta\gamma $.

a  $ x^{3}+3x^{2}-5=0 $ b  $ 2x^{3}+5x^{2}-6=0 $ c  $ x^{3}+7x-9=0 $

2 Given that  $ x^3 - 3x^2 + 12 = 0 $ has roots  $ \alpha, \beta, \gamma $, find the following values:

a  $ \alpha + \beta + \gamma $ and  $ \alpha\beta + \alpha\gamma + \beta\gamma $

b  $ \alpha^2 + \beta^2 + \gamma^2 $

3 The roots of each of the following cubic equations are $\alpha, \beta, \gamma$. In each case, find the values of $S_{2}$ and $S_{-1}$.

a $x^{3}-2x^{2}+5=0$ b $3x^{3}+4x-1=0$ c $x^{3}+3x^{2}+5x-7=0$

4 The cubic equation  $ x^{3}-x+7=0 $ has roots  $ \alpha,\beta,\gamma $. Find the values of  $ \Sigma\alpha $ and  $ \Sigma\alpha^{2} $.

5 Given that $2x^{3}+5x^{2}+1=0$ has roots $\alpha,\beta,\gamma$, and that $S_{n}=\alpha^{n}+\beta^{n}+\gamma^{n}$, find the values of $S_{2}$ and $S_{3}$.

6 The cubic equation  $ x^{3} + ax^{2} + bx + a = 0 $ has roots  $ \alpha, \beta, \gamma $, and the constants a, b are real and positive.

a Find, in terms of a and b, the values of  $ \Sigma\alpha $ and  $ \Sigma\frac{1}{\alpha} $.

b Given that  $ \Sigma\alpha = \Sigma\frac{1}{\alpha} $, does this cubic equation have complex roots? Give a reason for your answer.

7 The cubic equation  $ x^{3}-x+3=0 $ has roots  $ \alpha,\beta,\gamma $.

a Using the relation  $ S_{n}=\alpha^{n}+\beta^{n}+\gamma^{n} $, or otherwise, find the value of  $ S_{4} $.

b By considering $S_{1}$ and $S_{4}$, determine the value of $\alpha^{3}(\beta+\gamma)+\beta^{3}(\alpha+\gamma)+\gamma^{3}(\alpha+\beta)$.

P 8 A cubic polynomial is given as  $ 2x^{3}-x^{2}+x-5=0 $, having roots  $ \alpha,\beta,\gamma $.

a Show that  $ 2S_{n+3}-S_{n+2}+S_{n+1}-5S_n=0 $.

b Find the value of  $ S_{-2} $.

M 9 The cubic equation  $ px^{3} + qx^{2} + r = 0 $ has roots  $ \alpha, \beta, \gamma $. Find, in terms of p, q, r:

a  $ S_{1} $ b  $ S_{2} $ c  $ S_{3} $

10 The equation  $ x^{3} + px^{2} + qx + r = 0 $ is such that  $ S_{1} = 0 $,  $ S_{2} = -2 $ and  $ S_{-1} = \frac{1}{5} $.

Find the values of the constants p, q, r.

### 1.3 Quartics

Now that we are working with quartics, it is best to use the recurrence formula whenever we can. This is especially true for the sum of the cubes ( $ \alpha^3 + \beta^3 + \gamma^3 + \delta^3 $). If we want to determine the sum of the cubes of a general quartic, the best way is to first note down  $ S_1 $, then determine  $ S_2 $ and  $ S_{-1} $. After this, we can use the form  $ aS_4 + bS_3 + cS_2 + dS_1 + 4e = 0 $, then divide by  $ x $ to obtain  $ S_3 $. This process allows us to work out other values, especially those beyond the highest power.

As we have seen with previous polynomials, there are standard results that are defined by observation from previous cases, but the algebra for some results is too complicated to be discussed here.

<!-- page 21 -->

So, with our roots  $ \alpha, \beta, \gamma, \delta $, we have  $ \Sigma\alpha = -\frac{b}{a}, \Sigma\alpha\beta = \frac{c}{a}, \Sigma\alpha\beta\gamma = -\frac{d}{a} $ and  $ \Sigma\alpha\beta\gamma\delta = \frac{e}{a} $.

We also have  $ S_{2} = (\Sigma\alpha)^{2} - 2\Sigma\alpha\beta $ and  $ S_{-1} = \frac{\Sigma\alpha\beta\gamma}{\Sigma\alpha\beta\gamma\delta} $ and so on.

Algebraically it is much more sensible to use  $ S_{n} = \alpha^{n} + \beta^{n} + \gamma^{n} + \delta^{n} $.

When converting a polynomial to a recurrence formula, the constant is always multiplied by n from the original equation. As an example,  $ x^4 - 3x^3 - 5 = 0 $ would give  $ S_4 - 3S_3 - 20 = 0 $.

### WORKED EXAMPLE 1.8

A quartic polynomial is given as  $ x^{4} + 3x^{2} - x + 5 = 0 $ and has roots  $ \alpha, \beta, \gamma, \delta $. Find the values of  $ S_{2} $ and  $ S_{4} $.

## Answer


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td colspan="2">Answer</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ S_1 = 0 $</td><td style='text-align: center; word-wrap: break-word;'>Simply state the negative of the coefficient of  $ x^3 $, as the coefficient of  $ x^4 $ is 1.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ S_2 = 0^2 - 2 \times 3 = -6 $</td><td style='text-align: center; word-wrap: break-word;'>Use  $ S_2 = (\Sigma \alpha)^2 - 2\Sigma \alpha \beta $.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ S_4 + 3S_2 - S_1 + 20 = 0 $</td><td style='text-align: center; word-wrap: break-word;'>Use  $ S_n = \alpha^n + \beta^n + \gamma^n + \delta^n $.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ S_4 = -2 $</td><td style='text-align: center; word-wrap: break-word;'>Final answer.</td></tr></table>

<div style="text-align: center;"><img src="imgs/img_in_image_box_867_414_905_451.jpg" alt="Image" width="3%" /></div>


## TIP

Remember that for any polynomial,  $ \Sigma\frac{1}{\alpha} $ is always obtained using the negative of the coefficient of the linear term over the constant term.

### WORKED EXAMPLE 1.9

For the quartic  $ x^{4}-x^{3}+2x^{2}-2x-5=0 $, state the values of  $ S_{1} $ and  $ S_{-1} $, and determine the value of  $ S_{2} $. State whether or not there are any complex solutions.

## Answer

 $$ -1\times(-1) $$ 

 $$ S_{1}=1 $$ 

Use  $ S_{-1} = \frac{\Sigma \alpha \beta \gamma}{\Sigma \alpha \beta \gamma \delta} $.

 $$ S_{-1}=\frac{-(-2)}{-5}=-\frac{2}{5} $$ 

 $$ S_{2}=(1)^{2}-2\times2=-3 $$ 

 $$  Use~S_{2}=(\Sigma\alpha)^{2}-2\Sigma\alpha\beta. $$ 

 $ S_{2} $ < 0 so there are complex solutions.

<div style="text-align: center;"><img src="imgs/img_in_image_box_25_1248_65_1283.jpg" alt="Image" width="3%" /></div>


### KEY POINT 1.3

For quartics, use  $ S_{n} = \alpha^{n} + \beta^{n} + \gamma^{n} + \delta^{n} $ as a recurrence model to determine results.

<div style="text-align: center;"><img src="imgs/img_in_image_box_861_1153_900_1193.jpg" alt="Image" width="3%" /></div>


## TIP

Don't try to use an algebraic approach for quartics, especially for  $ S_{3} $ and higher. Use the recurrence method.

## EXERCISE 1C

1 For each of the following quartic equations, find the values of  $ \Sigma\alpha $ and  $ \Sigma\alpha\beta $.

a

 $$ x^{4}-2x^{3}+5x^{2}+7=0 $$ 

b

 $$ 2x^{4}+5x^{3}-3x+4=0 $$ 

c

 $$ 3x^{4}-2x^{2}+9x-11=0 $$

<!-- page 22 -->

2 The quartic equation  $ 5x^{4}-3x^{3}+x-13=0 $ has roots  $ \alpha $,  $ \beta $,  $ \gamma $,  $ \delta $. Find:

a  $ \Sigma\alpha $ and  $ \Sigma\alpha^{2} $ b  $ \Sigma\frac{1}{\alpha} $

3 A quartic equation is given as  $ x^{4}+x+2=0 $. It has roots  $ \alpha,\beta,\gamma,\delta $. State the values of  $ S_{1} $ and  $ S_{-1} $, and find the value of  $ S_{2} $.

4 The quartic equation  $ 2x^{4}+x^{3}-x+7=0 $ has roots  $ \alpha,\beta,\gamma,\delta $. Given that  $ S_{3}=\frac{11}{8} $, and using  $ S_{n} $, find the value of  $ S_{4} $.

5 You are given that  $ x^{4}-x^{3}+x+2=0 $, where the roots are  $ \alpha,\beta,\gamma,\delta $. Find the values of  $ \Sigma\alpha,\Sigma\alpha^{2} $ and  $ \Sigma\frac{1}{\alpha} $. Hence, determine the value of  $ \Sigma\alpha^{3} $.

PS 6 The quartic polynomial  $ x^{4} + ax^{2} + bx + 1 = 0 $ has roots  $ \alpha, \beta, \gamma, \delta $. Given that  $ S_{2} = S_{-1} $, find  $ S_{3} $ in terms of a.

PS 7 The polynomial  $ 3x^{4}+2x^{3}+7x^{2}+4=0 $ has roots  $ \alpha,\beta,\gamma,\delta $, where  $ S_{n}=\alpha^{n}+\beta^{n}+\gamma^{n}+\delta^{n} $.

a Find the values of  $ S_{1} $ and  $ S_{2} $

b Find the values of  $ S_{3} $ and  $ S_{4} $.

c Are there any complex roots? Give a reason for your answer.

8 For the polynomial  $ x^{4} + ax^{3} + bx^{2} + c = 0 $, with roots  $ \alpha, \beta, \gamma $ and  $ \delta $, it is given that  $ \alpha + \beta + \gamma + \delta = 2 $,  $ \alpha\beta\gamma\delta = 1 $ and  $ \alpha^{2} + \beta^{2} + \gamma^{2} + \delta^{2} = 0 $. Find the values of the coefficients a, b and c.

<div style="text-align: center;"><img src="imgs/img_in_image_box_115_730_148_761.jpg" alt="Image" width="2%" /></div>


9 The roots of the quartic  $ x^{4}-2x^{3}+x^{2}-4=0 $ are  $ \alpha,\beta,\gamma,\delta $. Show that  $ S_{4}=9S_{3} $.

### 1.4 Substitutions

Imagine that we are given the quadratic equation  $ x^2 + 3x + 5 = 0 $ with roots  $ \alpha, \beta $ and we are asked to find a quadratic that has roots  $ 2\alpha, 2\beta $. There are two approaches that we can take.

<div style="text-align: center;"><img src="imgs/img_in_image_box_928_803_970_844.jpg" alt="Image" width="3%" /></div>


First, consider the quadratic $(y-2\alpha)(y-2\beta)=0$, then $y^{2}-(2\alpha+2\beta)y+4\alpha\beta=0$. If we compare this with the original, which is $\alpha+\beta=-3$, $\alpha\beta=5$, then $y^{2}+6y+20=0$ is the new quadratic. This method requires us to know some results, or at least spend time working them out.

## TIP

A second method is to start with $y = 2x$, since each root of $y$ is twice that of $x$. Then,

substituting $x = \frac{y}{2}$ into the original gives $\left(\frac{y}{2}\right)^2 + 3\left(\frac{y}{2}\right) + 5 = 0$. Alternatively,

multiplying by $4, y^2 + 6y + 20 = 0$. This second approach does not need the values of roots.

It just needs the relationship between the roots of each polynomial.

You learned in AS &

A Level Mathematics

Pure Mathematics 1

Coursebook how to

find inverse functions

by interchanging

$x$ and $y$. The same

process is helpful here.



### WORKED EXAMPLE 1.10

Given that  $ x^{2}-2x+12=0 $ has roots  $ \alpha,\beta $, find the quadratic equation with roots  $ \frac{\alpha}{3},\frac{\beta}{3} $.

Answer

 $$ y=\frac{x}{3}\Rightarrow x=3y $$ 

 $$ (3y)^{2}-2(3y)+12=0 $$ 

Rearrange to make x the subject.

Substitute for x.

 $$ 3y^{2}-2y+4=0 $$ 

Multiply out terms and simplify.

<!-- page 23 -->

More complicated substitutions include reciprocal functions. For example, consider the cubic function  $ x^3 + x^2 - 7 = 0 $ with roots  $ \alpha, \beta $. If we are asked to find a cubic function with roots  $ \frac{1}{\alpha}, \frac{1}{\beta}, \frac{1}{\gamma} $, we would begin with  $ y = \frac{1}{x} \Rightarrow x = \frac{1}{y} $. Then  $ \left(\frac{1}{y}\right)^3 + \left(\frac{1}{y}\right)^2 - 7 = 0 $, which simplifies to the cubic  $ 7y^3 - y - 1 = 0 $.

### WORKED EXAMPLE 1.11

Given that  $ x^3 + x^2 - 5 = 0 $ has roots  $ \alpha, \beta, \gamma $, find the cubic equation with roots  $ \frac{1}{\alpha - 2}, \frac{1}{\beta - 2}, \frac{1}{\gamma - 2} $.

## Answer

 $$ y=\frac{1}{x-2}\Rightarrow xy-2y=1 $$ 

 $$ x=\frac{1+2y}{y} $$ 

Rearrange to make x the subject.

 $$ \left(\frac{1+2y}{y}\right)^{3}+\left(\frac{1+2y}{y}\right)^{2}-5=0 $$ 

Substitute for x.

 $$ \frac{1+6y+12y^{2}+8y^{3}}{y^{3}}+\frac{1+4y+4y^{2}}{y^{2}}-5=0 $$ 

Expand brackets.

 $$ 7y^{3}+16y^{2}+7y+1=0 $$ 

Multiply by  $ y^{3} $ and simplify.

### EXPLORE 1.1

The polynomial  $ x^3 + x - 3 = 0 $ has roots  $ \alpha, \beta, \gamma $. If  $ \frac{a\alpha + 1}{\alpha - b}, \frac{a\beta + 1}{\beta - b}, \frac{a\gamma + 1}{\gamma - b} $ are the roots of another cubic, what are the conditions on  $ a $ and  $ b $ to ensure that these cubics are the same?

Powers of roots require a different method. For example, if we have the cubic equation  $ 2x^3 + 7x^2 - 1 = 0 $ with roots  $ \alpha $,  $ \beta $,  $ \gamma $ and we want to determine the cubic with roots  $ \alpha^2 $,  $ \beta^2 $,  $ \gamma^2 $, there are two ways of approaching this.

First, we could state that $y = x^{2}$ and so $x = \sqrt{y}$. Substituting gives $2y^{\frac{3}{2}} + 7y - 1 = 0$. Next, write as $7y - 1 = -2y^{\frac{3}{2}}$ and square both sides, giving $49y^{2} - 14y + 1 = 4y^{3}$. So $4y^{3} - 49y^{2} + 14y - 1 = 0$ is the cubic that we are looking for.

In the second approach we first rearrange the cubic to  $ 2x^3 = 1 - 7x^2 $. Doing this allows us to square both sides and get even powers of  $ x $ for every term, so  $ 4x^6 = 1 - 14x^2 + 49x^4 $. Substituting in  $ x^2 = y $ gives the same cubic as before.

In the first approach we substitute $y = x^{2}$ before rearranging the equation. In the second approach we do the steps in the reverse order. For both approaches we need to make sure the powers of $x$ are appropriate.

<!-- page 24 -->

### WORKED EXAMPLE 1.12


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>The polynomial  $ x^{4} + x^{3} - x + 12 = 0 $ has roots  $ \alpha, \beta, \gamma, \delta $. Find the polynomial with roots  $ \alpha^{2}, \beta^{2}, \gamma^{2}, \delta^{2} $.</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Answer\n $ y = x^{2} $\n $ x^{4} + 12 = x - x^{3} $\n $ \quad x^{8} + 24x^{4} + 144 = x^{2} - 2x^{4} + x^{6} $\n $ \quad x^{8} - x^{6} + 26x^{4} - x^{2} + 144 = 0 $\n $ \quad y^{4} - y^{3} + 26y^{2} - y + 144 = 0 $</td><td style='text-align: center; word-wrap: break-word;'>State the substitution.\n\nRearrange so that both sides when squared give even terms.\n\nSquare both sides.\n\nSimplify.\n\nUse  $ x^{2} = y $.</td></tr></table>

These substitution methods are useful when dealing with problems such as finding the value of  $ S_{6} $ or even  $ S_{8} $.

Consider the quartic  $ x^4 + x^3 - 5 = 0 $. For this polynomial, we would like to determine the value of  $ S_4 $. The process for finding  $ S_4 = \alpha^4 + \beta^4 + \gamma^4 + \delta^4 $ can be time consuming. Now, consider that there is another quartic such that  $ y = x^2 $. If this quartic exists, then for  $ y $ we would have  $ S_n = \alpha^2n + \beta^2n + \gamma^2n + \delta^2n $. Since we have doubled the power for each root, once we have determined the quartic for  $ y $ we only need to find  $ S_2 $, which is straightforward.

Rewrite the original quartic as  $ x^4 - 5 = -x^3 $, then square both sides to get  $ x^8 - 10x^4 + 25 = x^6 $. Next, replace  $ x^2 $ with  $ y $ so that  $ y^4 - y^3 - 10y^2 + 25 = 0 $. Finally, for the new quartic,  $ S_1 = 1 $ and  $ S_2 = 1^2 - 2 \times (-10) = 21 $. Hence, for the original quartic,  $ S_4 = 21 $.

This is an effective method and can save lots of time, particularly for much higher values of n.

### WORKED EXAMPLE 1.13


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td colspan="3">The cubic polynomial  $ x^{3} + 5x^{2} + 1 = 0 $ has roots  $ \alpha, \beta, \gamma $. Using the substitution  $ y = x^{3} $, or otherwise, find the value of  $ S_{6} $.</td></tr><tr><td colspan="3">Answer</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ x^{3} + 5x^{2} + 1 = 0 $</td><td style='text-align: center; word-wrap: break-word;'>(1)</td><td style='text-align: center; word-wrap: break-word;'>Label the original equation.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ x^{3} + 1 = -5x^{2} $</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Since we are using  $ x^{3} $, ensure all terms are arranged so when both sides are cubed, they produce powers that are multiples of 3.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ x^{9} + 3x^{6} + 3x^{3} + 1 = -125x^{6} $</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Cube both sides.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ \Rightarrow x^{9} + 128x^{6} + 3x^{3} + 1 = 0 $</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Simplify.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ \Rightarrow y^{3} + 128y^{2} + 3y + 1 = 0 $</td><td style='text-align: center; word-wrap: break-word;'>(2)</td><td style='text-align: center; word-wrap: break-word;'>Use  $ x^{3} = y $, label the new equation.</td></tr></table>

<div style="text-align: center;"><img src="imgs/img_in_image_box_927_840_968_878.jpg" alt="Image" width="3%" /></div>


## TIP

Ensure both sides of the rearranged polynomial will give appropriate powers when the squaring or cubing operation has taken place. For example,  $ x^{3}-5x+7=0 $ with  $ y=x^{2} $ would be written as  $ x^{3}-5x=-7 $ to ensure that, when squared, both sides produce only even powers.

If the same equation is used with $y = x^{3}$, then rearrange to $x^{3} + 7 = 5x$ so that, when it is cubed, the powers of $x$ are multiples of 3 on both sides.

<!-- page 25 -->

$$ S_{1}=-128 $$ 

Determine $S_{1}$.

 $$ S_{2}=(-128)^{2}-2\times3=16378for(2) $$ 

Substitute for $S_{2}$.

Hence, for (1),  $ S_{6}=16378 $

State $S_{6}$.

<div style="text-align: center;"><img src="imgs/img_in_image_box_30_317_74_357.jpg" alt="Image" width="3%" /></div>


## DID YOU KNOW?

The term ‘polynomials’ was not used until the 17th century. Before the 15th century, equations were represented by words, not symbols. A famous Chinese algebraic problem was written: ‘Three bundles of good crop, two bundles of mediocre crop, and one bundle of bad crop are sold for 29 dou.’ In modern times we would phrase this as  $ 3a + 2b + c = 29 $.

## EXERCISE 1D

M 1 The quadratic equation  $ x^{2}+5x+3=0 $ has roots  $ \alpha $,  $ \beta $. Find the quadratic equation with roots  $ 3\alpha $,  $ 3\beta $.

M 2 The quadratic equation  $ 2x^{2}-4x+7=0 $ has roots  $ \alpha,\beta $.

a Find the quadratic equation with roots  $ \alpha^{2}, \beta^{2} $.

b Find the quadratic equation with roots  $ 2\alpha - 3 $,  $ 2\beta - 3 $.

M 3 Given that  $ 3x^{2}-2x+9=0 $ has roots  $ \alpha, \beta $, find the quadratic equation with roots  $ \frac{\alpha+1}{\alpha}, \frac{\beta+1}{\beta} $.

4 The quadratic equation  $ x^{2}-4x+9=0 $ has roots  $ \alpha,\beta $. Find the quadratic that has roots  $ \frac{1}{\alpha},\frac{1}{\beta} $.

5 Given that $2x^{3}-5x+1=0$ has roots $\alpha,\beta,\gamma$, find the cubic equation with roots $\alpha^{2},\beta^{2},\gamma^{2}$. Hence, find the value of $S_{4}$.

P PS 6 The cubic equation  $ x^{3} + 3x^{2} - 1 = 0 $ has roots  $ \alpha, \beta, \gamma $. Show that the cubic equation with roots  $ \frac{\alpha + 2}{\alpha}, \frac{\beta + 2}{\beta}, \frac{\gamma + 2}{\gamma} $ is  $ y^{3} - 3y^{2} - 9y + 3 = 0 $. Hence, determine the values of:

a  $ \frac{(\alpha+2)(\beta+2)(\gamma+2)}{\alpha\beta\gamma} $ b  $ \frac{\alpha}{\alpha+2}+\frac{\beta}{\beta+2}+\frac{\gamma}{\gamma+2} $

7 A quartic equation, $2x^{4}-x^{3}-6=0$, has roots $\alpha,\beta,\gamma,\delta$. Show that the quartic equation with roots $\alpha^{3},\beta^{3},\gamma^{3},\delta^{3}$ is $8y^{4}-y^{3}-18y^{2}-108y-216=0$. Hence, find the values of $S_{6}$ and $S_{-3}$.

8 The cubic equation  $ x^{3}-x+4=0 $ has roots  $ \alpha,\beta,\gamma $. Find the cubic equation that has roots  $ \alpha^{2},\beta^{2},\gamma^{2} $. Hence, otherwise, determine the values of  $ S_{6}, S_{8} $ and  $ S_{10} $.

<!-- page 26 -->

## WORKED PAST PAPER QUESTION

The equation  $ x^{3} + x - 1 = 0 $ has roots  $ \alpha, \beta, \gamma $.

Show that the equation with roots  $ \alpha^{3}, \beta^{3}, \gamma^{3} $ is  $ y^{3} - 3y^{2} + 4y - 1 = 0 $.

Hence, find the value of  $ \alpha^{6} + \beta^{6} + \gamma^{6} $.

Cambridge International AS & A Level Further Mathematics 9231 Paper 1 Q5 June 2008

Answer

Start with  $ x^{3} - 1 = -x $.

Then rewrite this as  $ (x^{3} - 1)^{3} = -x^{3} $. This gives  $ x^{9} - 3x^{6} + 4x^{3} - 1 = 0 $.

Let  $ y = x^{3} $ to give  $ y^{3} - 3y^{2} + 4y - 1 = 0 $.

Note that  $ S_{n} = \alpha^{n} + \beta^{n} + \gamma^{n} $.

 $ S_{6} $ for the original equation is  $ S_{2} $ for the new equation, so  $ S_{2} = 3^{2} - 2 \times 4 = 1 $.

Hence,  $ \alpha^{6} + \beta^{6} + \gamma^{6} = 1 $.

## Checklist of learning and understanding

## For quadratic equations  $ (ax^{2} + bx + c = 0) $:

 $ \Sigma\alpha = \alpha + \beta = -\frac{b}{a} $

 $ \Sigma\alpha\beta = \alpha\beta = \frac{c}{a} $

 $ S_n = \alpha^n + \beta^n $

For cubic equations  $ (ax^{3} + bx^{2} + cx + d = 0) $:

 $ \Sigma\alpha = \alpha + \beta + \gamma = -\frac{b}{a} $

$$\Sigma\alpha\beta=\alpha\beta+\alpha\gamma+\beta\gamma=\frac{c}{a}$$

$$\Sigma\alpha\beta\gamma=\alpha\beta\gamma=-\frac{d}{a}$$

 $ S_n = \alpha^n + \beta^n + \gamma^n $

For quartic equations  $ (ax^{4} + bx^{3} + cx^{2} + dx + e = 0) $:

$$\Sigma\alpha=\alpha+\beta+\gamma+\delta=-\frac{b}{a}$$

$$\Sigma\alpha\beta=\alpha\beta+\alpha\gamma+\alpha\delta+\beta\gamma+\beta\delta+\gamma\delta=\frac{c}{a}$$

 $$ \Sigma\alpha\beta\gamma=\alpha\beta\gamma+\alpha\beta\delta+\alpha\gamma\delta+\beta\gamma\delta=-\frac{d}{a} $$ 

 $ \Sigma\alpha\beta\gamma\delta=\alpha\beta\gamma\delta=\frac{e}{a} $

 $ S_n = \alpha^n + \beta^n + \gamma^n + \delta^n $

## For recurrence notation:

 $ \Sigma\alpha $ is also known as  $ S_{1} $

 $ \Sigma\alpha^{2}=(\Sigma\alpha)^{2}-2\Sigma\alpha\beta $ is also known as  $ S_{2} $.

$\Sigma_{\alpha}^{1}$ is known as $S_{-1}$. It is always equal to the negative of the coefficient of the linear term divided by the coefficient of the constant term.

<!-- page 27 -->

1 The roots of the equation  $ x^3 + 4x - 1 = 0 $ are  $ \alpha, \beta $ and  $ \gamma $. Use the substitution  $ y = \frac{1}{1 + x} $ to show that the equation  $ 6y^3 - 7y^2 + 3y - 1 = 0 $ has roots  $ \frac{1}{\alpha + 1}, \frac{1}{\beta + 1} $ and  $ \frac{1}{\nu + 1} $.

For the cases $n=1$ and $n=2$, find the value of $\frac{1}{(\alpha+1)^{n}}+\frac{1}{(\beta+1)^{n}}+\frac{1}{(\gamma+1)^{n}}$.

Deduce the value of  $ \frac{1}{(\alpha+1)^3}+\frac{1}{(\beta+1)^3}+\frac{1}{(\gamma+1)^3} $.

Hence show that  $ \frac{(\beta+1)(\gamma+1)}{(\alpha+1)^2}+\frac{(\gamma+1)(\alpha+1)}{(\beta+1)^2}+\frac{(\alpha+1)(\beta+1)}{(\gamma+1)^2}=\frac{73}{36} $.

Cambridge International AS & A Level Further Mathematics 9231 Paper 1 Q7 November 2010

## 2 The roots of the quartic equation  $ x^{4}+4x^{3}+2x^{2}-4x+1=0 $ are  $ \alpha,\beta,\gamma $ and  $ \delta $

## Find the values of

i  $ \alpha + \beta + \gamma + \delta $,

ii  $ \alpha^{2}+\beta^{2}+\gamma^{2}+\delta^{2} $,

iii  $ \frac{1}{\alpha} + \frac{1}{\beta} + \frac{1}{\gamma} + \frac{1}{\delta} $,

$$\mathrm{iv}\quad\frac{\alpha}{\beta\gamma\delta}+\frac{\beta}{\alpha\gamma\delta}+\frac{\gamma}{\alpha\beta\delta}+\frac{\delta}{\alpha\beta\gamma}.$$

Using the substitution $y = x + 1$, find a quartic equation in $y$. Solve this quartic equation and hence find the roots of the equation $x^{4} + 4x^{3} + 2x^{2} - 4x + 1 = 0$.

Cambridge International AS & A Level Further Mathematics 9231 Paper 11 Q11 November 2014

3 The cubic equation  $ x^{3}-x^{2}-3x-10=0 $ has roots  $ \alpha,\beta,\gamma $.

i Let $u = -\alpha + \beta + \gamma$. Show that $u + 2\alpha = 1$, and hence find a cubic equation having roots $-\alpha + \beta + \gamma$, $\alpha - \beta + \gamma$, $\alpha + \beta - \gamma$.

ii State the value of $\alpha\beta\gamma$ and hence find a cubic equation having roots $\frac{1}{\beta\gamma},\frac{1}{\gamma\alpha},\frac{1}{\alpha\beta}$.

Cambridge International AS & A Level Further Mathematics 9231 Paper 13 Q8 June 2012

