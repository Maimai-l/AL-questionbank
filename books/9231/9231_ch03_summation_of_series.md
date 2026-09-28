# Summation of series

<!-- Cambridge International AS  A Level Further Mathematics Coursebook (Lee Mckelvey Martin Crozier) .pdf p57-69 -->

<!-- page 57 -->

# Chapter 3 Summation of series

## In this chapter you will learn how to:

use the standard results for  $ \Sigma r $,  $ \Sigma r^{2} $ and  $ \Sigma r^{3} $ to find related sums

use the method of differences to obtain the sum of a finite series

recognise, by direct consideration of a sum to n terms, when a series is convergent, and find the sum to infinity in such cases.

<!-- page 58 -->

## PREREQUISITE KNOWLEDGE


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Where it comes from</td><td style='text-align: center; word-wrap: break-word;'>What you should be able to do</td><td style='text-align: center; word-wrap: break-word;'>Check your skills</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>AS &amp; A Level Mathematics Pure Mathematics 2 &amp; 3, Chapter 7</td><td style='text-align: center; word-wrap: break-word;'>Work with basic partial fractions, particularly those with a higher power in the denominator than in the numerator.</td><td style='text-align: center; word-wrap: break-word;'>1 Split the following into partial fractions. a  $ \frac{1}{(x+1)(x-1)} $ b  $ \frac{2}{x^{2}-3x+2} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>AS &amp; A Level Mathematics Pure Mathematics 1, Chapter 6</td><td style='text-align: center; word-wrap: break-word;'>Have a basic understanding of arithmetic sequences, as well as an appreciation for convergent series.</td><td style='text-align: center; word-wrap: break-word;'>2 Evaluate:  $ S_{\infty} - S_{10} $, where  $ S_{n} = \frac{2(1 - 0.5^{n})}{0.5} $</td></tr></table>

## What is the summation of series?

A series is the sum of terms in a mathematical sequence. Historically, mathematicians needed to use infinite series to approximate values such as $\pi$, and to develop polynomials to approximate other functions. Today, we can use series to work out the value of financial investments or to help musicians mix recorded tracks to achieve the sound they want.

You are already familiar with arithmetic and geometric series and how to sum them to a given term or to infinity in the case of geometric series. This chapter will build on some of these concepts and extend them, incorporating convergent series and squares and cubes of numbers. You will also work with partial fractions to recognise and simplify number patterns.

### 3.1 The summation formulae  $ \Sigma r $,  $ \Sigma r^{2} $,  $ \Sigma r^{3} $

<div style="text-align: center;"><img src="imgs/img_in_image_box_98_939_143_975.jpg" alt="Image" width="3%" /></div>


### KEY POINT 3.1

The expression for the sum of a series consisting of a constant $k$, added together $n$ times, is written as $\sum_{r=1}^{n} k$ and its value is $kn$.

In your AS & A Level work you will have seen a variety of sequences. We know that the sum of an arithmetic sequence is  $ S_n = \frac{n}{2}[2a + (n-1)d] $. For the case when  $ a = 1 $,  $ d = 1 $ then  $ S_n = \frac{n}{2}[2 + (n-1)] $. This result is written as  $ S_n = \frac{n(n+1)}{2} $. It is known as the sum of the first  $ n $ natural numbers as it represents  $ 1 + 2 + 3 + 4 + \ldots + n $.

In summation notation, this is written as  $ \sum_{r=1}^{n} r = \frac{n(n+1)}{2} $. Another way to derive this is to consider the expression  $ (r+1)^2 = r^2 + 2r + 1 $, then write down the expression as r goes from 1 to n.

<!-- page 59 -->

$$ r=1\Rightarrow2^{2}=1^{2}+2\times1+1 $$ 

 $$ r=2\Rightarrow3^{2}=2^{2}+2\times2+1 $$ 

 $$ r=3\Rightarrow4^{2}=3^{2}+2\times3+1 $$ 

 $$ \begin{array}{r l r}&{\bullet}&{\bullet}\\ &{\bullet}&{\bullet}\\ &{\bullet}&{\bullet}\end{array} $$ 

 $$ r=n\Rightarrow(n+1)^{2}=n^{2}+2\times n+1 $$ 

Consider the right-hand side of the equations, summed from top to bottom. Write it in summation form. This gives the expression  $ \sum_{r=1}^{n} r^2 + 2 \sum_{r=1}^{n} r + n $.

Next, add 1 to both sides to get  $ 1^{2} + 2^{2} + 3^{2} + \cdots + n^{2} + (n+1)^{2} = \sum_{r=1}^{n} r^{2} + 2 \sum_{r=1}^{n} r + n + 1 $.

The left- and right-hand sides both include  $ \sum_{r=1}^{n} r^2 $. Cancelling this term leaves

 $ (n+1)^2 = 2 \times \sum_{r=1}^{n} r + n + 1 $. This simplifies to  $ \sum_{r=1}^{n} r = \frac{n(n+1)}{2} $.

### WORKED EXAMPLE 3.1

Find  $ \sum_{r=1}^{n}(4r+1) $. Hence determine the value of  $ \sum_{17}^{48}(4r+1) $.

 $$ \begin{aligned}\sum_{1}^{n}(4r+1)&=4\sum_{1}^{n}r+\sum_{1}^{n}1\\&=4\times\frac{n(n+1)}{2}+n\\&=2n^{2}+3n\end{aligned} $$ 

Split the sum into smaller parts.

Use the sum of natural numbers.

Combine terms.

Write out as the difference of two separate sums, one with limits of 1 and 16, the other with limits of 1 and 48.

Determine the final answer.

We can use  $ \sum r $ instead of  $ \sum_{r=1}^{n} r $ provided we remember the correct limits.

 $$ \begin{aligned}\therefore\sum_{17}^{48}(4r+1)&=(2\times48^{2}+3\times48)-(2\times16^{2}+3\times16)\\&=4192\end{aligned} $$ 

Since the sum has a variable upper limit, we can write anything we want as this limit. For example, we might want to determine the value of  $ \sum_{r=1}^{2n} r $, which would be  $ \frac{(2n)(2n+1)}{2} = 2n^2 + n $.

This result can be used to deduce the result of  $ \sum_{n+1}^{2n} r $. Carefully consider what the limits mean: this is the sum of the first  $ 2n $ terms minus the sum of the first  $ n $ terms.

<!-- page 60 -->

So

 $$ 2n^{2}+n-\frac{n(n+1)}{2}=\frac{3}{2}n^{2}+\frac{1}{2}n. $$ 

### WORKED EXAMPLE 3.2

Find an expression for  $ 1 + 3 + 5 + 7 + \cdots $, for the first n terms, using two different approaches.

## Answer

## Method 1:

 $$ \begin{aligned}1+3+5+7+\cdots&=\sum_{r=1}^{n}(2r-1)\\&=2\sum_{r=1}^{n}r-n\\&=n(n+1)-n\\&\cdots=\frac{2}{n-1}n-n-1.\end{aligned} $$ 

Write the sum of $n$ odd terms.

Use the standard result.

 $$ \Rightarrow1+3+5+7+\cdots=n^{2} $$ 

Simplify.

## Method 2:

 $$ \begin{aligned}1+3+5+7+\cdots&=\sum_{r=1}^{2n}r-\sum_{r=1}^{n}(2r)&\\&=\frac{1}{2}(2n)(2n+1)-2\times\frac{1}{2}n(n+1)\\ &=n^{2}\\ \end{aligned} $$ 

Write a sum of $2n$ terms and subtract all even terms, leaving $n$ terms.

The second sum is twice the sum of the first $n$ natural numbers.

This gives the same result.

The next case to look at is the sum of  $ 1^{2} + 2^{2} + 3^{2} + 4^{2} + \cdots $. We will use the same method as shown previously.

Start with the expression  $ (r+1)^3 = r^3 + 3r^2 + 3r + 1 $, then write this for r = 1 to n.

 $$ r=1\Rightarrow2^{3}=1^{3}+3\times1^{2}+3\times1+1 $$ 

 $$ r=2\Rightarrow3^{3}=2^{3}+3\times2^{2}+3\times2+1 $$ 

 $$ r=3\Rightarrow4^{3}=3^{3}+3\times3^{2}+3\times3+1 $$ 

 $$ \begin{array}{r l r}{*}&{}&{*}\\ {*}&{}&{*}\\ {*}&{}&{*}\end{array} $$ 

 $$ r=n\Rightarrow(n+1)^{3}=n^{3}+3\times n^{2}+3\times n+1 $$ 

Sum the right side to get  $ \sum_{r=1}^{n}r^{3}+3\sum_{r=1}^{n}r^{2}+3\sum_{r=1}^{n}r+n $. Then add 1 to both sides to get

 $ 1^3 + 2^3 + 3^3 + \cdots + (n+1)^3 = \sum_{r=1}^{n} r^3 + 3 \sum_{r=1}^{n} r^2 + 3 \sum_{r=1}^{n} r + n + 1 $. After cancelling like terms,

this reduces to  $ n^{3} + 3n^{2} + 3n + 1 = 3 \sum_{r=1}^{n} r^{2} + 3 \sum_{r=1}^{n} r + n + 1 $.

Since  $ \sum_{r=1}^{n} r = \frac{n(n+1)}{2} $, we have

 $$ 3\sum_{r=1}^{n}r^{2}=n^{3}+3n^{2}+3n+1-3\frac{n(n+1)}{2}-n-1 $$

<!-- page 61 -->

$$ 3\sum_{r=1}^{n}r^{2}=n(n+1)(n+2)-3\frac{n(n+1)}{2} $$ 

 $$ 3\sum_{r=1}^{n}r^{2}=n(n+1)\left(n+\frac{1}{2}\right) $$ 

 $$ 3\sum_{r=1}^{n}r^{2}=\frac{n}{2}(n+1)(2n+1) $$ 

and it follows that  $ \sum_{r=1}^{n}r^{2}=\frac{1}{6}n(n+1)(2n+1) $.

This is the sum of the squares of the first n natural numbers.

### WORKED EXAMPLE 3.3

Find an expression in terms of n for  $ \sum_{r=1}^{n}(3r^{2}-4r+2) $.

Answer

 $$ \begin{aligned}\sum_{r=1}^{n}(3r^{2}-4r+2)&=3\sum_{r=1}^{n}r^{2}-4\sum_{r=1}^{n}r+\sum_{r=1}^{n}2&\text{Split into individual sums.}\\ &=3\times\frac{1}{6}n(n+1)(2n+1)-4\times\frac{1}{2}n(n+1)+2n\\ &=\frac{n}{2}(2n^{2}+3n+1)-2n^{2}-2n+2n\\ &=n^{3}+\frac{3}{2}n^{2}+\frac{1}{2}n-2n^{2}\\ &=n^{3}-\frac{1}{2}n^{2}+\frac{1}{2}n\\ &\end{aligned}\text{Use the result for each sum.} $$ 

Using an approach similar to the one in Worked example 3.2, we are going to find an expression for  $ 1^{2} + 4^{2} + 7^{2} + \cdots $, for the first n terms.

There are, again, two ways to achieve this. First, write  $ \sum_{r=1}^{n}(3r-2)^{2} $ and then expand it to

get  $ 9\sum_{r=1}^{n}r^{2}-12\sum_{r=1}^{n}r+\sum_{r=1}^{n}4 $.

This gives  $ 9 \times \frac{1}{6}n(n+1)(2n+1) - 12 \times \frac{1}{2}n(n+1) + 4n $

 $ = \frac{3n}{2}(2n^2 + 3n + 1) - 6n^2 - 6n + 4n $

 $ = 3n^3 + \frac{9}{2}n^2 + \frac{3}{2}n - 6n^2 - 2n $ which simplifies to  $ \frac{1}{2}n(6n^2 - 3n - 1) $.

The alternative method is to assume we have 3n terms and write the expression as

 $ 1^2 + 4^2 + 7^2 + \cdots = \sum_{r=1}^{3n} r^2 - \sum_{r=1}^{n} (3r - 1)^2 - \sum_{r=1}^{n} (3r)^2 $. The second sum removes  $ 2^2, 5^2, 8^2, \ldots $

from the total and the third sum removes  $ 3^{2}, 6^{2}, 9^{2}, \ldots $

Working through the algebra will lead to the same result as before. The first method is simpler, but there are cases when an alternative approach is needed.

<!-- page 62 -->

<div style="text-align: center;"><img src="imgs/img_in_image_box_93_147_137_186.jpg" alt="Image" width="3%" /></div>


## DID YOU KNOW?

Carl Friedrich Gauss added $1+2+3+\cdots+100$ in a matter of seconds. He did this by considering the pairs $(1+100)+(2+99)+\cdots+(50+51)=5050$.

This became formally known as  $ \sum_{r=1}^{n} r = \frac{n(n+1)}{2} $.

### EXPLORE 3.1

Working in groups, try to work out the sum of  $ 1^{2}-2^{2}+3^{2}-4^{2}+\cdots $.

Can you write this as one summation, or do you need a series of summations?

We will now consider the sum of the cubes of natural numbers. This is the sum  $ 1^3 + 2^3 + 3^3 + \cdots $.

As with the previous two examples, start with  $ (r+1)^{4}=r^{4}+4r^{3}+6r^{2}+4r+1 $, then list the terms as before, from r=1 to r=n.

 $$ r=1\Rightarrow2^{4}=1^{4}+4\times1^{3}+6\times1^{2}+4\times1+1 $$ 

 $$ r=2\Rightarrow3^{4}=2^{4}+4\times2^{3}+6\times2^{2}+4\times2+1 $$ 

 $$ r=3\Rightarrow4^{4}=3^{4}+4\times3^{3}+6\times3^{2}+4\times3+1 $$ 

\[\begin{array}{c} \bullet \quad \bullet \quad

 $$ r=n\Rightarrow(n+1)^{4}=n^{4}+4\times n^{3}+6\times n^{2}+4\times n+1 $$ 

Following the same procedure as in Worked examples 3.2 and 3.3, we find  $ \sum_{r=1}^{n} r^{3} = \frac{1}{4} n^{2}(n+1)^{2} $.

This is the sum of the cubes of the first $n$ natural numbers.

### WORKED EXAMPLE 3.4

Find an expression in terms of n for  $ \sum_{r=1}^{n} r^2 (r-1) $.

Answer

 $$ \begin{aligned}\sum_{r=1}^{n}r^{2}(r-1)&=\sum_{r=1}^{n}r^{3}-\sum_{r=1}^{n}r^{2}\\&=\frac{1}{4}n^{2}(n+1)^{2}-\frac{1}{6}n(n+1)(2n+1)\\&=n(n+1)\left(\frac{n^{2}}{4}+\frac{n}{4}-\frac{n}{3}-\frac{1}{6}\right)\\&=\frac{1}{12}n(n+1)(3n^{2}-n-2)\\&=\frac{1}{12}n(n+1)(n-1)(3n+2)\end{aligned} $$ 

Write as two separate sums.

Replace with the appropriate formulae.

Note we do not need to expand all the brackets to simplify.

Simplify.

<!-- page 63 -->

<div style="text-align: center;"><img src="imgs/img_in_image_box_18_145_49_176.jpg" alt="Image" width="2%" /></div>


As a class, or in groups, can you derive an expression for  $ \sum_{r=1}^{n} r^{4} $? This is beyond the syllabus but will reinforce your understanding of summations.

<div style="text-align: center;"><img src="imgs/img_in_image_box_865_150_908_187.jpg" alt="Image" width="3%" /></div>


## FAST FORWARD

You will meet these formulae again in Chapter 7, when you will prove them in a more rigorous way.

## EXERCISE 3A

P 1 Show that  $ \sum_{r=1}^{n}(3r-5)=\frac{n}{2}(3n-7) $.

P 2 Prove that  $ \sum_{r=1}^{n}2r(r-3)=\frac{2}{3}n(n+1)(n-4). $

PS 3 Determine the value of $1-2+3-4+\ldots+(2n-1)-(2n)$.

4 Without using a calculator, show that  $ \sum_{r=1}^{n}(r+2)(r+3)=\frac{n(n^{2}-19)}{3} $.

PS 5 Without using a calculator, find a simplified expression for  $ 1^{2} + 2^{2} - 3^{2} + 4^{2} + 5^{2} - 6^{2} + \cdots + (3n - 2)^{2} + (3n - 1)^{2} - (3n)^{2} $.

PS 6 Find, in terms of $n$, an expression for $\sum_{r=n+1}^{2n} r(r+1)$.

M 7 Find the sum of the terms  $ 1^{2} + 2^{2} + 3^{2} + 5^{2} + 6^{2} + 7^{2} + \cdots + 97^{2} + 98^{2} + 99^{2} $

P PS 8 Show that  $ \sum_{r=1}^{n}(2r+1)(3r+2)=\frac{n(4n^{2}+13n+13)}{2} $. Hence, find the result of  $ \sum_{r=11}^{25}(2r+1)(3r+2) $.

M PS 9 Find the sum of the cubes of the first 100 even terms.

### 3.2 Converging series

For the series in this section, we will reach a finite sum as the number of terms tends to infinity. This will be achieved by setting up the series in an appropriate form to help us spot a recognisable pattern.

Consider the summation  $ \sum_{r=1}^{n}\frac{1}{r(r+1)} $. How could we represent this in terms of  $ n $?

If we write down a few terms,  $ \frac{1}{2}+\frac{1}{6}+\frac{1}{12}+\frac{1}{20}+\cdots $, it appears that there is no recognisable pattern.

So, go back to the original form of the summation, and this time split the fraction into partial fractions.

Now we have  $ \frac{1}{r(r+1)}=\frac{A}{r}+\frac{B}{r+1} $, which gives  $ 1=A(r+1)+Br $. From r=-1, B=-1 and from r=0, A=1.

<!-- page 64 -->

We are now working with  $ \sum_{r=1}^{n}\left(\frac{1}{r}-\frac{1}{r+1}\right) $. Write down a few terms, from the start and the end of the series,

 $$ \sum_{r=1}^{n}\left(\frac{1}{r}-\frac{1}{r+1}\right)=\left(\frac{1}{1}-\frac{1}{2}\right)+\left(\frac{1}{2}-\frac{1}{3}\right)+\left(\frac{1}{3}-\frac{1}{4}\right)+\cdots+\left(\frac{1}{n-1}-\frac{1}{n}\right)+\left(\frac{1}{n}-\frac{1}{n+1}\right) $$ 

Lots of the terms cancel, and we are left with  $ \sum_{r=1}^{n}\left(\frac{1}{r}-\frac{1}{r+1}\right)=1-\frac{1}{n+1} $.

The cancelling of terms in this way to simplify the summation is known as the method of differences.

<div style="text-align: center;"><img src="imgs/img_in_image_box_929_175_971_213.jpg" alt="Image" width="3%" /></div>


## TIP

It is always a good idea to write down some terms. To determine which terms cancel you need to see some of the pattern. Ensure you write down terms at the start and at the end of the series.

### WORKED EXAMPLE 3.5

Find, in terms of $n$, the sum of $\sum_{r=1}^{n}\frac{1}{(r+1)(r+2)}.$

## Answer

 $$ \begin{aligned}\frac{1}{(r+1)(r+2)}&=\frac{A}{r+1}+\frac{B}{r+2}\\1&=A(r+2)+B(r+1)\end{aligned} $$ 

Split into partial fractions.

using r = -1, A = 1 and using r = -2, B = -1

Find the coefficients.

 $$ \begin{aligned}\sum_{r=1}^{n}\left(\frac{1}{r+1}-\frac{1}{r+2}\right)&=\left(\frac{1}{2}-\frac{1}{3}\right)+\left(\frac{1}{3}-\frac{1}{4}\right)+\left(\frac{1}{4}-\frac{1}{5}\right)+\cdots\\&\quad+\left(\frac{1}{n}-\frac{1}{n+1}\right)+\left(\frac{1}{n+1}-\frac{1}{n+2}\right)\\&=\left(\frac{1}{2}-\frac{1}{3}\right)+\left(\frac{1}{3}-\frac{1}{4}\right)+\left(\frac{1}{4}-\frac{1}{5}\right)+\cdots\\&\quad+\left(\frac{1}{n}-\frac{1}{n+1}\right)+\left(\frac{1}{n+1}-\frac{1}{n+2}\right)\end{aligned} $$ 

Write down enough terms to see the cancellations.

 $$ \therefore\sum_{r=1}^{n}\frac{1}{(r+1)(r+2)}=\frac{1}{2}-\frac{1}{n+2} $$ 

Cancel terms to get the final answer.

For the two previous examples, the difference between the factors of the denominator was 1 in both cases. Recall we had  $ r(r+1) $ and then  $ (r+1)(r+2) $.

If we now consider the summation  $ \sum_{r=1}^{n}\frac{1}{r(r+2)} $, the procedure will be the same as before.

Split it into partial fractions first to give  $ \frac{1}{2}\sum_{r=1}^{n}\left(\frac{1}{r}-\frac{1}{r+2}\right) $, then write down some terms, initially ignoring the  $ \frac{1}{2} $ in front of the summation:

 $$ \begin{aligned}&\left(\frac{1}{1}-\frac{1}{3}\right)+\left(\frac{1}{2}-\frac{1}{4}\right)+\left(\frac{1}{3}-\frac{1}{5}\right)+\left(\frac{1}{4}-\frac{1}{6}\right)+\cdots+\left(\frac{1}{n-2}-\frac{1}{n}\right)+\left(\frac{1}{n-1}-\frac{1}{n+1}\right)\\ &+\left(\frac{1}{n}-\frac{1}{n+2}\right)\\ \end{aligned} $$

<!-- page 65 -->

Cancel like terms to get  $ 1 + \frac{1}{2} - \frac{1}{n+1} - \frac{1}{n+2} $. If we then multiply by the  $ \frac{1}{2} $ we ignored previously, the summation can be written as  $ \sum_{r=1}^{n} \frac{1}{r(r+2)} = \frac{3}{4} - \frac{1}{2(n+1)} - \frac{1}{2(n+2)} $.

In this example, notice that two terms from the start and finish are included in the final answer. Previously it was only one term from each end.

### EXPLORE 3.3

Consider the summation  $ \sum_{r=1}^{n}\frac{1}{(ar+b)(ar+c)} $. In groups, investigate the effect of changing these values. For example, what happens when a=2?

### WORKED EXAMPLE 3.6

For the summation  $ \sum_{r=2}^{n}\frac{1}{(r-1)(r+1)} $, find an expression in terms of n.

## Answer

 $$ \frac{1}{(r-1)(r+1)}=\frac{A}{r-1}+\frac{B}{r+1} $$ 

 $$ 1=A(r+1)+B(r-1) $$ 

 $$ A=\frac{1}{2},B=-\frac{1}{2} $$ 

Split into partial fractions.

 $$ \begin{aligned}\sum_{r=2}^{n}\frac{1}{(r-1)(r+1)}&=\left(\frac{1}{1}-\frac{1}{3}\right)+\left(\frac{1}{2}-\frac{1}{4}\right)+\left(\frac{1}{3}-\frac{1}{5}\right)+\cdots\\&\quad+\left(\frac{1}{n-3}-\frac{1}{n-1}\right)+\left(\frac{1}{n-2}-\frac{1}{n}\right)\\&\quad+\left(\frac{1}{n-1}-\frac{1}{n+1}\right)\end{aligned} $$ 

Determine the coefficients.

Initially ignore the $\frac{1}{2}$ in front of every term, and note that this sum starts at $r=2$.

 $$ =1+\frac{1}{2}-\frac{1}{n}-\frac{1}{n+1} $$ 

 $$ \sum_{r=2}^{n}\frac{1}{(r-1)(r+1)}=\frac{3}{4}-\frac{1}{2n}-\frac{1}{2(n+1)} $$ 

## Cancel terms

Simplify and remember the factor of  $ \frac{1}{2} $ we previously ignored.

<!-- page 66 -->

Finally, let us consider these summations as the upper limit tends to infinity. Since the powers of $r$ are always dominant in the denominator, these summations will always tend to a limit.

Look back at the example of  $ \sum_{r=1}^{n}\frac{1}{r(r+1)}=1-\frac{1}{n+1} $. As  $ n\to\infty $ this will tend to 1.

<div style="text-align: center;"><img src="imgs/img_in_image_box_929_140_972_180.jpg" alt="Image" width="3%" /></div>


## TIP

Pay close attention to the limit of your sum. This may not be 1.

### WORKED EXAMPLE 3.7


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td colspan="2">Given that  $ S_n = \sum_{r=2}^{n} \frac{5}{r(r-1)} $, find the sum of the terms as  $ n \to \infty $.</td></tr><tr><td colspan="2">Answer</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ \frac{5}{r(r-1)} = \frac{A}{r} + \frac{B}{r-1} $\n $ 5 = A(r-1) + Br $\n $ A = -5, B = 5 $\n $ \left( \frac{1}{1} - \frac{1}{2} \right) + \left( \frac{1}{2} - \frac{1}{3} \right) + \cdots + \left( \frac{1}{n-2} - \frac{1}{n-1} \right) + \left( \frac{1}{n-1} - \frac{1}{n} \right) $\n $ \therefore S_n = \sum_{r=2}^{n} \frac{5}{r(r-1)} = 5 - \frac{5}{n} $\n $ n \to \infty, S_n \to 5 $</td><td style='text-align: center; word-wrap: break-word;'>Split into partial fractions.\n\nDetermine the coefficients.\nInitially ignoring the 5 in front of every term, write down enough terms to spot a pattern.\nState  $ S_n $, remembering to include the 5 we previously ignored.\nWrite down the limit.</td></tr></table>

## EXERCISE 3B

PS 1 Find, in terms of $n$, an expression for $\sum_{r=2}^{n}\frac{3}{(r-1)r}$.

P 2 Show that  $ \sum_{r=1}^{n}\frac{1}{(r+4)(r+5)} $ can be written as  $ \frac{n}{5n+25} $.

3 Determine the value of  $ \sum_{r=1}^{\infty}\frac{1}{(2r+3)(2r+5)} $

4 Without using a calculator, find, in terms of $n$, an expression for $\sum_{r=1}^{n}\frac{1}{(r+3)(r+4)}.$

Without using a calculator, given that $S_{n}=\sum_{r=0}^{n}\frac{1}{(2r+1)(2r+3)}$, show that $S_{n}=\frac{n+1}{2n+3}$.

## PPS

Without using a calculator, show that  $ \sum_{r=3}^{n}\frac{1}{r(r-2)}=\frac{3}{4}-\frac{1}{2n-2}-\frac{1}{2n} $. Hence, determine, in terms of n, the result of  $ \sum_{r=n+1}^{2n}\frac{1}{r(r-2)} $.

<!-- page 67 -->

PS 7 Without using a calculator, determine the value of  $ \sum_{r=2}^{\infty}\frac{4}{r^{2}-1} $.

PS 8 Let  $ S_{n} = \sum_{r=4}^{n} \frac{1}{r^{2} - 5r + 6} $.

a Find, in terms of $n$, an expression for $S_{n}$.

b Given that $S=\lim_{n\to\infty}S_n$, write down the value of $S$.

c Find the range of values of n such that $S - S_{n} < 0.001$.

## WORKED PAST PAPER QUESTION

Verify that, for all positive values of $n$,

 $$ \frac{1}{(n+2)(2n+3)}-\frac{1}{(n+3)(2n+5)}=\frac{4n+9}{(n+2)(n+3)(2n+3)(2n+5)}. $$ 

For the series  $ \sum_{n=1}^{N}\frac{4n+9}{(n+2)(n+3)(2n+3)(2n+5)} $, find

i the sum to N terms,

ii the sum to infinity.

Cambridge International AS & A Level Further Mathematics 9231 Paper 1 Q2 June 2009

## Answer

 $$ \begin{aligned}\frac{1}{(n+2)(2n+3)}-\frac{1}{(n+3)(2n+5)}&=\frac{2n^{2}+11n+15-(2n^{2}+7n+6)}{(n+2)(n+3)(2n+3)(2n+5)}\\&=\frac{4n+9}{(n+2)(n+3)(2n+3)(2n+5)}\end{aligned} $$ 

 $$ \begin{aligned}\mathrm{i}\quad\sum_{n=1}^{N}\frac{4n+9}{(n+2)(n+3)(2n+3)(2n+5)}&=\frac{1}{3\times5}-\frac{1}{4\times7}+\frac{1}{4\times7}-\frac{1}{5\times9}+\cdots+\frac{1}{(N+2)(2N+3)}-\frac{1}{(N+3)(2N+5)}\\&=\frac{1}{15}-\frac{1}{(N+3)(2N+5)}\end{aligned} $$ 

ii As $N \to \infty$, sum becomes $\frac{1}{15}$.

<!-- page 68 -->

## Checklist of learning and understanding

## Standard summations:

$$\sum_{r=1}^{n} r = \frac{1}{2} n (n+1)$$

$$\sum_{r=1}^{n}r^{2}=\frac{1}{6}n(n+1)(2n+1)$$

$$\sum_{r=1}^{n}r^{3}=\frac{1}{4}n^{2}(n+1)^{2}$$

When we consider summations such as  $ \sum_{r=n+b}^{2n} f(r) $, it is often best to first determine  $ \sum_{r=1}^{n} f(r) $, then replace n with 2n to determine  $ \sum_{r=1}^{2n} f(r) $. Finally, write  $ \sum_{r=n+b}^{2n} f(r) = \sum_{r=1}^{2n} f(r) - \sum_{r=1}^{n+b-1} f(r) $.

When we use the method of differences, first split  $ \sum_{r=1}^{n}\frac{a}{(r+b)(r+c)} $ into partial fractions such as  $ \sum_{r=1}^{n}\left(\frac{A}{r+b}+\frac{B}{r+c}\right) $. Next, list as many terms as needed to effectively cancel terms and get a reduced form.

For convergence, first get the summation in the form  $ \sum_{r=a}^{n} f(n) = b + \frac{c}{dn + e} + \cdots $. Allowing  $ n \to \infty $ will lead to the result of b.

<!-- page 69 -->

## Do not use a calculator in this exercise

1 Find the sum of the first n terms of the series  $ \frac{1}{1 \times 3} + \frac{1}{2 \times 4} + \frac{1}{3 \times 5} + \cdots $ and deduce the sum to infinity.

Cambridge International AS & A Level Further Mathematics 9231 Paper 13 Q1 June 2012

2 Find  $ 2^{2} + 4^{2} + \cdots + (2n)^{2} $.

Hence find  $ 1^{2}-2^{2}+3^{2}-4^{2}+\cdots-(2n)^{2} $, simplifying your answer.

Cambridge International AS & A Level Further Mathematics 9231 Paper 13 Q1 June 2011

3 Use the method of differences to show that  $ \sum_{r=1}^{N}\frac{1}{(2r+1)(2r+3)}=\frac{1}{6}-\frac{1}{2(2N+3)} $.

Deduce that  $ \sum_{r=N+1}^{2N}\frac{1}{(2r+1)(2r+3)}<\frac{1}{8N} $.

Cambridge International AS & A Level Further Mathematics 9231 Paper 11 Q5 June 2013

