# Probability generating functions

<!-- Cambridge International AS  A Level Further Mathematics Coursebook (Lee Mckelvey Martin Crozier) .pdf p291-319 -->

<!-- page 291 -->

<div style="text-align: center;"><img src="imgs/img_in_image_box_6_6_1188_766.jpg" alt="Image" width="96%" /></div>


# Chapter 12 Probability generating functions

## In this chapter you will learn how to:

understand the concept of a probability generating function (PGF)

construct and use the PGF for given distributions, including:

discrete uniform distribution

binomial distribution

geometric distribution

Poisson distribution

use formulae for the mean (E(X)) and variance (Var(X)) of a discrete random variable in terms of its PGF, and use these formulae to calculate the mean and variance of a given probability distribution

use the result that the PGF of the sum of independent random variables is the product of the PGFs of those random variables (the convolution theorem)

find the probability generating function of a linear transformation of random variables

generalise to three or more random variables.

<!-- page 292 -->

## PREREQUISITE KNOWLEDGE


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Where it comes from</td><td style='text-align: center; word-wrap: break-word;'>What you should be able to do</td><td style='text-align: center; word-wrap: break-word;'>Check your skills</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>AS &amp; A Level Mathematics Probability &amp; Statistics 1, Chapters 7 &amp; 8AS &amp; A Level Mathematics Probability &amp; Statistics 2, Chapters 2 &amp; 4</td><td style='text-align: center; word-wrap: break-word;'>You should be familiar with the binomial distribution, the Poisson distribution, and the geometric distribution.</td><td style='text-align: center; word-wrap: break-word;'>1 Find  $ E(X) $ and  $ \operatorname{Var}(X) $ of  $ X \sim \operatorname{Bin}(8, 0.4) $.2 Find  $ E(X) $ and  $ \operatorname{Var}(X) $ of  $ X \sim \operatorname{Po}(2) $.3 Find  $ E(X) $ and  $ \operatorname{Var}(X) $ of  $ X \sim \operatorname{Geo}(0.3) $.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>AS &amp; A Level Mathematics Pure Mathematics 1, Chapters 6 &amp; 21</td><td style='text-align: center; word-wrap: break-word;'>Find the sum of a geometric series. Use some aspects of Maclaurin expansions.</td><td style='text-align: center; word-wrap: break-word;'>4 Find the sum to the  $ n $th term of  $ \frac{1}{3} + \left(\frac{1}{3}\right)^2 + \left(\frac{1}{3}\right)^3 + ... $5 Find the Maclaurin expansion of  $ \frac{5}{(3 - 2t)^2 $ up to and including the  $ t^3 $ term.</td></tr></table>

## Redefining probability distributions

The discrete uniform distribution is a distribution where each discrete value has the same probability of occurring. For instance, when rolling a fair die, the probability of each outcome is  $ \frac{1}{6} $.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>x</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>P(X=x)</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{6} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{6} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{6} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{6} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{6} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{6} $</td></tr></table>

Generally:

 $$ \mathrm{P}(X=x)=\begin{cases}\dfrac{1}{n}&x=x_{1},x_{2},\ldots,x_{n}\\ 0&otherwise\end{cases} $$ 

In this chapter, we shall study a different way of describing a probability distribution. We focus on finding the probability generating functions (PGFs) of discrete probability distributions. This gives an elegant and efficient way of finding expected values and variances. A PGF gives a concise form for a probability distribution and allows much greater analysis. By recognising the expansions of functions, PGFs enable us to describe the structure of infinite discrete distributions, such as the Poisson distribution and geometric distribution. We can therefore use PGFs to find the probabilities when the value of the discrete random variable is very large indeed.

### 12.1 The probability generating function

Let X represent a discrete random variable, with values  $ x_{i} $:


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>x</td><td style='text-align: center; word-wrap: break-word;'>$ x_1 $</td><td style='text-align: center; word-wrap: break-word;'>$ x_2 $</td><td style='text-align: center; word-wrap: break-word;'>$ x_3 $</td><td style='text-align: center; word-wrap: break-word;'>...</td><td style='text-align: center; word-wrap: break-word;'>$ x_n $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ \mathrm{P}(X=x) $</td><td style='text-align: center; word-wrap: break-word;'>$ \mathrm{P}(X=x_1) $</td><td style='text-align: center; word-wrap: break-word;'>$ \mathrm{P}(X=x_2) $</td><td style='text-align: center; word-wrap: break-word;'>$ \mathrm{P}(X=x_3) $</td><td style='text-align: center; word-wrap: break-word;'>...</td><td style='text-align: center; word-wrap: break-word;'>$ \mathrm{P}(X=x_n) $</td></tr></table>

<!-- page 293 -->

We can create a function $G_{X}(t)$ using this table:

 $$ \mathrm{G}_{X}(t)=\mathrm{P}(X=x_{1})t^{x_{1}}+\mathrm{P}(X=x_{2})t^{x_{2}}+\mathrm{P}(X=x_{3})t^{x_{3}}+\cdots+\mathrm{P}(X=x_{n})t^{x_{n}} $$ 

This function is called the probability generating function (PGF). It can be written as a single summation:

 $$ \mathrm{G}_{X}(t)=\sum_{x}t^{x_{i}}\mathrm{P}(X=x_{i}) $$ 

This is called the closed form of the probability generating function. Notice that the expression for $G_X(t)$ is the same as that for the expectation function, $\mathrm{E}(t^X)$, and so $G_X(t) = \sum_x t^{x_i} \mathrm{P}(X = x_i) = \mathrm{E}(t^X)$, as shown in Key point 12.1.

<div style="text-align: center;"><img src="imgs/img_in_image_box_26_444_68_478.jpg" alt="Image" width="3%" /></div>


### KEY POINT 12.1

 $$ \mathrm{G}_{X}(t)=\sum_{x}t^{x_{i}}\mathrm{P}(X=x_{i})=\mathrm{E}(t^{X}) $$ 

The variable $t$ is called a dummy variable in this case, and has no significance itself, but $t$ does have an important role in finding the expectation of $X$ and higher moments of expectation.

WORKED EXAMPLE 12.1

Consider the following probability distribution.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>x</td><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>P(X=x)</td><td style='text-align: center; word-wrap: break-word;'>0.1</td><td style='text-align: center; word-wrap: break-word;'>0.2</td><td style='text-align: center; word-wrap: break-word;'>0.3</td><td style='text-align: center; word-wrap: break-word;'>0.15</td><td style='text-align: center; word-wrap: break-word;'>0.1</td><td style='text-align: center; word-wrap: break-word;'>0.1</td><td style='text-align: center; word-wrap: break-word;'>0.05</td></tr></table>

Write down the PGF for the random variable X.

## Answer

Apply the general form for the PGF.

 $$ \mathbf{G}_{X}(t)=\sum t^{x_{i}}\mathrm{P}(X=x_{i}) $$ 

Sometimes it is useful to do this in table form first.

 $$ \mathbf{G}_{X}(t)=0.1t^{0}+0.2t^{1}+0.3t^{2}+0.15t^{3}+0.1t^{4}+0.1t^{5}+0.05t^{6} $$ 

In Worked example 12.1, the values of the random variable occur in a sequence. This does not have to be the case, as Worked example 12.2 shows.

### WORKED EXAMPLE 12.2

Consider the following probability distribution.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>x</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>10</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ P(X=x) $</td><td style='text-align: center; word-wrap: break-word;'>0.1</td><td style='text-align: center; word-wrap: break-word;'>0.2</td><td style='text-align: center; word-wrap: break-word;'>0.3</td><td style='text-align: center; word-wrap: break-word;'>0.4</td></tr></table>

Write down the PGF for the random variable X.

## Answer

Apply the general form for the PGF.

 $$ \mathrm{G}_{X}(t)=\sum_{x}t^{x_{i}}\mathrm{P}(X=x_{i}) $$ 

 $$ \mathbf{G}_{X}(t)=0.1t^{2}+0.2t^{4}+0.3t^{5}+0.4t^{10} $$ 

Notice that there does not need to be any specific pattern in the values that the random variable can take.

<!-- page 294 -->

At a trivial level, you can think of a PGF as a different way of presenting the information given by a probability distribution table. As you will discover throughout this chapter, PGFs allow us to calculate much more.

You may have noticed in Worked examples 12.1 and 12.2 that the probabilities are just the coefficients of each of the terms in t. The sum of these probabilities is 1.

We can see this by evaluating the probability generating function when t = 1:

 $$ \begin{array}{r l}&{\mathrm{G}_{X}(1)=\displaystyle\sum_{x}1^{x_{i}}\mathrm{P}(X=x_{i})=\displaystyle\sum_{x}\mathrm{P}(X=x_{i})=1}\\ &{\mathrm{G}_{X}(1)=1}\end{array} $$ 

Something that is a little harder to spot is that if we differentiate the probability generating function with respect to $t$, we will multiply each term by the value $x_{i}$.

 $$ \mathrm{G}^{\prime}_{X}(1)=\sum_{x}x_{i}(1)^{x_{i}-1}\mathrm{P}\left(X=x_{i}\right) $$ 

And then evaluating at t = 1 gives:

 $$ \mathrm{G}_{X}^{\prime}(1)=\sum_{x}x_{i}(1)^{x_{i}-1}\mathrm{P}\left(X=x_{i}\right)=\mathrm{E}(X) $$ 

So  $ G_{X}^{\prime}(1) = \mathrm{E}(X) $, as shown in Key point 12.2.

<div style="text-align: center;"><img src="imgs/img_in_image_box_102_707_144_743.jpg" alt="Image" width="3%" /></div>


### KEY POINT 12.2

 $$ \mathrm{G}^{\prime}_{X}(1)=\mathrm{E}(X) $$ 

You may notice that if all of the values of $x$ are non-negative integer values, then $G_{X}(t)$ forms a polynomial in $t$. This may be finite or infinite, depending on the context.

<div style="text-align: center;"><img src="imgs/img_in_image_box_932_528_976_564.jpg" alt="Image" width="3%" /></div>


## REWIND

From your work on series in AS & A Level Pure Mathematics 1 Chapter 6, you may have observed that if there is a pattern in the PGF, it may be possible to express it as a function rather than a summation. This can lead to an efficient way of finding E(X).

### WORKED EXAMPLE 12.3

Let X be a discrete random variable, as shown in the probability distribution given by:


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>x</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>P(X=x)</td><td style='text-align: center; word-wrap: break-word;'>0.2</td><td style='text-align: center; word-wrap: break-word;'>0.2</td><td style='text-align: center; word-wrap: break-word;'>0.2</td><td style='text-align: center; word-wrap: break-word;'>0.2</td><td style='text-align: center; word-wrap: break-word;'>0.2</td></tr></table>

Find the probability generating function for $X$.

## Answer

The PGF is:

Use the definition of  $ G_{X}(t) $.

 $$ \mathrm{G}_{X}(t)=\sum_{x}t^{x_{i}}\mathrm{P}(X=x_{i}) $$ 

 $$ \begin{aligned}G_{X}(t)&=0.2t^{1}+0.2t^{2}+0.2t^{3}+0.2t^{4}+0.2t^{5}\\&=0.2t(1+t+t^{2}+t^{3}+t^{4})\end{aligned} $$ 

Factorise.

<div style="text-align: center;"><img src="imgs/img_in_image_box_935_1015_979_1054.jpg" alt="Image" width="3%" /></div>


## FAST FORWARD

In the work on Maclaurin expansions in Chapter 21 Section 21.4, you should see that if there is a pattern in the PGF, it may be possible to express it as a function rather than a summation. This is an efficient way of finding E(X) and higher moments of expectation.

<!-- page 295 -->

$$ (1+t+t^{2}+t^{3}+t^{4})=S_{5}=\frac{1-t^{5}}{1-t} $$ 

 $$ G_{X}(t)=\frac{0.2t(1-t^{5})}{1-t} $$ 

Notice that the distribution from the table is a uniform distribution.

Notice that this expression is the sum of the first five terms of a geometric series with first term 1 and common ratio t.



So we can use the formula

 $ S_{n}=\frac{a(1-r^{n})}{1-r} $ from AS & A Level Pure

Mathematics 1.

## Discrete uniform distribution

Let $X$ be a discrete random variable with $\mathrm{P}(X=x_i)=\begin{cases}\dfrac{1}{n}&\text{if }i=1,\ldots n\\0&\text{otherwise}.\end{cases}$

Then  $  \mathrm{G}_{X}(t) = \frac{t(1 - t^{n})}{n(1 - t)}  $, as shown in Key point 12.3.

<div style="text-align: center;"><img src="imgs/img_in_image_box_29_625_71_659.jpg" alt="Image" width="3%" /></div>


### KEY POINT 12.3

For a uniform distribution:

 $$ \mathrm{G}_{X}(t)=\frac{t(1-t^{n})}{n(1-t)} $$ 

### WORKED EXAMPLE 12.4

Let  $ X \sim \text{Bin}(5, 0.2) $. Find the probability generating function for  $ X $.

## Answer

As a reminder, the probability distribution would be:

Use the binomial formula from AS & A Level Probability & Statistics 1:




<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>x</td><td style='text-align: center; word-wrap: break-word;'>P(X=x)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>0.8^{5}</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>5\times0.8^{4}\times0.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>10\times0.8^{3}\times0.2^{2}</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>10\times0.8^{2}\times0.2^{3}</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>5\times0.8^{1}\times0.2^{4}</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>0.2^{5}</td></tr></table>

The PGF is:

 $$ \mathrm{P}(X=x)=\binom{n}{x}p^{x}q^{n-x} $$ 

 $$ \mathrm{G}_{X}(t)=\sum_{i}t^{x_{i}}\mathrm{P}(X=x_{i}) $$ 

 $$ \begin{aligned}\mathrm{G}_{\chi}(t)&=0.8^{5}+5\times0.8^{4}\times0.2t+10\times0.8^{3}\times0.2^{2}t^{2}\\&\quad+10\times0.8^{2}\times0.2^{3}t^{3}+5\times0.8^{1}\times0.2^{4}t^{4}+0.2^{5}t^{5}\\&=(0.8+0.2t)^{5}\end{aligned} $$ 

This is a binomial expansion and can be factorised.

<!-- page 296 -->

## Binomial distribution

Let  $ X \sim \mathrm{Bin}(n, p) $. Thenn  $ \mathrm{G}_{X}(t) = (q + pt)^{n} $, as shown in Key point 12.4.

<div style="text-align: center;"><img src="imgs/img_in_image_box_95_229_135_263.jpg" alt="Image" width="3%" /></div>


### KEY POINT 12.4

For the binomial distribution:

 $$ G_{X}(t)=(q+p t)^{n} $$ 

### WORKED EXAMPLE 12.5

Let  $ X \sim \text{Geo}\left(\frac{1}{5}\right) $. Find the probability generating function for  $ X $.

## Answer

As a reminder, the probability distribution would be:


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>x</td><td style='text-align: center; word-wrap: break-word;'>$ P(X=x) $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{5} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>$ \left(\frac{4}{5}\right)\left(\frac{1}{5}\right) $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>$ \left(\frac{4}{5}\right)^{2}\left(\frac{1}{5}\right) $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>...</td><td style='text-align: center; word-wrap: break-word;'>...</td></tr></table>

The PGF is:

 $$ G_{X}(t)=\sum_{x}t^{x_{i}}\mathrm{P}(X=x_{i}) $$ 

 $$ \begin{aligned}G_{X}(t)&=\frac{1}{5}t+\left(\frac{4}{5}\right)\left(\frac{1}{5}\right)t^{2}+\left(\frac{4}{5}\right)^{2}\left(\frac{1}{5}\right)t^{3}+\cdots\\&=\frac{t}{5}\Biggl(1+\left(\frac{4t}{5}\right)+\left(\frac{4t}{5}\right)^{2}+\cdots\Biggr)\\&=\frac{\frac{t}{5}}{\left(1-\frac{4t}{5}\right)}\\&=\frac{t}{5-4t}\\ \end{aligned} $$ 

Using the geometric formula from AS & A Level Probability & Statistics 1:

 $$ \mathrm{P}(X=x)=\left(\frac{4}{5}\right)^{x-1}\left(\frac{1}{5}\right) $$ 

This is the sum of a geometric series to infinity. So we can use the formula  $ S_{\infty} = \frac{a}{1 - r} $ from AS & A Level Pure Mathematics 1.

This gives us a generalised form, but we need to simplify it.

<!-- page 297 -->

## Geometric distribution

Let $X \sim \mathrm{Geo}(p)$. Then $G_{X}(t) = \frac{pt}{1 - qt}$, as shown in Key point 12.5.

<div style="text-align: center;"><img src="imgs/img_in_image_box_34_252_74_286.jpg" alt="Image" width="3%" /></div>


### KEY POINT 12.5

For a geometric distribution:

 $$ \mathrm{G}_{X}(t)=\frac{p t}{1-q t} $$ 

## Poisson distribution

Let  $ X \sim \mathrm{Po}(\lambda) $. Then  $ G_X(t) = \mathrm{e}^{\lambda(t-1)} $, as shown in Key point 12.6.

<div style="text-align: center;"><img src="imgs/img_in_image_box_34_517_71_549.jpg" alt="Image" width="3%" /></div>


### KEY POINT 12.6

For a Poisson distribution:

 $$ G_{X}(t)=\mathrm{e}^{\lambda(t-1)} $$ 

### PROOF 12.1

The following table shows the probability distribution table for $X \sim \mathrm{Po}(\lambda)$, using $\mathrm{P}(X = x) = \frac{\mathrm{e}^{-\lambda} \lambda^x}{x!}$.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>x</td><td style='text-align: center; word-wrap: break-word;'>P(X=x)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>$ e^{-\lambda} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{\lambda e^{-\lambda}}{1!} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{\lambda^{2}e^{-\lambda}}{2!} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{\lambda^{3}e^{-\lambda}}{3!} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>...</td><td style='text-align: center; word-wrap: break-word;'>...</td></tr></table>

And so the PGF is:

 $$ \begin{aligned}\mathrm{G}_{X}(t)&=\mathrm{e}^{-\lambda}+\frac{\lambda\mathrm{e}^{-\lambda}}{1!}t+\frac{\lambda^{2}\mathrm{e}^{-\lambda}}{2!}t^{2}+\frac{\lambda^{3}\mathrm{e}^{-\lambda}}{3!}t^{3}+\cdots\\&=\mathrm{e}^{-\lambda}\bigg(1+\lambda t+\frac{(\lambda t)^{2}}{2!}+\frac{(\lambda t)^{3}}{3!}+\cdots\bigg)\end{aligned} $$ 

From Chapter 21, we have the following Maclaurin expansion.

 $$ \mathrm{e}^{x}\approx1+x+\frac{x^{2}}{2!}+\frac{x^{3}}{3!}+\cdots $$ 

Therefore, the PGF becomes:

 $$ \begin{aligned}G_{X}(t)&=\mathrm{e}^{-\lambda}(\mathrm{e}^{\lambda t})\\&=\mathrm{e}^{\lambda(t-1)}\end{aligned} $$ 

as required.

<!-- page 298 -->

## EXERCISE 12A

1 For each of the following distributions, write down the probability generating function,  $ \mathrm{G}_{X}(t) $.

a  $ X \sim \mathrm{Bin}(20, 0.3) $ b  $ X \sim \mathrm{Bin}(10, 0.25) $ c  $ X \sim \mathrm{Bin}(50, 0.04) $

2 For each of the following distributions, write down the probability generating function,  $ \mathrm{G}_{X}(t) $.

a  $ X \sim \mathrm{Po}(4) $ b  $ X \sim \mathrm{Po}(2.3) $ c  $ X \sim \mathrm{Po}(12) $

3 For each of the following distributions, write down the probability generating function,  $ \mathrm{G}_{X}(t) $.

a  $ X \sim \text{Geo}(0.1) $ b  $ X \sim \text{Geo}(0.7) $ c  $ X \sim \text{Geo}(0.4) $

4 Find the probability generating function for:


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>x</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>6</td><td style='text-align: center; word-wrap: break-word;'>7</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>P(X=x)</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{4} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{8} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{4} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{16} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{16} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{8} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{8} $</td></tr></table>

5 Find the probability generating function for:


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>x</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>6</td><td style='text-align: center; word-wrap: break-word;'>8</td><td style='text-align: center; word-wrap: break-word;'>10</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>P(X=x)</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{16} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{4} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{3}{8} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{4} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{16} $</td></tr></table>

Write your answer in the form $at^{b}(1 + t^{2})^{c}$.

6 Find the probability distribution for the following probability generating function.

 $$ G_{X}(t)=\frac{t^{3}}{6}(2+t^{4}+2t^{8}) $$ 

7 Find the probability distribution for the following probability generating function.

 $$ \mathrm{G}_{X}(t)=\left(\frac{4}{5}+\frac{t}{5}\right)^{7} $$ 

8 A distribution has a probability generating function of:

 $$ G_{X}(t)=\frac{1}{3}\bigg(\frac{2+t}{2-t}\bigg) $$ 

a Find the probabilities for when x = 0, 1, 2, 3.

b Find a general formula for  $ \mathrm{P}(X=k), k \geqslant 1 $.

9 Independent trials, each with the probability of ‘success’ $p$, are carried out. The random variable $X$ counts the number of trials up to and including that on which the first success is obtained. Write down an expression for $P(X=x)$ for $x=1,2,\ldots$. Show that the probability generating function of $X$ is $G_{X}(t)=pt(1-qt)^{-1}$.

10 Consider the probability generating function  $ G_{X}(t) = \frac{k}{(5 - 2t)^{2}} $. Find the value of k.

<!-- page 299 -->

### 12.2 Mean  $ (\mathrm{E}(X)) $ and variance  $ (\mathrm{Var}(X)) $ using the probability generating function

In this section, we shall find the mean and variance using the PGF of a discrete random variable. We shall discover why expressing the probabilities in a functional way using a polynomial is a very powerful tool.

Here are a few important results that we shall use:

 $$ \mathrm{E}(X)=\sum_{\forall x}x\mathrm{P}(X=x) $$ 

 $$ \mathrm{E}(X^{2})=\sum_{\forall x}x^{2}\mathrm{P}(X=x) $$ 

 $$  Var(X)=E(X^{2})-[E(X)]^{2} $$ 

These lead to the following results. First, as shown in Section 12.1, Key point 12.2:

 $$ \mathrm{E}(X)=\mathrm{G}^{\prime}_{X}(1) $$ 

Differentiating  $ \mathrm{G}_{X}(t) $ twice:

 $$ \mathrm{G}_{X}(t)=\sum_{x}t^{x}\mathrm{P}(X=x) $$ 

 $$ \mathrm{G}^{\prime}_{X}(t)=\sum_{x}xt^{x-1}\mathrm{P}(X=x) $$ 

 $$ \mathrm{G}_{X}^{\prime \prime}(t)=\sum_{x}x(x-1)t^{x-2}\mathrm{P}(X=x) $$ 

Evaluating at t = 1:

 $$ \mathrm{G}_{X}^{\prime \prime}(1)=\sum_{x}x(x-1)\mathrm{P}(X=x) $$ 

 $$ \mathrm{G}_{X}^{\prime \prime}(1)=\sum_{x}(x^{2}-x)\mathrm{P}(X=x) $$ 

 $$ \mathrm{G}_{X}^{\prime \prime}(1)=\sum_{x}x^{2}\mathrm{P}(X=x)-\sum_{x}x\mathrm{P}(X=x) $$ 

 $$ \mathrm{G}_{X}^{\prime \prime}(1)=\mathrm{E}(X^{2})-\mathrm{E}(X) $$ 

 $$ \mathrm{E}(X^{2})=\mathrm{G}_{X}^{\prime\prime}(1)+\mathrm{G}_{X}^{\prime}(1) $$ 

 $$  Var(X)=E(X^{2})-[E(X)]^{2} $$ 

Therefore:

 $$  Var(X)=G^{\prime \prime}_{X}(1)+G^{\prime}_{X}(1)-[G^{\prime}_{X}(1)]^{2} $$ 

as shown in Key point 12.7.

<div style="text-align: center;"><img src="imgs/img_in_image_box_25_1276_63_1310.jpg" alt="Image" width="3%" /></div>


### KEY POINT 12.7

 $$  Var(X)=G^{\prime}_{X}(1)+G^{\prime}_{X}(1)-[G^{\prime}_{X}(1)]^{2} $$

<!-- page 300 -->

### WORKED EXAMPLE 12.6

A bag contains five red balls and three green balls. The balls are taken out one at a time, the colour is noted, and then it is replaced. Let X be the number of times a ball is removed until a green ball is chosen.

a State the PGF of X.

b Calculate the mean and variance of X.

## Answer

a In this question, we can see that the outcomes follow a geometric distribution:

 $$ X\sim\mathrm{Geo}\left(\frac{3}{8}\right) $$ 

Always define a random variable before using it. Here,  $ p = \frac{3}{8} $ and  $ q = \frac{5}{8} $.

Its PGF is:

 $$ \begin{array}{l}\mathrm{G}_{X}(t)=\frac{p t}{1-q t}\\ =\frac{\left(\frac{3}{8}\right)t}{1-\left(\frac{5}{8}\right)t}\\ =\frac{3t}{8-5t}\end{array} $$ 

Simplify.

We will need to differentiate this twice in part b.

b

 $$ \begin{aligned}\mathrm{G}^{\prime}_{X}(t)&=\frac{3(8-5t)-3t(-5)}{(8-5t)^{2}}\\&=\frac{24}{(8-5t)^{2}}\\&=24(8-5t)^{-2}\end{aligned} $$ 

The quotient rule is needed here.

 $$ \begin{array}{l} \displaystyle \mathrm{G}_{x}^{\prime \prime}(t)=24 \times -5 \times -2(8 - 5t)^{-3} \\ \displaystyle \qquad =  \frac{240}{(8 - 5t)^{3}} \end{array} $$ 

 $$ G_{X}^{\prime}(1)=\frac{24}{9}=2\frac{2}{3} $$ 

Find the second derivative.

Use the chain rule.

 $$ G_{X}^{\prime\prime}(1)=\frac{240}{27}=8\frac{8}{9} $$ 

Evaluate at t = 1.

 $$ \mathrm{E}(X)=\mathrm{G}^{\prime}_{X}(1)=2\frac{2}{3} $$ 

 $$ \begin{aligned}\mathrm{Var}(X)&=\mathrm{G}_{X}^{\prime\prime}(1)+\mathrm{G}_{X}^{\prime}(1)-[\mathrm{G}_{X}^{\prime}(1)]^{2}\\&=\frac{80}{9}+\frac{8}{3}-\frac{64}{9}\\&=\frac{40}{9}=4\frac{4}{9}\end{aligned} $$ 

Use the standard results.

Generally, the previous results offer only a different way of calculating the mean and variance. Worked examples 12.7 and 12.8 demonstrate some properties of distributions using the probability generating functions.

<!-- page 301 -->

<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Prove that for  $ X \sim \text{Po}(\lambda) $:</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>a</td><td style='text-align: center; word-wrap: break-word;'>E(X) =  $ \lambda $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>b</td><td style='text-align: center; word-wrap: break-word;'>G $ _{X}^{\prime}(t) $ =  $ \lambda $ $ e^{\lambda(t-1)} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>a</td><td style='text-align: center; word-wrap: break-word;'>G $ _{X}^{\prime}(t) $ =  $ e^{\lambda(t-1)} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>b</td><td style='text-align: center; word-wrap: break-word;'>G $ _{X}^{\prime}(t) $ =  $ \lambda $ $ e^{\lambda(t-1)} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>a</td><td style='text-align: center; word-wrap: break-word;'>G $ _{X}^{\prime}(1) $ =  $ \lambda $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>b</td><td style='text-align: center; word-wrap: break-word;'>G $ _{X}^{\prime}(1) $ =  $ \lambda $ $ e^{\lambda(t-1)} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>a</td><td style='text-align: center; word-wrap: break-word;'>G $ _{X}^{\prime}(1) $ =  $ \lambda $ $ e^{\lambda(t-1)} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>b</td><td style='text-align: center; word-wrap: break-word;'>G $ _{X}^{\prime}(1) $ =  $ \lambda $ $ e^{\lambda(t-1)} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>a</td><td style='text-align: center; word-wrap: break-word;'>G $ _{X}^{\prime\prime}(t) $ =  $ \lambda^{2} $ $ e^{\lambda(t-1)} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>b</td><td style='text-align: center; word-wrap: break-word;'>G $ _{X}^{\prime\prime}(1) $ =  $ \lambda^{2} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>a</td><td style='text-align: center; word-wrap: break-word;'>G $ _{X}^{\prime\prime}(1) $ =  $ \lambda $ $ e^{\lambda(t-1)} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>a</td><td style='text-align: center; word-wrap: break-word;'>G $ _{X}^{\prime\prime}(1) $ =  $ G_{X}^{\prime}(1) + G_{X}^{\prime}(1) - [G_{X}^{\prime}(1)]^{2} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>a</td><td style='text-align: center; word-wrap: break-word;'>G $ _{X}^{\prime\prime}(1) $ =  $ \lambda $ $ e^{\lambda(t-1)} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>a</td><td style='text-align: center; word-wrap: break-word;'>G $ _{X}^{\prime\prime}(1) $ =  $ \lambda</td></tr></table>

We shall use the properties of the mean and variance to calculate unknown probabilities using the PGF, as in Worked example 12.8.

### WORKED EXAMPLE 12.8

A discrete random variable has the following probability distribution.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>x</td><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>P(X=x)</td><td style='text-align: center; word-wrap: break-word;'>a</td><td style='text-align: center; word-wrap: break-word;'>b</td><td style='text-align: center; word-wrap: break-word;'>c</td></tr></table>

The mean is  $ \frac{2}{3} $ and the variance is  $ \frac{5}{9} $. Find a, b and c.

## Answer

First, express this using the PGF:

 $$ \mathbf{G}_{X}(t)=a+bt+ct^{2} $$ 

 $$ G_{X}^{\prime}(t)=b+2c t $$ 

 $$ G_{X}^{\prime \prime}(t)=2c $$ 

 $$ \mathrm{G}_{X}(t)=\sum_{x}t^{x_{i}}\mathrm{P}(X=x_{i}) $$ 

 $$ G_{X}(1)=a+b+c $$ 

Differentiate twice to find the expectation and variance.

 $$ G_{X}^{\prime}(1)=b+2c $$ 

 $$ G_{x}^{\prime \prime}(1)=2c $$ 

Evaluate at t = 1.

<!-- page 302 -->

<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>1 =  $ a + b + c $ (1)</td><td style='text-align: center; word-wrap: break-word;'>$ G_{Y}(1) = 1 $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ \frac{2}{3} = b + 2c $ (2)</td><td style='text-align: center; word-wrap: break-word;'>$ \mathrm{E}(X) = G_{X}^{\prime}(1) $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ \frac{5}{9} = 2c + \frac{2}{3} - \frac{4}{9} $</td><td style='text-align: center; word-wrap: break-word;'>$ \mathrm{Var}(X) = G_{X}^{\prime\prime}(1) + G_{X}^{\prime}(1) - [G_{X}^{\prime}(1)]^{2} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{3} = 2c $ (3)</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>From (3):  $ c = \frac{1}{6} $</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>From (2):  $ b = \frac{1}{3} $</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>From (1):  $ a = \frac{1}{2} $</td><td style='text-align: center; word-wrap: break-word;'></td></tr></table>

We can use the derivatives of $G_{X}(t)$ to help us find $P(X=r)$ of probability generating functions. We use the idea that the expansion of a function of this type coincides with its Maclaurin expansion.

Consider  $  \mathrm{G}_{X}(t) = \frac{t}{2 - t}  $.

This can be expanded binomially to give  $ \frac{t}{2} + \frac{t^{2}}{4} + \frac{t^{3}}{8} + \frac{t^{4}}{16} + \cdots $

The probabilities for each r can be seen here clearly, but what if the expansion is not a known one?

We can consider the Maclaurin expansion of any function as:

 $$ \mathrm{G}_{X}(t)=\mathrm{G}_{X}(0)+\mathrm{G}_{X}^{\prime}(0)t+\frac{\mathrm{G}_{X}^{\prime \prime}(0)t^{2}}{2!}+\frac{\mathrm{G}_{X}^{\prime \prime \prime}(0)t^{3}}{3!}+\cdots $$ 

And so the probabilities could also be calculated using:

 $$ \mathrm{P}(X=r)=\frac{\mathrm{G}_{X}^{(r)}(0)}{r!} $$ 

where  $  \mathrm{G}_{X}^{(r)}(t)  $ is the rth derivative of  $  \mathrm{G}_{X}(t)  $.

## EXERCISE 12B

1 For the following probability generating function:

 $$ \mathbf{G}_{X}(t)=\frac{t^{2}}{10}(1+2t+3t^{2}+2t^{4}+t^{5}) $$ 

a Find  $ G_{X}^{\prime}(1) $.

b Find  $ G_{X}^{\prime\prime}(1) $. c Find E(X).



d Find Var(X).

2 For the following probability generating function:

 $$ \mathrm{G}_{X}(t)=\frac{t}{16}(1+4t+6t^{2}+4t^{3}+t^{4}) $$ 

a Find  $ G_{X}^{\prime}(1) $

b Find  $ G_{X}^{\prime\prime}(1) $

d Find Var(X).

3 Find  $ \mathrm{E}(X) $ and  $ \mathrm{Var}(X) $ of the following probability generating function.

 $$ G_{X}(t)=\frac{t^{4}}{10}(3+5t+t^{3}+t^{5}) $$

<!-- page 303 -->

4 Find  $ \mathrm{E}(X) $ and  $ \mathrm{Var}(X) $ of the following probability generating function.

 $$ \mathrm{G}_{X}(t)=\frac{9}{(5-2t)^{2}} $$ 

5 In a game, the probability that player A wins on her rth go can be described as a discrete random variable $X$, with probability function $\mathrm{P}(X=r)=\frac{1}{2^r}$, for $r=1,2,3,\ldots$.

a Find the probability generating function.

b Find  $ E(X) $ and  $ \mathrm{Var}(X) $.

6 Find  $ \mathrm{E}(X) $ and  $ \mathrm{Var}(X) $ of the following probability generating function,

 $$ \mathrm{G}_{X}(t)=\frac{p}{1-qt} $$ 

where q = 1 - p.

7 Find  $ \mathrm{E}(X) $ and  $ \mathrm{Var}(X) $ of the following probability generating function.

 $$ \mathrm{G}_{X}(t)=\frac{t+2}{(2-t^{2})(4-t)} $$ 

M 8 A regular octagonal spinner is made up of eight isosceles triangles. Two of the triangles have a score of 2, three triangles have a score of ‘a’ and three triangles have a score of ‘b’, where a < b. The expectation and variance of the spinner are given by:

 $$  E(X)=4.25 $$ 

 $$  Var(X)=\frac{75}{16} $$ 

a Find an expression for $G_{X}(t)$, $G_{X}^{\prime}(t)$ and $G_{X}^{\prime\prime}(t)$.

b Hence, find the values of a and b.

All the examples covered so far have involved discrete random variables where each value of the random variable has a probability associated with it. This means we can set up the probability generating function easily and calculate the mean and variance from this.

This is not possible to do if the random variable is continuous. To calculate the mean and variance for a continuous random variable we use the moment generating function. This technique also works for a discrete random variable.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>$ M_{X}(\theta) = \sum_{x} \mathrm{e}^{\theta x} \mathrm{P}(X = x) $</td><td style='text-align: center; word-wrap: break-word;'>For a discrete random variable,  $ X $.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ M_{X}(\theta) = \int \mathrm{e}^{\theta x} \mathrm{f}(x) \, \mathrm{d}x $</td><td style='text-align: center; word-wrap: break-word;'>For a continuous random variable,  $ X $, with a probability density function  $ f(x) $.</td></tr></table>

The following results come from the moment generating function.

 $$ \mathrm{E}(X)=M^{\prime}(0) $$ 

 $$ \mathrm{E}(X^{r})=M^{r}(0) $$ 

 $$ \mathrm{Var}(X)=M^{\prime \prime}(0)-[M^{\prime}(0)]^{2} $$ 

This is beyond the Further Mathematics course.

<!-- page 304 -->

### 12.3 The sum of independent random variables

In AS & A Level Probability & Statistics 2, Chapter 3, you learned that, if there are two independent variables of the same distribution (for example the normal),  $ X \sim \mathrm{N}(\mu_1, \sigma_1^2) $ and  $ Y \sim \mathrm{N}(\mu_2, \sigma_2^2) $, we can create the distribution of  $ X + Y $. This will be  $ X + Y \sim N(\mu_1 + \mu_2, \sigma_1^2 + \sigma_2^2) $. The same is true for the Poisson distribution. We need to have some method for finding the PGF of  $ X + Y $ for any pairing of independent random variables X and Y. We will consider discrete random variables in this case.

Consider the following two distributions as an example. In Section 12.4, we will extend this idea to three or more random variables.

Let X have the following probability distribution.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>x</td><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ P(X=x) $</td><td style='text-align: center; word-wrap: break-word;'>$ p_{0} $</td><td style='text-align: center; word-wrap: break-word;'>$ p_{1} $</td><td style='text-align: center; word-wrap: break-word;'>$ p_{2} $</td></tr></table>

Let Y have the following probability distribution.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>y</td><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ P(Y=y) $</td><td style='text-align: center; word-wrap: break-word;'>q_{0}</td><td style='text-align: center; word-wrap: break-word;'>q_{1}</td><td style='text-align: center; word-wrap: break-word;'>q_{2}</td></tr></table>

Then the distribution of  $ X + Y $ is:


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>$ x + y $</td><td style='text-align: center; word-wrap: break-word;'>$ \text{P}(X + Y = x + y) $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>$ \text{P}(X = 0 \cap Y = 0) $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>$ \text{P}(X = 0 \cap Y = 1) + \text{P}(X = 1 \cap Y = 0) $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>$ \text{P}(X = 0 \cap Y = 2) + \text{P}(X = 1 \cap Y = 1) + \text{P}(X = 2 \cap Y = 0) $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>$ \text{P}(X = 1 \cap Y = 2) + \text{P}(X = 2 \cap Y = 1) $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>$ \text{P}(X = 2 \cap Y = 2) $</td></tr></table>

If $X$ and $Y$ are independent, then $\mathrm{P}(X=x_i \cap Y=y_j)=\mathrm{P}(X=x_i) \times \mathrm{P}(Y=y_j)=p_i q_j$.

The previous table now becomes:


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>$ x+y $</td><td style='text-align: center; word-wrap: break-word;'>$ \mathrm{P}(X+Y=x+y) $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>$ p_{0}q_{0} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>$ p_{1}q_{0}+p_{0}q_{1} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>$ p_{2}q_{0}+p_{1}q_{1}+p_{0}q_{2} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>$ p_{2}q_{1}+p_{1}q_{2} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>$ p_{2}q_{2} $</td></tr></table>

Now consider the PGF of  $ X + Y $:

 $$ \mathrm{G}_{X+Y}(t)=p_{0}q_{0}+(p_{1}q_{0}+p_{0}q_{1})t+(p_{2}q_{0}+p_{1}q_{1}+p_{0}q_{2})t^{2}+(p_{2}q_{1}+p_{1}q_{2})t^{3}+p_{2}q_{2}t^{4} $$ 

This can be rewritten as:

 $$ G_{X+Y}(t)=(p_{0}+p_{1}t+p_{2}t^{2})(q_{0}+q_{1}t+q_{2}t^{2}) $$ 

And we notice that these are the PGFs of X and of Y:

 $$ \mathrm{G}_{X+Y}(t)=\mathrm{G}_{X}(t)\times\mathrm{G}_{Y}(t) $$ 

This is called the convolution theorem.

<!-- page 305 -->

## The convolution theorem

Let $X$ and $Y$ be two independent discrete random variables with PGFs $G_X(t)$ and $G_Y(t)$. The probability generating function of $X + Y$ is given as $G_{X+Y}(t) = G_X(t) \times G_Y(t)$, as shown in Key point 12.8.

<div style="text-align: center;"><img src="imgs/img_in_image_box_34_278_74_312.jpg" alt="Image" width="3%" /></div>


### KEY POINT 12.8

 $$ \mathrm{G}_{X+Y}(t)=\mathrm{G}_{X}(t)\times\mathrm{G}_{Y}(t) $$ 

We will use this result directly to find the probability generating function of the sum of two independent random variables.

### WORKED EXAMPLE 12.9

The discrete random variables X and Y have the following probability distributions.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>x</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>P(X=x)</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{4} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{4} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{2} $</td></tr></table>


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>y</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>P(Y=y)</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{3} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{3} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{3} $</td></tr></table>

Assuming that X and Y are independent:

a find the PGF of  $ X + Y $

b write down the probability distribution of  $ X + Y $

c show that  $ \mathrm{E}(X + Y) = \mathrm{E}(X) + \mathrm{E}(Y) $ and  $ \mathrm{Var}(X + Y) = \mathrm{Var}(X) + \mathrm{Var}(Y) $.

## Answer


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>$ G_{X}(t) = \frac{1}{4}t + \frac{1}{4}t^{2} + \frac{1}{2}t^{3} $</td><td style='text-align: center; word-wrap: break-word;'>First, consider the PGFs of X and Y.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>and  $ G_{Y}(t) = \frac{1}{3}t^{2} + \frac{1}{3}t^{4} + \frac{1}{3}t^{6} $</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ G_{X+Y}(t) = G_{X}(t) \times G_{Y}(t) $</td><td style='text-align: center; word-wrap: break-word;'>Since X and Y are assumed to be independent, we can use the convolution theorem.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ G_{X+Y}(t) = \left(\frac{1}{4}t + \frac{1}{4}t^{2} + \frac{1}{2}t^{3}\right) \times \left(\frac{1}{3}t^{2} + \frac{1}{3}t^{4} + \frac{1}{3}t^{6}\right) $</td><td style='text-align: center; word-wrap: break-word;'>Take out  $ \frac{1}{4}t \times \frac{1}{3}t^{2} $ as a common factor.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ G_{Y}(t) = \frac{1}{3}t^{2} + \frac{1}{3}t^{4} + \frac{1}{3}t^{6} $</td><td style='text-align: center; word-wrap: break-word;'>Multiply.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ G_{X}(t) = \frac{1}{3}t^{2} + \frac{1}{3}t^{4} + \frac{1}{3}t^{6} $</td><td style='text-align: center; word-wrap: break-word;'>Simplify.</td></tr></table>

<!-- page 306 -->

<div style="text-align: center;">b</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>$ x+y $</td><td style='text-align: center; word-wrap: break-word;'>$ \mathrm{P}(X+Y=x+y) $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{12} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{12} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{4} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>6</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{12} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{4} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>8</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{12} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>9</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{6} $</td></tr></table>

 $$ \mathbf{G}_{X+Y}(t)=\frac{1}{12}(t^{3}+t^{4}+3t^{5}+t^{6}+3t^{7}+t^{8}+2t^{9}) $$ 

Remember the powers of $t$ relate to the values of the distribution, and the coefficients relate to their respective probabilities.

 $$ \mathbf{G}^{\prime}_{X+Y}(t)=\frac{1}{12}(3t^{2}+4t^{3}+15t^{4}+6t^{5}+21t^{6}+8t^{7}+18t^{8}) $$ 

Find both derivatives first.

 $$ G^{^{\prime \prime}}_{X+Y}(t)=\frac{1}{12}(6t+12t^{2}+60t^{3}+30t^{4}+126t^{5}+56t^{6}+144t^{7}) $$ 

 $$ \begin{aligned}G_{X+Y}^{\prime}(1)&=\frac{1}{12}(3+4+15+6+21+8+18)\\&=\frac{75}{12}=6\frac{1}{4}\end{aligned} $$ 

Evaluate the derivatives at $t=1$.

 $$ \begin{aligned}G_{X+Y}^{\prime \prime}(1)&=\frac{1}{12}(6+12+60+30+126+56+144)\\&=\frac{434}{12}=36\frac{1}{6}\end{aligned} $$ 

 $$ \mathrm{E}(X+Y)=\mathrm{G}_{X+Y}^{\prime}(1)=6\frac{1}{4} $$ 

 $$ \mathrm{E}(X+Y)=\mathrm{G}^{\prime}_{X}(1) $$ 

 $$ \mathrm{Var}(X+Y)=\frac{434}{12}+\frac{75}{12}-\left[\frac{75}{12}\right]^{2}=\frac{161}{48}=3\frac{17}{48} $$ 

 $$ \mathrm{Var}(X)=\mathrm{G}_{X}^{\prime\prime}(1)+\mathrm{G}_{X}^{\prime}(1)-[\mathrm{G}_{X}^{\prime}(1)]^{2} $$ 

Similarly:

 $$ \mathbf{G}_{X}(t)=\frac{1}{4}t+\frac{1}{4}t^{2}+\frac{1}{2}t^{3} $$ 

 $$ \mathbf{G}^{\prime}_{X}(t)=\frac{1}{4}+\frac{2}{4}t+\frac{3}{2}t^{2} $$ 

 $$ G_{X}^{\prime}(1)=\frac{9}{4} $$ 

 $$ G^{\prime \prime}_{X}(t)=\frac{1}{2}+3t $$ 

 $$ G_{X}^{\prime \prime}\left(1\right)=\frac{7}{2} $$ 

 $$ \mathrm{E}(X)=\frac{9}{4} $$ 

 $$ \mathrm{Var}(X)=\frac{7}{2}+\frac{9}{4}-\left(\frac{9}{4}\right)^{2}=\frac{11}{16} $$

<!-- page 307 -->

And:

 $$ \mathrm{G}_{Y}(t)=\frac{1}{3}t^{2}+\frac{1}{3}t^{4}+\frac{1}{3}t^{6} $$ 

Consider $\mathrm{E}(Y)$ and $\mathrm{Var}(Y)$ in the same way as for $\mathrm{E}(X)$ and $\mathrm{Var}(X)$.

 $$ \mathbf{G}^{\prime}_{Y}(t)=\frac{2}{3}t+\frac{4}{3}t^{3}+2t^{5} $$ 

 $$ G^{\prime}_{Y}(1)=4 $$ 

 $$ G_{Y}^{\prime}(t)=\frac{2}{3}+4t^{2}+10t^{4} $$ 

 $$ G^{\prime \prime}_{Y}(1)=\frac{44}{3} $$ 

 $$ \mathrm{E}(Y)=4 $$ 

 $$ \mathrm{Var}(Y)=\frac{44}{3}+4-4^{2}=\frac{8}{3} $$ 

 $$ \mathrm{E}(X)+\mathrm{E}(Y)=\frac{9}{4}+4=6\frac{1}{4}=\mathrm{E}(X+Y) $$ 

 $$  Var(X)+Var(Y)=\frac{11}{16}+\frac{8}{3}=\frac{161}{48}=3\frac{17}{48}=Var(X+Y) $$ 

Therefore,  $ \mathrm{E}(X + Y) = \mathrm{E}(X) + \mathrm{E}(Y) $ and

Compare the two sets of results.

 $$  Var(X+Y)=Var(X)+Var(Y). $$ 

## The PGF of a function of a random variable

Consider a discrete random variable that is a function of another variable, as seen in Chapter 8.

 $ Y = aX + b $, where  $ X $ has PGF  $ G_X(t) $.

We can find the PGF of Y by considering the alternative definition of the PGF:

 $$ G_{X}(t)=\mathrm{E}(t^{X}) $$ 

Consider $Y = aX + b$, then:

 $$ \begin{array}{l}\mathrm{G}_{Y}(t)=\mathrm{E}(t^{Y})=\mathrm{E}(t^{a X+b})\\{\quad}=\mathrm{E}(t^{a X}t^{b})=t^{b}\mathrm{E}(t^{a X})\\{\quad}=t^{b}\mathrm{E}[(t^{a})^{\times}]\\{\quad}=t^{b}\mathrm{G}_{X}(t^{a})\\\end{array} $$ 

Therefore,  $  \mathrm{G}_{aX+b}(t) = t^b \mathrm{G}_X(t^a)  $, as shown in Key point 12.9.

<div style="text-align: center;"><img src="imgs/img_in_image_box_18_1067_60_1103.jpg" alt="Image" width="3%" /></div>


### KEY POINT 12.9

 $$ \mathrm{G}_{aX+b}(t)=t^{b}\mathrm{G}_{X}(t^{a}) $$ 

From this definition, we can now formally reproduce some of the results shown in Chapter 11.

Let us find the expectation and variance of $Y = aX + b$ using the PGF of $X$.

<!-- page 308 -->

<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>$ G_{aX+b}(t)=t^{b}G_{X}(t^{a}) $</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ G_{aX+b}^{\prime}(t)=bt^{b-1}G_{X}(t^{a})+at^{a-1}t^{b}G_{X}^{\prime}(t^{a}) $</td><td style='text-align: center; word-wrap: break-word;'>Discrete using the product rule and the chain rule.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ G_{aX+b}^{\prime}(1)=b1^{b-1}G_{X}(1^{a})+a1^{a-1}1^{b}G_{X}^{\prime}(1^{a}) $</td><td style='text-align: center; word-wrap: break-word;'>Discrete using the product rule and the chain rule.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ G_{aX+b}^{\prime}(1)=b\times1+aG_{X}^{\prime}(1) $</td><td style='text-align: center; word-wrap: break-word;'>Discrete using the product rule and the chain rule.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ E(aX+b)=aE(X)+b $</td><td style='text-align: center; word-wrap: break-word;'>Discrete using the product rule and the chain rule.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ G_{aX+b}^{\prime\prime}(t)=b(b-1)t^{b-2}G_{X}(t^{a})+abt^{a-1}t^{b-1}G_{X}^{\prime}(t^{a}) $</td><td style='text-align: center; word-wrap: break-word;'>Discrete using the product rule and the chain rule.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ G_{aX+b}^{\prime\prime}(t)=b(a+b-1)t^{a+b-2}G_{X}^{\prime}(t^{a})+a^{2}t^{a-1}t^{a-1}t^{b}G_{X}^{\prime\prime}(t^{a}) $</td><td style='text-align: center; word-wrap: break-word;'>Discrete using the product rule and the chain rule.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ G_{aX+b}^{\prime\prime}(1)=b(b-1)+abG_{X}^{\prime}(1)+a(a+b-1)G_{X}^{\prime}(1)+a^{2}G_{X}^{\prime\prime}(1) $</td><td style='text-align: center; word-wrap: break-word;'>Discrete using the product rule and the chain rule.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ Var(aX+b)=G_{aX+b}^{\prime\prime}(1)+G_{aX+b}^{\prime}(1)-[G_{aX+b}^{\prime}(1)]^{2} $</td><td style='text-align: center; word-wrap: break-word;'>$ Var(X)=G_{X}^{\prime\prime}(1)+E(X)-[E(X)]^{2} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ Var(aX+b)=b(b-1)+abE(X)+a(a+b-1)E(X)+a^{2}G_{X}^{\prime\prime}(1)+[aE(X)+b]-[aE(X)+b]^{2} $</td><td style='text-align: center; word-wrap: break-word;'>$ Var(X)=G_{X}^{\prime\prime}(1)+E(X)-[E(X)]^{2} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ =b^{2}-b+abE(X)+a^{2}E(X)+abE(X)-aE(X)+a^{2}G_{X}^{\prime\prime}(1)+aE(X)+b-a^{2}[E(X)]^{2}-2abE(X)-b^{2}+a^{2}E(X)+a^{2}G_{X}^{\prime\prime}(1)-[E(X)]^{2}] $</td><td style='text-align: center; word-wrap: break-word;'>Discrete using the product rule and the chain rule.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ Var(aX+b)=a^{2}Var(X) $</td><td style='text-align: center; word-wrap: break-word;'>Discrete using the product rule and the chain rule.</td></tr></table>

### WORKED EXAMPLE 12.10

A discrete random variable, $X$, has the probability distribution:


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>x</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ P(X=x) $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{9} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{2}{9} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{3}{9} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{2}{9} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{9} $</td></tr></table>

a Find  $ G_{X}(t) $, the PGF of X.

b Given that $Y=4-7X$, find $G_{Y}(t)$, the PGF of $Y$.

Answer

 $$ \begin{aligned}\mathrm{G}_{X}(t)&=\frac{1}{9}t+\frac{2}{9}t^{2}+\frac{3}{9}t^{3}+\frac{2}{9}t^{4}+\frac{1}{9}t^{5}\\&=\frac{t}{9}(1+2t+3t^{2}+2t^{3}+t^{4})\end{aligned} $$ 

 $$ G_{X}(t) $$ 

 $$ G_{Y}(t)=G_{-7X+4}(t) $$ 

 $$ G_{-7X+4}(t)=t^{4}G_{X}(t^{-7}) $$ 

 $$ \mathbf{G}_{aX+b}(t)=t^{b}\mathbf{G}_{X}(t^{a}) $$ 

 $$ \mathrm{G}_{-7X+4}(t)=t^{4}\times\frac{t^{-7}}{9}(1+2(t^{-7})+3(t^{-7})^{2}+2(t^{-7})^{3}+(t^{-7})^{4}) $$ 

 $$ \mathbf{G}_{Y}(t)=\frac{1}{9t^{3}}\bigg(1+\frac{2}{t^{7}}+\frac{3}{t^{14}}+\frac{2}{t^{21}}+\frac{1}{t^{28}}\bigg) $$

<!-- page 309 -->

1 A discrete random variable X has probability distribution:


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>x</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ \mathrm{P}(X=x) $</td><td style='text-align: center; word-wrap: break-word;'>0.4</td><td style='text-align: center; word-wrap: break-word;'>0.6</td></tr></table>

A discrete random variable Y has probability distribution:


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>y</td><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>P(Y=y)</td><td style='text-align: center; word-wrap: break-word;'>0.25</td><td style='text-align: center; word-wrap: break-word;'>0.25</td><td style='text-align: center; word-wrap: break-word;'>0.25</td><td style='text-align: center; word-wrap: break-word;'>0.25</td></tr></table>

Given that X and Y are independent, find:

a  $ G_{X}(t) $ b  $ G_{Y}(t) $ c  $ G_{X+Y}(t) $

2 A discrete random variable X has probability distribution:


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>x</td><td style='text-align: center; word-wrap: break-word;'>-2</td><td style='text-align: center; word-wrap: break-word;'>-1</td><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>P(X=x)</td><td style='text-align: center; word-wrap: break-word;'>0.1</td><td style='text-align: center; word-wrap: break-word;'>0.2</td><td style='text-align: center; word-wrap: break-word;'>0.4</td><td style='text-align: center; word-wrap: break-word;'>0.2</td><td style='text-align: center; word-wrap: break-word;'>0.1</td></tr></table>

A discrete random variable Y has probability distribution:


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>y</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>P(Y=y)</td><td style='text-align: center; word-wrap: break-word;'>0.2</td><td style='text-align: center; word-wrap: break-word;'>0.2</td><td style='text-align: center; word-wrap: break-word;'>0.2</td><td style='text-align: center; word-wrap: break-word;'>0.2</td><td style='text-align: center; word-wrap: break-word;'>0.2</td></tr></table>

Given that X and Y are independent, find:

a  $ G_{X}(t) $ b  $ G_{Y}(t) $ c  $ G_{X+Y}(t) $

3 A discrete random variable, $X$, has the probability distribution:


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>x</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ P(X=x) $</td><td style='text-align: center; word-wrap: break-word;'>0.2</td><td style='text-align: center; word-wrap: break-word;'>0.5</td><td style='text-align: center; word-wrap: break-word;'>0.3</td></tr></table>

A discrete random variable, Y, has the probability distribution:


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>y</td><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>P(Y=y)</td><td style='text-align: center; word-wrap: break-word;'>0.3</td><td style='text-align: center; word-wrap: break-word;'>0.4</td><td style='text-align: center; word-wrap: break-word;'>0.3</td></tr></table>

a Find  $ G_{X}(t) $.

 $$ G_{Y}(t) $$ 

Hence, given that X and Y are independent:

c find  $ G_{X+Y}(t) $ d write down the probability distribution of  $ X + Y $.

4 Let  $ X \sim \text{Geo}(0.4) $ and  $ Y \sim \text{Geo}(0.6) $, where X and Y are independent.

a Write down an expression for  $ G_{X+Y}(t) $. b Express  $ \frac{5}{(5-2t)(5-3t)} $ in partial fractions.

c Hence, find  $ \mathrm{P}(X+Y=k) $ for k=2,3,4.

5 Let  $ X \sim \text{Bin}(3, 0.2) $ and  $ Y \sim \text{Po}(2) $, where X and Y are independent.

a Find the probability generating function for  $ X + Y $.

b Find the value of  $ \mathrm{E}(X + Y) $.

c Find the value of  $ G_{X+Y}^{\prime\prime}(t) $. Write your answer in the form:

 $$ \frac{2\mathrm{e}^{2t}}{125\mathrm{e}^{2}}(t+4)(at^{2}+bt+c) $$ 

d Find the value of  $ \mathrm{Var}(X + Y) $.

<!-- page 310 -->

P 6 Let  $ X \sim \mathrm{Po}(a) $ and  $ Y \sim \mathrm{Po}(b) $. Prove that if X and Y are independent:

a  $ \mathrm{E}(X+Y)=a+b $ b  $ \mathrm{Var}(X+Y)=a+b $

7 Let  $ G_{X}(t) = \frac{3t}{5 - 2t} $.

a For Y=5X, find G_{Y}(t).

b For Y=X+7, find G_{Y}(t).

8 Let  $  \mathrm{G}_{X}(t) = \mathrm{e}^{4(t-1)}  $.

a For $Y=X-1$, find $G_{Y}(t)$. b For $Y=3-2X$, find $G_{Y}(t)$.

P 9 A discrete random variable, X, has the probability generating function:

 $$ G_{X}(t)=\frac{3}{10-7t} $$ 

a Find the probability generating function for  $ Y = 3X + 4 $.

b Show that  $ E(Y) = 11 $.

c Find P(Y=k) for k=4,7,10.

### 12.4 Three or more random variables

In the previous sections, we considered only two random variables and only a linear combination of one random variable. If the variables are independent, we can generalise this to deal with more than two random variables, and also linear combinations of these variables, as shown in Key points 12.10 and 12.11.

<div style="text-align: center;"><img src="imgs/img_in_image_box_97_793_141_828.jpg" alt="Image" width="3%" /></div>


### KEY POINT 12.10

For independent random variables, $X_{i}$, with corresponding PGF $G_{X_{i}}(t)$, then:

 $$ \mathrm{G}_{X_{1}+\cdots+X_{n}}(t)=\mathrm{G}_{X_{1}}(t)\times\cdots\times\mathrm{G}_{X_{n}}(t) $$ 

If n independent discrete random variables all have the same PGF, then this formula reduces to:

 $$ \mathrm{G}_{X_{1}+\cdots+X_{n}}(t)=[\mathrm{G}_{\chi}(t)]^{n} $$ 

This is different from:

 $$ G_{nX}(t)=G_{X}(t^{n}) $$ 

<div style="text-align: center;"><img src="imgs/img_in_image_box_103_1100_144_1133.jpg" alt="Image" width="3%" /></div>


### KEY POINT 12.11

For independent random variables,  $ X_i $, with corresponding PGF  $ G_{X_i}(t) $, then:

 $$ \mathrm{G}_{aX_{1}+bX_{2}}=\mathrm{G}_{X_{1}}(t^{a})\times\mathrm{G}_{X_{2}}(t^{b}) $$

<!-- page 311 -->

Find the probability generating function for the total number of 8s when a fair eight-sided die is rolled six times.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td colspan="2">Answer\nWhen one die is rolled,  $ X $ has the following probability distribution, where  $ X $ = number of 8s:\n $ X $ 0 1\n $ P(X=x) $  $ \frac{7}{8} $  $ \frac{1}{8} $</td><td style='text-align: center; word-wrap: break-word;'>Find the PGF.\nThis is called a Bernoulli distribution.\nThese are all independent, so we can use the property  $ G_{aX_1+bX_2}=G_{X_1}(t^a) \times G_{X_2}(t^b) $.\nNotice that this is the same as the PGF of  $ Y \sim \text{Bin}(6, \frac{1}{8}) $.</td></tr><tr><td colspan="3">And so its PGF is  $ G_X(t) = \frac{7}{8} + \frac{1}{8}t $.\nSince we are rolling the die six times, we define  $ Y = X_1 + X_2 + ... + X_6 $.\nAnd so the PGF of  $ Y $ is  $ G_Y(t) = [G_X(t)]^6 $.\n $ G_Y(t) = \left(\frac{7}{8} + \frac{1}{8}t\right)^6 $</td></tr></table>

## EXERCISE 12D

1 Consider the discrete random variable $X$, with probability generating function:

 $$ \mathrm{G}_{X}(t)=\frac{t^{2}}{5}(4+t) $$ 

 $ X_{1} $ and  $ X_{2} $ are two independent observations. Given that  $ Y = X_{1} + X_{2} $, find:

a  $ G_{Y}(t) $ b the probability distribution of Y.

2 Consider the discrete random variable X, with probability distribution:


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>x</td><td style='text-align: center; word-wrap: break-word;'>-1</td><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>P(X=x)</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{4} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{2} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{4} $</td></tr></table>

Three independent observations of $X$ are taken and the values are added to form $Y$. Three independent observations of $X$ are taken and the values of each $X_{i}$ added to form $Y$ where $Y = X_{1} + X_{2} + X_{3}$.

a Find  $ G_{X}(t) $.

b Find  $ G_{y}(t) $.

3 Two independent random variables X and Y have corresponding probability generating functions:

 $$ G_{X}(t)=\mathrm{e}^{3(t-1)} $$ 

and

It is given that A = Y - X.

 $$ G_{Y}(t)=\mathrm{e}^{5(t-1)} $$

<!-- page 312 -->

a A student made the following attempt to find  $ G_{A}(t) $:

Step 1:  $ G_{X+Y}(t) = G_X(t) \times G_Y(t) $

Step 2: Therefore  $  \mathrm{G}_{Y-X}(t) = \mathrm{G}_Y(t) \div \mathrm{G}_X(t)  $

Step 3:  $  \mathrm{G}_{Y-X}(t) = \mathrm{e}^{5(t-1)} \div \mathrm{e}^{3(t-1)}  $

Step 4:  $  \mathrm{G}_{Y-X}(t) = \mathrm{e}^{2(t-1)}  $

Which step contains the error in the student's working?

b Find the correct probability generating function of A,  $ G_{A}(t) $.

4 Consider the discrete random variable X, with probability distribution:


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>X</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>P(X=x)</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{3} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{3} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{3} $</td></tr></table>

and Y, with probability distribution:


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>y</td><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>P(Y=y)</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{2} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{4} $</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{4} $</td></tr></table>

It is given that A = 2Y - 3X.

a Find  $ G_{X}(t) $. b Find  $ G_{Y}(t) $. c Find  $ G_{A}(t) $.

5 Consider the independent discrete random variables X, Y and Z, where:

 $$ G_{X}(t)=(0.7+0.3t)^{3} $$ 

 $$ G_{Y}(t)=(0.3+0.7t)^{4} $$ 

 $$ G_{Z}(t)=\frac{3t}{10-7t} $$ 

Find the probability generating function for the following.

a  $ A = 2X + Y + 1 $

 $$ \mathbf{b}\quad B=X-Y-3Z+4 $$ 

 $$ \begin{aligned}c\quad C=3X+2Y+Z-1\end{aligned} $$ 

6 An observation from  $ X \sim \text{Geo}(0.3) $ is taken five times:  $ X_1, \ldots, X_5 $.

a Find the probability generating function of  $ Y=(X_{1}+\ldots+X_{5}) $.

b Find P(Y ≤ 8) to 4 significant figures.

7 Let X be a discrete random variable with probability distribution:


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>x</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>P(X = x)</td><td style='text-align: center; word-wrap: break-word;'>0.2</td><td style='text-align: center; word-wrap: break-word;'>0.3</td><td style='text-align: center; word-wrap: break-word;'>0.5</td></tr></table>

Four independent observations are made. Y is the sum of these observations.

a Find the probability density function of Y.

b Find E(Y). c Find Var(Y).

8 Let  $ X_1 \sim \text{Geo}(0.1) $,  $ X_2 \sim \text{Geo}(0.2) $ and  $ X_3 \sim \text{Geo}(0.3) $.

Let  $ Y = 3X_1 + 2X_2 + X_3 $.

a Find  $ G_Y(t) $.

b Find  $ P(Y = 7) $.

<!-- page 313 -->

### EXPLORE 12.1

Consider two die, A and B. Each face on each die has an equal probability of occurring.

Die A has faces 1, 3, 4, 5, 6, 8.

Die B has faces 1, 2, 2, 3, 3, 4.

1 Find the probability generating function of each die and, hence, the probability generating function for Z, the sum of the scores on both die.

2 What do you notice about the probability distribution for the sum of scores?

## WORKED EXAM-STYLE QUESTION

Jamil and Yao are revising for a Maths exam by randomly selecting questions from a large question bank. They play a game by taking it in turns to answer questions. The first person to get a question right wins the game.

Jamil answers a question correctly  $ \frac{1}{4} $ of the time. Yao answers a question correctly  $ \frac{1}{5} $ of the time. Assume that all question attempts are independent. Let X be the total number of questions attempted. Jamil will start the game.

a Find the probability generating function for X.

b Find E(X).

c Find Var(X).

## Answer

a  $ X = 1 $ (Jamil starts the game and wins)

 $$ \mathrm{P}(X=1)=\frac{1}{4} $$ 

X = 2 (Jamil is incorrect, then Yao is correct).

 $$ \mathrm{P}(X=2)=\frac{3}{4}\times\frac{1}{5}=\frac{3}{20} $$ 

It is worth finding a few probabilities to spot any patterns in them. There may be a standard PGF that we can apply.

 $ X = 3 $ (Jamil incorrect, Yao incorrect, Jamil correct).

 $$ \mathrm{P}(X=3)=\left(\frac{3}{4}\times\frac{4}{5}\right)\times\frac{1}{4}=\left(\frac{3}{5}\right)\times\frac{1}{4} $$ 

 $$ \mathrm{P}(X=4)=\frac{3}{4}\times\frac{4}{5}\times\frac{3}{4}\times\frac{1}{5}=\left(\frac{3}{5}\right)\times\frac{3}{20} $$ 

 $$ \mathrm{P}(X=5)=\frac{3}{4}\times\frac{4}{5}\times\frac{3}{4}\times\frac{4}{5}\times\frac{1}{4}=\left(\frac{3}{5}\right)^{2}\times\frac{1}{4} $$ 

 $$ \mathrm{P}(X=6)=\frac{3}{4}\times\frac{4}{5}\times\frac{3}{4}\times\frac{4}{5}\times\frac{3}{4}\times\frac{1}{5}=\left(\frac{3}{5}\right)^{2}\times\frac{3}{20} $$ 

And so on.

<!-- page 314 -->

$$ \begin{aligned}\mathrm{G}_{X}(t)&=\frac{1}{4}t+\left(\frac{3}{5}\right)\left(\frac{1}{4}\right)t^{3}+\left(\frac{3}{5}\right)^{2}\left(\frac{1}{4}\right)t^{5}+\cdots\\&\quad+\left(\frac{3}{20}\right)t^{2}+\left(\frac{3}{5}\right)\left(\frac{3}{20}\right)t^{4}+\left(\frac{3}{5}\right)^{2}\left(\frac{3}{20}\right)t^{6}+\cdots\\&=\left(\frac{t}{4}\right)\left(\frac{1}{1-\frac{3}{5}t^{2}}\right)+\left(\frac{3t^{2}}{20}\right)\left(\frac{1}{1-\frac{3}{5}t^{2}}\right)\\&=\frac{5t+3t^{2}}{4(5-3t^{2})}\end{aligned} $$ 

We can look for a pattern in the odd and even values for X. When X is odd, Jamil wins. When X is even, Yao wins.

Each of these patterns is a sum to infinity of geometric series, so we can use the formula  $ S_{\infty} = \frac{a}{1 - r} $ from AS & A Level Pure Mathematics 1.

 $$ G_{X}(t)=\frac{5t+3t^{2}}{4(5-3t^{2})} $$ 

Write in closed form and simplify.

 $$ \begin{aligned}\mathrm{G}^{\prime}_{X}(t)&=\frac{4(5-3t^{2})(5+6t)-(5t+3t^{2})(4)(-6t)}{4^{2}(5-3t^{2})^{2}}\\&=\frac{100+120t-60t^{2}-72t^{3}+120t^{2}+72t^{3}}{4^{2}(5-3t^{2})^{2}}\\&=\frac{5(3t^{2}+6t+5)}{4(5-3t^{2})^{2}}\end{aligned} $$ 

Differentiate.

 $$ G_{X}^{\prime}(1)=\frac{35}{8} $$ 

Set t = 1 to find  $ \mathrm{E}(X) $.

 $$ \mathrm{E}(X)=\frac{35}{8} $$ 

 $$ \begin{aligned}G_{X}^{\prime \prime}(t)&=\frac{4(5-3t^{2})^{2}(5)(6t+6)-5(3t^{2}+6t+5)(4)(2)(-6t)(5-3t^{2})}{4^{2}(5-3t^{2})^{4}}\\&=\frac{(5-3t^{2})(5)(3t+3)-5(3t^{2}+6t+5)(-6t)}{2(5-3t^{2})^{3}}\\&=\frac{75t+75-45t^{3}-45t^{2}+90t^{3}+180t^{2}+150t}{2(5-3t^{2})^{3}}\\&=\frac{15(3t^{3}+9t^{2}+15t+5)}{2(5-3t^{2})^{3}}\\ \end{aligned} $$ 

 $$ G_{X}^{\prime \prime}(1)=30 $$ 

We need $G_{X}^{\prime\prime}(1)$ to find $\mathrm{Var}(X)$:

 $$ \mathrm{Var}(X)=\mathrm{G}_{X}^{\prime \prime}(1)+\mathrm{G}_{X}^{\prime}(1)-[\mathrm{G}_{X}^{\prime}(1)]^{2} $$ 

 $$ \mathrm{Var}(X)=\mathrm{G}^{\prime \prime}_{\lambda}(1)+\mathrm{G}^{\prime}_{\lambda}(1)-[\mathrm{G}^{\prime}_{\lambda}(1)]^{2} $$ 

 $$ \begin{aligned}&\mathrm{Var}(X)=30+\frac{35}{8}-\left(\frac{35}{8}\right)^{2}\\ &=\frac{975}{64}\\ \end{aligned} $$

<!-- page 315 -->

## Checklist of learning and understanding

For a discrete probability distribution:

The probability generating function is  $ G_{X}(t) = \mathrm{E}(t^{X}) = \sum_{x} t^{x} \mathrm{P}(X = x) $.

Standard probability generating functions:


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Probability distribution</td><td style='text-align: center; word-wrap: break-word;'>P(X=r)</td><td style='text-align: center; word-wrap: break-word;'>G_{X}(r)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Bin(n,p)</td><td style='text-align: center; word-wrap: break-word;'>$ ^n C_r q^{n-r} p^r $</td><td style='text-align: center; word-wrap: break-word;'>$ (q+pt)^n $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Po( $ \lambda $)</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{e^{-\lambda\lambda^r}}{r!} $</td><td style='text-align: center; word-wrap: break-word;'>e^{\lambda(t-1)}</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Geo(p)</td><td style='text-align: center; word-wrap: break-word;'>q^{r-1}p</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{pt}{1-qt} $</td></tr></table>

E(X) and Var(X):

 $ G_{X}(1) = 1 $

 $  \mathrm{E}(X) = G_{X}^{\prime}(1)  $

 $  \text{Var}(X) = G_X''(1) + G_X'(1) - [G_X'(1)]^2  $

 $  \text{Var}(X) = G_X''(1) + \mathrm{E}(X) - [\mathrm{E}(X)^2]  $

For two independent random variables:

 $ G_{X+Y}(t) = G_X(t) \times G_Y(t) $

To generalise to three or more random variables:

 $ G_{X_1 + \ldots + X_n}(t) = G_{X_1}(t) \times \ldots \times G_{X_n}(t) $

The probability generating function of a linear transformation:

 $ G_{aX+b}(t) = t^b G_X(t^a) $

<!-- page 316 -->

## END-OF-CHAPTER REVIEW EXERCISE 12

The discrete random variable $X$ is the number of times we throw a pair of fair die to get a sum of eight. Find the probability generating function, as well as the expected number of throws and the variance of $X$.

2 A discrete random variable, X, has the probability distribution function:

 $$ \mathrm{P}(X=x)=\frac{k}{\mathrm{e}^{x}}\ x=0,1,2,3,\ \ldots $$ 

a Find the value of k and the probability generating function.

b Find E(X).

c Find Var(X).

P 3 A game consists of rolling two die, one die with six sides, the other die with eight sides, and adding the scores together. Both die are fair, with the first numbered 1 to 6 and the second numbered 1 to 8. Show that the probability generating function of Z, where Z is the sum of the scores on the two die, is:

 $$ \frac{t^{2}}{48}\times\frac{(1-t^{6})(1-t^{8})}{1-t^{2}} $$ 

P 4 The variable $Y$ can take only the values 1, 2, 3, ... and is such that $\mathrm{P}(Y=r)=k\mathrm{P}(X=r)$, where $X\sim\mathrm{Po}(\lambda)$. Show that the probability generating function of $Y$ is given by:

 $$ \mathrm{G}_{Y}(t)=\frac{\mathrm{e}^{\lambda t}-1}{\mathrm{e}^{\lambda}-1} $$

<!-- page 317 -->

1 A random sample of 40 observations of a random variable $X$, and a random sample of 25 observations of a random variable $Y$, are taken. The sample means and unbiased estimates are:

 $$ \overline{\boldsymbol{x}}=13.6\quad\overline{\boldsymbol{y}}=11.2\quad s_{x}=6.3\quad s_{y}=7.1 $$ 

A test is performed at a significance level of  $ \alpha\% $ using the following hypotheses:

 $$  H_{0}\colon\mu_{x}-\mu_{\nu}=0 $$ 

 $$  H_{1}:\mu_{x}-\mu_{y}>0 $$ 

Given that $H_{0}$ is not rejected, find the possible values of $\alpha$.

A school is considering buying a large number of safety devices to install in the classrooms. The devices are designed to activate sprinklers if the temperature in the room exceeds  $ 65^{\circ} $C. A sample of the devices are tested by slowly increasing the temperature and noting the temperatures, in  $ {}^{\circ} $C, at which the sprinklers are activated. The results are as follows.

 $$ \begin{array}{l l l l l l}{57.8}&{62.9}&{63.7}&{71.2}&{60.6}&{69.5}&{64.7}&{65.7}\end{array} $$ 

Use a t-test and the 10% significance level to examine whether the mean temperature at which the sprinklers are activated is  $ 65^{\circ} $C. Assume that the sample is random and mean temperatures are normally distributed.

A random variable $X$ has a probability distribution, $f(x)$, given by:

a Show that  $ k = \frac{3\mathrm{e}^{3}}{\mathrm{e}^{3}-1} $.

 $$ \mathrm{f}(x)=\left\{\begin{aligned}&k\mathrm{e}^{-3x}&0\leqslant x\leqslant1\\ &0&otherwise\end{aligned}\right. $$ 

b Find the median value of X.

A random sample of five metal rods produced by a machine is taken. Each rod is tested for hardness. The results, in suitable units, are as follows.

524 526 520 523 530

Some adjustments are made to the machine. Assume that a normal distribution is still appropriate and that the population variance remains unchanged. A second random sample, this time of ten metal rods, is now taken. The results for hardness are as follows.

Assuming a normal distribution, calculate a 95% confidence interval for the population mean.

525 520 522 524 518 520 519 525 527 516

ii Stating suitable hypotheses, test at the 10% significance level whether there is any difference between the population means before and after the adjustments.

Cambridge International AS & A Level Further Mathematics 9231 Paper 22 Q9 November 2011

A biased die has probability $p$ of showing a 6. The random variable $X$ counts the number of trials up to and including the trial in which the first 6 is obtained. The random variable $Y$ counts the number of trials up to and including the trial in which the $n$th 6 is obtained.

a Write down an expression for  $ P(X=x) $ for X=1,2, .... Show that the probability generating function of X is:

 $$ G_{X}(t)=p t(1-q t)^{-1} $$ 

where $q=1-p$. Hence show that the mean and variance of $X$ are, respectively:

 $$ \begin{aligned}&E(X)=\frac{1}{p}\\&Var(X)=\frac{q}{p^{2}}\end{aligned} $$

<!-- page 318 -->

b Given that the trials for X are independent and that  $ Y = X_{1} + X_{2} + \cdots + X_{n} $, find:

i the probability generating function for Y

ii E(Y) and Var(Y).

6 The owner of three driving schools, A, B and C, wished to assess whether there was an association between passing the driving test and the school attended. He selected a random sample of learner drivers from each of his schools and recorded the numbers of passes and failures at each school. The results that he obtained are shown in the table below.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2"></td><td colspan="3">Driving school attended</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>B</td><td style='text-align: center; word-wrap: break-word;'>C</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Passes</td><td style='text-align: center; word-wrap: break-word;'>23</td><td style='text-align: center; word-wrap: break-word;'>15</td><td style='text-align: center; word-wrap: break-word;'>17</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Failures</td><td style='text-align: center; word-wrap: break-word;'>27</td><td style='text-align: center; word-wrap: break-word;'>25</td><td style='text-align: center; word-wrap: break-word;'>43</td></tr></table>

Using a  $ \chi^{2} $-test and a 5% level of significance, test whether there is an association between passing or failing the driving test and the driving school attended.

Cambridge International AS & A Level Further Mathematics 9231 Paper 2 Q8 November 2010

Trees of the same species grow on opposite sides of a river valley. The heights of eight randomly selected trees from each side of the river valley are measured and the results, in metres, are given in the table.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>East side (m)</td><td style='text-align: center; word-wrap: break-word;'>13.6</td><td style='text-align: center; word-wrap: break-word;'>20.1</td><td style='text-align: center; word-wrap: break-word;'>7.8</td><td style='text-align: center; word-wrap: break-word;'>18.2</td><td style='text-align: center; word-wrap: break-word;'>8.5</td><td style='text-align: center; word-wrap: break-word;'>7.7</td><td style='text-align: center; word-wrap: break-word;'>16.0</td><td style='text-align: center; word-wrap: break-word;'>13.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>West side (m)</td><td style='text-align: center; word-wrap: break-word;'>5.9</td><td style='text-align: center; word-wrap: break-word;'>7.5</td><td style='text-align: center; word-wrap: break-word;'>9.6</td><td style='text-align: center; word-wrap: break-word;'>11.0</td><td style='text-align: center; word-wrap: break-word;'>4.1</td><td style='text-align: center; word-wrap: break-word;'>7.1</td><td style='text-align: center; word-wrap: break-word;'>10.1</td><td style='text-align: center; word-wrap: break-word;'>12.2</td></tr></table>

Carry out a Wilcoxon rank-sum test, at the 5% level of significance, to investigate whether there is any difference in the average heights of the trees from the two sides of the river valley.

Interpret your conclusion in context.

8 The continuous random variable X has probability density function f, given by:

 $$ \mathrm{f}(x)=\left\{\begin{aligned}&\frac{1}{15}((x-3)^{2}+2)&0\leqslant x\leqslant3\\ &0&otherwise\end{aligned}\right. $$ 

The random variable Y is defined by  $ Y = X^{2} $.

a Show that the cumulative distribution function  $ G(y) $ is given by:

 $$ \mathrm{G}(y)=\begin{cases}0&y<0\\\frac{1}{45}\binom{y^{\frac{3}{2}}-9y+33y^{\frac{1}{2}}}{}&\end{cases}0\leqslant y\leqslant9\\1&y>9\end{cases} $$ 

b Show that the median is 0.75, correct to 2 decimal places.

c Find E(Y).

<!-- page 319 -->

9 A charity launched a campaign to raise awareness of low pay amongst full-time workers in company canteens. The charity now believes the median weekly wage in this job sector has increased.

After the campaign, a random sample of ten canteen workers was asked how much they earned in the previous week. The results, in NZ$, were as follows.

156.45 145.50 151.30 150.70 156.10 151.15 144.40 146.60 163.75 157.60

Before the campaign the median weekly wage for full-time workers in the company canteens was NZ$147.50.

Carry out a Wilcoxon signed-rank test to determine whether there has been an increase in the median wage after the campaign. Use the 5% level of significance.

10 It has been found that 60% of the computer chips produced in a factory are faulty. As part of quality control, 100 samples of 4 chips are selected at random, and each chip is tested. The number of faulty chips in each sample is recorded, with the results given in the following table.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Number of faulty chips</td><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Number of samples</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>12</td><td style='text-align: center; word-wrap: break-word;'>27</td><td style='text-align: center; word-wrap: break-word;'>49</td><td style='text-align: center; word-wrap: break-word;'>10</td></tr></table>

The expected values for a binomial distribution with parameters $n=4$ and $p=0.6$ are given in the following table.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Number of faulty chips</td><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Number of samples</td><td style='text-align: center; word-wrap: break-word;'>2.56</td><td style='text-align: center; word-wrap: break-word;'>15.36</td><td style='text-align: center; word-wrap: break-word;'>34.56</td><td style='text-align: center; word-wrap: break-word;'>34.56</td><td style='text-align: center; word-wrap: break-word;'>12.96</td></tr></table>

i Show how the expected value 34.56 corresponding to 2 faulty chips is obtained.

ii Carry out a goodness of fit test at the 5% significance level, and state what can be deduced from the outcome of the test.

Cambridge International AS & A Level Further Mathematics 9231 Paper 2 Q9 November 2009

11 The Tax Bureau claims that people typically take 140 minutes to fill in a tax form. A researcher believes that this claim is incorrect and that, generally, it takes people longer to complete the form. She recorded the time (in minutes) it took ten people to complete the form. The results are given below.

151 138 132 149 145 152 141 148 162 146

Carry out a sign test, at the 5% significance level, to investigate whether the average time to complete the form is greater than 140 minutes.

