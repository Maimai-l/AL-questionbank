# Proof by induction

<!-- Cambridge International AS  A Level Further Mathematics Coursebook (Lee Mckelvey Martin Crozier) .pdf p151-165 -->

<!-- page 151 -->

<div style="text-align: center;"><img src="imgs/img_in_image_box_2_10_1187_759.jpg" alt="Image" width="96%" /></div>


## Chapter 7 Proof by induction

In this chapter you will learn how to:

use the method of mathematical induction to establish a given result

recognise situations where conjecture based on a limited trial followed by inductive proof is a useful strategy, and carry this out in simple cases.

<div style="text-align: center;"><img src="imgs/img_in_image_box_372_1132_1181_1293.jpg" alt="Image" width="66%" /></div>

<!-- page 152 -->

## PREREQUISITE KNOWLEDGE


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Where it comes from</td><td style='text-align: center; word-wrap: break-word;'>What you should be able to do</td><td style='text-align: center; word-wrap: break-word;'>Check your skills</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>AS &amp; A Level Mathematics Pure Mathematics 2 &amp; 3, Chapter 5</td><td style='text-align: center; word-wrap: break-word;'>Differentiate functions such as polynomials, exponentials and trigonometric functions, to 2nd derivative form.</td><td style='text-align: center; word-wrap: break-word;'>1 Find the derivative stated for each function.\na  $ y = xe^{x} $,  $ \frac{d^{4}y}{dx^{4}} $\nb  $ y = \sin^{2}2x $,  $ \frac{d^{6}y}{dx^{6}} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Probability &amp; Statistics 1, Chapter 2 Pure Mathematics 1, Chapter 6</td><td style='text-align: center; word-wrap: break-word;'>Work with recurrence relations and general series summation formulae.</td><td style='text-align: center; word-wrap: break-word;'>2 Simplify  $ \sum_{r=1}^{n}(2r+3) + 2n + 5 $.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Chapter 4</td><td style='text-align: center; word-wrap: break-word;'>Multiply matrices together.</td><td style='text-align: center; word-wrap: break-word;'>3 Given that  $ A = \begin{pmatrix} 1 &amp; 2 \\ -1 &amp; 4 \end{pmatrix} $ and  $ B = \begin{pmatrix} -3 &amp; 0 \\ 2 &amp; 5 \end{pmatrix} $, evaluate:\na AB\nb  $ A^{3} $</td></tr></table>

## What is proof?

If we consider the sequence 1, 2, 4, 8, 16, ... we can see that the terms increase by a factor of 2. It also appears that every term in this sequence will continue to be of the form  $ 2^n $ for  $ n \geq 0 $. Let us look at a way of proving that this is always true.

We can define the sequence by $u_{n+1}=2u_{n}$, where $u_{0}=1$. We can also see that $u_{n}=2^{n}$ for $n\geqslant0$. But for true mathematical proof, we need to be certain that a relationship is true (or false) for all values being considered, without exception.

In this chapter, we will look at one kind of mathematical proof, proof by induction. We will learn how to set up a mathematical inductive process, using the first term and a general term given. We need to form a convincing argument to prove a statement is true for all values in the interval.

### 7.1 The inductive process

The condition for proof by induction is shown in Key point 7.1.

<div style="text-align: center;"><img src="imgs/img_in_image_box_98_1195_140_1229.jpg" alt="Image" width="3%" /></div>


### KEY POINT 7.1

If a statement is defined for $u_{n} \geq a$, then your proof must reflect this exact interval in the final conclusion.

Using the example mentioned in the introduction, we shall prove by mathematical induction that  $ u_n = 2^n $ for  $ n \geq 0 $ (recall  $ u_{n+1} = 2u_n $).

Start with the case $n=0$: $u_{0}=2^{0}=1$. Since we know this is the first term in the sequence, we can say that the $n=0$ case is true. (Later we will denote this $P_{0}$.)

A general way to say the next part is:

Let  $ P_k $ be the statement that, for some integer  $ k $,  $ u_k = 2^k $.

<!-- page 153 -->

This is what we are trying to prove, so we make the assumption that it is true. We should be very clear with this statement.

Next, place this assumed result into our recurrence relation, so  $ u_{k+1} = 2 \times u_k = 2 \times 2^k = 2^{k+1} $. Hence, we have shown that  $ P_k \Rightarrow P_{k+1} $. That is to say, a general term implies the next term must also be true.

To complete the inductive process, we must now conclude what we have found.

Hence, by mathematical induction, since  $ P_0 $ is true and  $ P_k \Rightarrow P_{k+1} $,  $ P_n $ is true for all  $ n \geq 0 $.

### WORKED EXAMPLE 7.1


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td colspan="2">Prove, by mathematical induction, that  $ \sum_{r=1}^{n} r = \frac{1}{2} n (n+1) $.</td></tr><tr><td colspan="2">Answer</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Let  $ P_k $ be the statement that, for some value n = k:</td><td style='text-align: center; word-wrap: break-word;'>Write your opening inductive statement.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ \sum_{r=1}^{k} r = \frac{1}{2} k (k+1) $</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>For  $ P_1 $, n = 1: So  $ \sum_{r=1}^{1} r = \frac{1}{2} \times 1 \times 2 = 1 $, and the sum of only the first term is 1. Hence,  $ P_1 $ is true.</td><td style='text-align: center; word-wrap: break-word;'>Show the first case works, that is the left side and the right side of the equation are equal when n = 1.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Next, consider  $ \sum_{r=1}^{k+1} r = \frac{1}{2} k (k+1) + k + 1 = \frac{1}{2} k^2 + \frac{3}{2} k + 1 = \frac{1}{2} (k^2 + 3k + 2) = \frac{1}{2} (k + 1) (k + 2) = \frac{1}{2} (k + 1) ((k + 1) + 1) $</td><td style='text-align: center; word-wrap: break-word;'>Set up the k + 1 case.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Hence,  $ P_k \Rightarrow P_{k+1} $.</td><td style='text-align: center; word-wrap: break-word;'>This is in the same form as the original statement for  $ P_k $, with k replaced by k + 1.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Hence, since  $ P_1 $ is true and  $ P_k \Rightarrow P_{k+1} $, by mathematical induction,  $ P_n $ is true for all n ≥ 1.</td><td style='text-align: center; word-wrap: break-word;'>Show it leads to what you would expect to be true.</td></tr></table>

Your task is to set up the process to verify the validity of the statement. Remember to note that each statement is actually true.

As well as the standard summation formulae, we can also use this method for any summation.

For example, let us assume we are asked to prove by induction that

 $$ \sum_{r=1}^{n}r(r+1)=\frac{1}{3}n(n+1)(n+2). $$ 

We make our statement for $P_{k}$, which is $\sum_{r=1}^{k} r(r+1) = \frac{1}{3} k (k+1) (k+2)$.

<!-- page 154 -->

Start with n=1 to get the usual initial case:

 $$ \begin{aligned}left side is1(2)=2and right side is\frac{1}{3}\times1\times2\times3=2\end{aligned} $$ 

Hence $P_{1}$ is true.

Then add the next term to the sum. This means adding  $ r(r+1) $ with  $ r=k+1 $ to the sum, that is adding  $ (k+1)(k+2) $. The right side is  $ \frac{1}{3}k(k+1)(k+2)+(k+1)(k+2)=(k+1)(k+2)\left(\frac{k}{3}+1\right) $.

This simplifies to  $ \frac{1}{3}(k+1)(k+2)(k+3) $, which is the sum shown with k replaced by  $ k+1 $. This shows that  $ P_k \Rightarrow P_{k+1} $.

Finally, conclude and ensure that we mention the valid values for $n$. Hence, since $P_1$ is true and $P_k \Rightarrow P_{k+1}$, by mathematical induction, $P_n$ is true for all $n \geq 1$.

### WORKED EXAMPLE 7.2


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Use mathematical induction to prove  $ \sum_{r=1}^{n}(r^{2}-r)=\frac{n(n^{2}-1)}{3} $ for all  $ n \ge 1 $.</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td rowspan="5">Answer\nLet  $ P_{k} $ be the statement that, for some  $ n=k $:\n $ \sum_{r=1}^{k}(r^{2}-r)=\frac{k(k^{2}-1)}{3} $\n $ P_{1} $: When  $ n=1 $,  $ \sum_{r=1}^{1}(r^{2}-r)=0 $ and  $ \frac{1(1-1)}{3}=0 $.\nTherefore,  $ P_{1} $ is true.\nNext consider  $ \frac{k(k^{2}-1)}{3}+(k+1)^{2}-(k+1)= $  $ \frac{(k+1)}{3}[k(k-1)+3(k+1)-3]= $  $ \frac{(k+1)}{3}[k^{2}+2k+3-3]= $  $ \frac{1}{3}(k+1)[(k+1)^{2}-1] $, and so  $ P_{k} \Rightarrow P_{k+1} $.\nHence, since  $ P_{1} $ is true and  $ P_{k} \Rightarrow P_{k+1} $, by mathematical induction,  $ P_{n} $ is true for all  $ n \ge 1 $.</td><td style='text-align: center; word-wrap: break-word;'>Write your opening inductive statement.\nShow that the first case works.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Set up the  $ k+1 $ case.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Be aware we are aiming to reach the right side of the  $ P_{k} $ statement with  $ k $ replaced by  $ k+1 $. It is best to keep factors where possible.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Show it leads to what you would expect to be true.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Conclude the inductive process.</td></tr></table>

As well as working with summation of series, we also need to be able to work with derivatives of functions.

Starting with a very simple example, we are going to prove by mathematical induction that if  $ y = e^{2x} $, then  $ \frac{d^n y}{dx^n} = 2^n e^{2x} $.

Let $P_{k}$ be the statement that, for some value $n=k$, $\frac{\mathrm{d}^{k}y}{\mathrm{d}x^{k}}=2^{k}\mathrm{e}^{2x}$.

To confirm the initial case, we need to differentiate at least once, so n = 1.

<!-- page 155 -->

Thus,  $ \frac{dy}{dx} = 2e^{2x} $, confirming from the result  $ \frac{d^1y}{dx^1} = 2^1 \times e^{2x} $. So  $ P_1 $ is true.

Next $\frac{\mathrm{d}}{\mathrm{d}x}(2^{k}\mathrm{e}^{2x})=2^{k}\times2\times\mathrm{e}^{2x}=2^{k+1}\mathrm{e}^{2x}$. This is convincing enough to say it is the $(k+1)$th derivative. Therefore, $P_{k}\Rightarrow P_{k+1}$.

Hence, since $P_{1}$ is true and $P_{k} \Rightarrow P_{k+1}$, by mathematical induction, $P_{n}$ is true for all $n \geqslant 1$. Suppose, however, the function is $y = \sin 3x$ and we are asked to prove that $\frac{\mathrm{d}^{2n}y}{\mathrm{d}x^{2n}} = (-1)^{n}3^{2n}\sin 3x$. It is important to consider the number of times we need to differentiate. When determining the base case, we need to differentiate twice, but this counts as $n = 1$.

Also, when considering the $k$th case, we must differentiate this twice to obtain first $\frac{\mathrm{d}^{2k+1}y}{\mathrm{d}x^{2k+1}}$, then $\frac{\mathrm{d}^{2k+2}y}{\mathrm{d}x^{2k+2}}$, which can also be written as $\frac{\mathrm{d}^{2(k+1)}y}{\mathrm{d}x^{2(k+1)}}$. This will generally occur when we are dealing with a $\sin f(x)$ or $\cos f(x)$ form.

### WORKED EXAMPLE 7.3


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Prove by mathematical induction that the 2ndth derivative of y = cos(1 - 2x) is  $ \frac{\mathrm{d}^{2n}y}{\mathrm{d}x^{2n}} = (-1)^{n}2^{2n}\cos(1 - 2x) $.</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Answer\nLet  $ P_k $ be the statement that, for some value n = k:\n $ \frac{\mathrm{d}^{2k}y}{\mathrm{d}x^{2k}} = (-1)^{k}2^{2k}\cos(1 - 2x) $\n $ \frac{\mathrm{d}y}{\mathrm{d}x} = 2\sin(1 - 2x) $,  $ \frac{\mathrm{d}^{2}y}{\mathrm{d}x^{2}} = -4\cos(1 - 2x) $\n $ \mathrm{So~for~}n = 1 $:\n $ \frac{\mathrm{d}^{2}y}{\mathrm{d}x^{2}} = (-1)^{1} \times 2^{2}\cos(1 - 2x) = -4\cos(1 - 2x) $</td><td style='text-align: center; word-wrap: break-word;'>Write your opening inductive statement.\n\nDifferentiate twice for the n = 1 case.</td></tr><tr><td colspan="2">This shows that  $ P_1 $ is true.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ \frac{\mathrm{d}}{\mathrm{d}x}((-1)^{k}2^{2k}\cos(1 - 2x)) = (-1)^{k}(-1)2 \times 2^{2k}\sin(1 - 2x) $\n $ \frac{\mathrm{d}}{\mathrm{d}x}((-1)^{k+1}2^{2k+1}\sin(1 - 2x)) = (-1)^{k+1}(-1)2 \times 2^{2k+1}\cos(1 - 2x) $\n $ = (-1)^{k+1}2^{2(k+1)}\cos(1 - 2x) $</td><td style='text-align: center; word-wrap: break-word;'>Differentiate the kth case twice to obtain the (k + 1)th case.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Note this is the  $ P_k $ statement with k replaced by k + 1.</td><td style='text-align: center; word-wrap: break-word;'>Therefore,  $ P_k \Rightarrow P_{k+1} $.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Note the inductive step.</td><td style='text-align: center; word-wrap: break-word;'>Hence, since  $ P_1 $ is true and  $ P_k \Rightarrow P_{k+1} $, by mathematical induction,  $ P_n $ is true for all n ≥ 1.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Finish the inductive proof.</td><td style='text-align: center; word-wrap: break-word;'></td></tr></table>

Next, let us consider recurrence relations. As an example, we will first look at  $ u_{n+1} = \frac{4u_n + 3}{u_n + 2} $, where  $ u_1 = 1 $. Our task is to show that  $ u_n < 3 $; that is, all terms are smaller than 3.

<!-- page 156 -->

We state our $P_{k}$, which is $u_{k}<3$, and is what we are trying to show.

For the case when $n=1$ we know $u_{1}=1$ so it is definitely less than 3, as it is stated as 1.

Next take $u_{k+1}=\frac{4u_{k}+3}{u_{k}+2}$ and subtract 3 from both sides to get $u_{k+1}-3=\frac{4u_{k}+3}{u_{k}+2}-3=\frac{4u_{k}+3-3(u_{k}+2)}{u_{k}+2}=\frac{u_{k}-3}{u_{k}+2}$. It is easier to show this is greater or less than 0 rather than greater than or less than some value $a$.

After simplifying we get  $ u_{k+1} - 3 = 1 - \frac{5}{u_k + 2} $. If  $ u_k < 3 $ then  $ \frac{5}{u_k + 2} > 1 $ so  $ 1 - \frac{5}{u_k + 2} < 0 $

This implies that  $ u_{k+1} - 3 < 0 $ and  $ u_{k+1} < 3 $. Thus,  $ P_k \Rightarrow P_{k+1} $. Hence, since  $ P_1 $ is true and  $ P_k \Rightarrow P_{k+1} $, by mathematical induction  $ P_n $ is true for all  $ n \geq 1 $.

You don't always need to subtract from both sides, but it does make the process more straightforward.



<div style="text-align: center;"><img src="imgs/img_in_image_box_925_186_967_226.jpg" alt="Image" width="3%" /></div>


## TIP

### WORKED EXAMPLE 7.4

Prove by mathematical induction the two following problems.

a If  $ u_{n+1} = \frac{5u_n - 2}{u_n + 2} $, where  $ u_1 = 5 $. Show that  $ u_n > 2 $ for all  $ n \geq 1 $.

b If  $ u_{n+1} = 3u_n + 2 $, where  $ u_1 = 1 $. Show that  $ u_n = 2 \times 3^{n-1} - 1 $ for all  $ n \geq 1 $.

Answer

a Let  $ P_k $ be the statement that, for some value  $ n = k $,  $ u_k > 2 $.

Subtract 2 from both sides.

 $ u_1 = 5 > 2 $. Hence,  $ P_1 $ is true.

Show  $ n = 1 $ case is true.

Then  $ u_{k+1} - 2 = \frac{5u_k - 2}{u_k + 2} - 2 $

 $ \Rightarrow \frac{5u_k - 2 - 2(u_k + 2)}{u_k + 2} $

Simplify the algebra.

 $ \Rightarrow \frac{3u_k - 6}{u_k + 2} $

 $ = 3 - \frac{12}{u_k + 2} $

So if  $ u_k > 2 $,  $ \frac{12}{u_k + 2} < 3 $, then  $ 3 - \frac{12}{u_k + 2} > 0 $.

Hence  $ u_{k+1} - 2 > 0 $.

Therefore  $ P_k \Rightarrow P_{k+1} $.

So by mathematical induction,  $ P_n $ is true for all  $ n \geq 1 $.

b Let  $ P_k $ be the statement that, for some value  $ n = k $,  $ u_k = 2 \times 3^{k-1} $.

Conclude mathematical induction.

Make general statement.

 $ u_1 = 2 \times 3^0 - 1 = 1 $ so  $ P_1 $ is true.

Show  $ n = 1 $ is true.

Then  $ u_{k+1} = 3(2 \times 3^{k-1} - 1) + 2 $

 $ \Rightarrow 2 \times 3^k - 3 + 2 $

 $ \therefore u_{k+1} = 2 \times 3^k - 1 $

Therefore  $ P_k \Rightarrow P_{k+1} $.

So by mathematical induction,  $ P_n $ is true for all  $ n \geq 1 $.

Complete the inductive process.

<!-- page 157 -->

Finally, let us look at matrices. Consider the matrix  $ \mathbf{A} = \begin{pmatrix} 1 & 0 \\ 1 & 1 \end{pmatrix} $. It is given that  $ \mathbf{A}^n = \begin{pmatrix} 1 & 0 \\ n & 1 \end{pmatrix} $

Let  $ P_{k} $ be the statement that, for some value n = k,  $ \mathbf{A}^{k} = \begin{pmatrix} 1 & 0 \\ k & 1 \end{pmatrix} $.

To show this result is true we must show the first case is true. This is achieved by considering

 $ \mathbf{A}^{1} = \begin{pmatrix} 1 & 0 \\ 1 & 1 \end{pmatrix} $, which is true. Hence  $ P_{1} $ is true.

Then consider  $ \mathbf{A}^k\mathbf{A} $, which is  $ \begin{pmatrix} 1 & 0 \\ k & 1 \end{pmatrix} \begin{pmatrix} 1 & 0 \\ 1 & 1 \end{pmatrix} = \begin{pmatrix} 1 & 0 \\ k + 1 & 1 \end{pmatrix} $. So it is true that  $ P_k \Rightarrow P_{k+1} $.

Since $P_{1}$ is true and $P_{k} \Rightarrow P_{k+1}$, by mathematical induction, $P_{n}$ is true for all $n \geqslant 1$.

### WORKED EXAMPLE 7.5

The matrix  $ \mathbf{B} = \begin{pmatrix} 2 & 1 \\ 0 & 1 \end{pmatrix} $ is to be raised to the power n to give  $ \mathbf{B}^n = \begin{pmatrix} 2^n & 2^n - 1 \\ 0 & 1 \end{pmatrix} $. Prove this is true by mathematical induction.

## Answer

Let  $ P_{k} $ be the statement that, for some value n = k:

 $$ P_{k} $$ 

 $$ \mathbf{B}^{k}=\begin{pmatrix}2^{k}&2^{k}-1\\ 0&1\end{pmatrix} $$ 

For $P_1$: When $n=1$, $\mathbf{B}^1 = \begin{pmatrix} 2^1 & 2^1 - 1 \\ 0 & 1 \end{pmatrix} = \begin{pmatrix} 2 & 1 \\ 0 & 1 \end{pmatrix} = \mathbf{B}$.

Show the first case is true.



Hence, true for the case when n = 1.

 $$ \mathbf{B}^{k}\mathbf{B}=\begin{pmatrix}2^{k}&2^{k}-1\\ 0&1\end{pmatrix}\begin{pmatrix}2&1\\ 0&1\end{pmatrix} $$ 

Show that $P_{k}$ leads to $P_{k+1}$.

This is  $ \begin{pmatrix} 2 \times 2^k & 2^k + 2^k - 1 \\ 0 & 1 \end{pmatrix} = \begin{pmatrix} 2^{k+1} & 2^{k+1} - 1 \\ 0 & 1 \end{pmatrix} = \mathbf{B}^{k+1} $.

Therefore,  $ P_k \Rightarrow P_{k+1} $.

So since $P_{1}$ is true and $P_{k} \Rightarrow P_{k+1}$, by mathematical induction, $P_{n}$ is true for all $n \geq 1$.

Finish inductive proof.



### EXPLORE 7.1

If a matrix is given as  $  \mathbf{C} = \begin{pmatrix} \frac{1}{2} & 1 \\ 0 & 1 \end{pmatrix}  $, work in groups to determine  $  \mathbf{C}^n  $ and find out what happens as  $  n \to \infty  $.

## EXERCISE 7A

## Do not use a calculator in this exercise

P 1 Prove, by mathematical induction, that  $ \sum_{r=1}^{\infty} r(r+3) = \frac{1}{3} n(n+1)(n+5) $ for all  $ n \geq 1 $.

<!-- page 158 -->

2 Prove, by mathematical induction, that the sum of the first $n$ terms of an arithmetic sequence is $\frac{n}{2}[2a + (n-1)d]$, where $a$ is the first term and $d$ is the common difference.

3 Given that  $ u_{n+1}=2u_{n}+1 $ and that  $ u_{1}=1 $, show, by mathematical induction, that  $ u_{n}=2^{n}-1 $ for all  $ n\geqslant1 $.

P 4 Use mathematical induction to prove that  $ \sum_{r=1}^{n} r(r^2 - 1) = \frac{1}{4}n(n+1)(n-1)(n+2) $.

P 5 A function is given as  $ y = \cos 2x + 2 \sin 2x $.

a Find the second derivative.

b Using mathematical induction, show that  $ \frac{\mathrm{d}^{2n}y}{\mathrm{d}x^{2n}}=(-1)^{n}2^{2n}[\cos2x+2\sin2x] $ for values  $ n\geq1 $.

6 The recurrence relation  $ u_{n+1}=2u_{n}-2 $ has first term  $ u_{1}=10 $.

a Find the values of  $ u_{2} $,  $ u_{3} $ and  $ u_{4} $.

b Prove by mathematical induction that  $ u_{n}=4\times2^{n}+2 $.

P 7 Prove, by mathematical induction, that  $ u_{n} > \frac{1}{2} $ is true for the relation  $ u_{n+1} = \frac{u_{n}^{2} + 1}{u_{n} + 2} $ where  $ u_{1} = 1 $.

P 8 Using mathematical induction, prove that  $ \sum_{r=1}^{n}(3r^{2}+r)=n(n+1)^{2} $.

## 146 PPS

9 A matrix is given as  $  \mathbf{A} = \begin{pmatrix} \frac{1}{3} & 0 \\ -1 & 1 \end{pmatrix}  $.

a Determine the values of  $ A^{2} $,  $ A^{3} $ and  $ A^{4} $.

b Prove, by mathematical induction, that  $ \mathbf{A}^n = \begin{pmatrix} \frac{1}{3^n} & 0 \\ \frac{3}{2}\left(\frac{1}{3^n} - 1\right) & 1 \end{pmatrix} $.

c State  $ A^{n} $ when  $ n \to \infty $.

### 7.2 Proof by induction for divisibility

Consider the function  $ f(n) = 2^{2n+2} + 5 $ for  $ n \geq 0 $. We are given that each term is divisible by 3.

We check a few terms. For example,  $ f(0) = 9 $,  $ f(1) = 21 $ and  $ f(2) = 69 $ so it seems as though they are all divisible by 3.

How can this be proved by mathematical induction?

Let  $ P_k $ be the statement that, for some value  $ n = k $,  $ f(k) = 2^{2k+2} + 5 $ is divisible by 3.

The first case, $n=0$, is certainly true so we can say that $P_{0}$ is true. All the previous examples had a way of getting to the next term, by adding, multiplying, differentiating and so on.

For this function we are going to write down the case for $n=k+1$. This is $f(k+1)=2^{2(k+1)+2}+5$. Then consider $f(k+1)-f(k)=2^{2k+4}-2^{2k+2}$. Now, before we progress, recall that our statement was to assume that $f(k)$ is divisible by 3. If this is true, then by writing $f(k+1)=2^{2k+4}-2^{2k+2}+f(k)$ we just need to show that $2^{2k+4}-2^{2k+2}$ is divisible by 3.

<!-- page 159 -->

$ 2^{2k+4} - 2^{2k+2} = 2^4 \times 2^{2k} - 2^2 \times 2^{2k} = 16 \times 2^{2k} - 4 \times 2^{2k} = 12 \times 2^{2k} $ or  $ 3 \times 4 \times 2^{2k} $. This is divisible by 3.

So if  $ 2^{2k+4}-2^{2k+2} $ and  $ f(k) $ are both divisible by 3, then  $ f(k+1) $ must be divisible by 3.

Therefore,  $ P_k \Rightarrow P_{k+1} $, and since  $ P_0 $ is true and  $ P_k \Rightarrow P_{k+1} $, by mathematical induction  $ P_n $ true for all  $ n \geq 0 $.

This process is summarised in Key point 7.2.

<div style="text-align: center;"><img src="imgs/img_in_image_box_29_376_72_411.jpg" alt="Image" width="3%" /></div>


### KEY POINT 7.2

If $f(a)$ is assumed to be divisible by $b$, and $k$ is divisible by $b$, then $f(a+1)-f(a)=k$ implies that $f(a+1)$ must also be divisible by $b$.

### WORKED EXAMPLE 7.6

A function is defined as  $ f(n) = 3^{n+2} + 5 $. Using mathematical induction, prove that  $ 3^{n+2} + 5 $ is always divisible by 2 for  $ n \geqslant 0 $.
Answer
Let  $ P_{k} $ be the statement that, for some value n = k,  $ 3^{k+2} + 5 $ is divisible by 2.
State  $ P_{k} $.
For  $ P_{0} $: when n = 0, f(0) = 14. So  $ P_{0} $ is true.
Show base case is true.
Then  $ f(k+1) = 3^{k+1+2} + 5 = 3 \times 3^{k+2} + 5 $.
Write down the difference.
So  $ f(k+1) - f(k) = 3 \times 3^{k+2} + 5 - 3^{k+2} - 5 $
We assumed  $ f(k) $ was divisible by 2, so we can then say that
State initial assumption..
 $ f(k+1) = 2 \times 3^{k+2} + f(k) $, which is clearly divisible by 2.
Show  $ f(k+1) $ must be divisible by 2.
Therefore  $ P_{k} \Rightarrow P_{k+1} $.
Hence, for all n  $ \geqslant 0 $, by mathematical induction  $ P_{n} $ is always true.
Inductive step.
Final conclusion.

This approach also works with polynomials, for example, showing that  $ f(n) = n^{2} + (n + 2)^{2} $ is divisible by 2.

We may have identified that this will be an even number, but we are going to prove it using mathematical induction.

Let  $ P_k $ be the statement that, for some value  $ n = k $,  $ \mathrm{f}(k) = k^2 + (k + 2)^2 $ is divisible by 2.

We see that  $ f(0) = 0^2 + 2^2 = 4 $, so  $ f(0) $ is divisible by 2. We can say that  $ P_0 $ is true.

Then  $ f(k+1)=(k+1)^2+(k+1+2)^2=(k+1)^2+(k+3)^2 $.

 $$ \begin{aligned}Next,\mathrm{f}(k+1)-\mathrm{f}(k)&=(k+1)^{2}+(k+3)^{2}-k^{2}-(k+2)^{2}\\&=k^{2}+2k+1+k^{2}+6k+9-k^{2}-k^{2}-4k-4\\&=2k^{2}+8k+10-(2k^{2}+4k+4)\\&=4k+6=2(2k+3)\end{aligned} $$ 

which is divisible by 2 and so it follows that  $ P_k \Rightarrow P_{k+1} $.

<!-- page 160 -->

We can now conclude our argument. Since  $ P_0 $ is true and  $ P_k \Rightarrow P_{k+1} $, by mathematical induction  $ P_n $ is true for all  $ n \geqslant 0 $.

### WORKED EXAMPLE 7.7

A function is given as  $ f(n) = (n+2)^3 + (2n+1)^3 $. Prove by induction that  $ f(n) $ is divisible by 3 for all values  $ n \geq 0 $.

Answer
Let  $ P_k $ be the statement that, for some value  $ n = k $,  $ (k+2)^3 + (2k+1)^3 $ is divisible by 3.

For  $ P_0 $: Let  $ n = 0 \Rightarrow f(0) = (0+2)^3 + (0+1)^3 = 9 = 3 \times 3 $ which is divisible by 3 so  $ f(0) $ is divisible by 3. So  $ P_0 $ is true.

 $ f(k+1) = (k+3)^3 + (2k+3)^3 $, then using  $ f(k+1) - f(k) = (k+3)^3 + (2k+3)^3 - (k+2)^3 - (2k+1)^3 = k^3 + 9k^2 + 27k + 27 + 8k^3 + 36k^2 + 54k + 27 - k^3 - 6k^2 - 12k - 8 - 8k^3 - 12k^2 - 6k - 1 $

which gives  $ 27k^2 + 63k + 45 $.

Hence,  $ f(k+1) = 3(9k^2 + 21k + 15) + f(k) $ which is divisible by 3 as  $ 3(9k^2 + 21k + 15) $ has a factor of 3. We have stated earlier that  $ f(k) $ is divisible by 3, and therefore  $ P_k \Rightarrow P_{k+1} $.

Thus, since  $ P_0 $ is true and  $ P_k \Rightarrow P_{k+1} $,  $ P_n $ is true by mathematical induction for all  $ n \geq 0 $.

State  $ P_k $.

Show the first value works.

Find the difference between successive values.

Show the inductive step.

State the conclusion.

## EXERCISE 7B

## Do not use a calculator in this exercise

1 Prove, by mathematical induction, that  $ n^{3} + 2n $ is divisible by 3 for all  $ n \geqslant 1 $.

2 Prove, by mathematical induction, that $8^{n}-3^{n}$ is divisible by 5 for all $n\geqslant1$.

3 Prove, by mathematical induction, that  $ 3^{2n} - 1 $ is divisible by 8 for all  $ n \geqslant 1 $.

4 Prove, by mathematical induction, that  $ 3^{(3n+2)} + 4 $ is divisible by 13 for  $ n \geqslant 0 $.

5 A function is given as  $ f(n) = (2n + 1)^3 + (3n - 2)^2 + n + 3 $. Using mathematical induction, prove that  $ f(n) $ is always even for  $ n \geq 0 $.

6 Using mathematical induction, prove that  $ 8^{n}-1 $ is always divisible by 7.

7 Prove, by mathematical induction, that  $ n^{3}-n $ is divisible by 6 for  $ n \geqslant 2 $.

8 A function is given as  $ f(n) = 3^{4n+3} + 7^{2n+1} + 6 $. Show by using proof by induction that  $ f(n) $ is always divisible by 8 for  $ n \geq 0 $.

<!-- page 161 -->

<div style="text-align: center;"><img src="imgs/img_in_image_box_7_151_39_180.jpg" alt="Image" width="2%" /></div>


Prove by induction that  $ \sum_{r=1}^{n}(3r^{5}+r^{3})=\frac{1}{2}n^{3}(n+1)^{3} $ for all  $ n\geq1 $.

Cambridge International AS & A Level Further Mathematics 9231 Paper 1 Q7 (first part) June 2008

## Answer

Let $P_k$ be the statement that, for some value $n=k$, $\sum_{r=1}^{k}(3r^5+r^3)=\frac{1}{2}k^3(k+1)^3$.

For $n=1:P_1$ is $\sum_{r=1}^{1}(3r^5+r^3)=(3\times1+1)=4$, and also $\frac{1}{2}\times1\times(1+1)^3=4$.

Therefore, $P_{1}$ is true.

Then  $ \sum_{r=1}^{k+1}(3r^{5}+r^{3})=\frac{1}{2}k^{3}(k+1)^{3}+3(k+1)^{5}+(k+1)^{3} $,

which is  $ (k+1)^3\left[\frac{1}{2}k^3+3(k+1)^2+1\right]=\frac{1}{2}(k+1)^3[k^3+6k^2+12k+8]=\frac{1}{2}(k+1)^3(k+2)^3 $

 $ \quad=\frac{1}{2}(k+1)^3(k+1+1)^3 $

Therefore  $ P_k \Rightarrow P_{k+1} $.

Hence, since $P_{1}$ is true and $P_{k} \Rightarrow P_{k+1}$, $P_{n}$ is true by mathematical induction for all values $n \geqslant 1$.

<div style="text-align: center;"><img src="imgs/img_in_image_box_20_794_62_834.jpg" alt="Image" width="3%" /></div>


## DID YOU KNOW?

As far back as 370 BCE, ancient mathematicians such as Plato were using inductive proof in an implicit way. Even Euclid used a form of induction when proving the number of primes is infinite.

The first mathematician to explicitly state the inductive procedure in the correct manner was Blaise Pascal in 1665.

<!-- page 162 -->

## Checklist of learning and understanding

## Setting up the proof:

Let  $ P_{k} $ be the statement that, for some value k, your expression is true.

Start with the smallest possible value for n and show the statement is true for  $ P_{0} $, or  $ P_{1} $, or whichever  $ P_{n} $ has been found to be true.

Show this statement leads to the next value  $ k + 1 $. See the separate sections below for the method.

Complete the proof with a conclusion that mentions your $P_n$ is true for all values as stated in the question. The statement should be similar to ‘Since $P_0$ is true and $P_k \Rightarrow P_{k+1}$, by mathematical induction $P_n$ is true for all $n \geq 0$.

## Summations:

If  $ \sum_{r=1}^{n} f(r) = g(n) $ is given, assume  $ \sum_{r=1}^{n} f(r) = g(k) $ is true for  $ P_k $ and add  $ f(k+1) $ to  $ g(k) $ to show that  $ P_k \Rightarrow P_{k+1} $.

## Derivatives:

If $y = \mathrm{f}(x)$, $\frac{\mathrm{d}^n y}{\mathrm{d}x^n} = \mathrm{f}^{(n)}(x)$ is given, assume $\frac{\mathrm{d}^k y}{\mathrm{d}x^k} = \mathrm{f}^{(k)}(x)$ is true for $P_k$. Differentiate $\frac{\mathrm{d}^k y}{\mathrm{d}x^k} = \mathrm{f}^{(k)}(x)$ as many times as required to show $P_k \Rightarrow P_{k+1}$.

If  $ u_{n+1} = f(u_n) $ and  $ u_n = g(n) $ are given, assume  $ u_k = g(k) $ is true for  $ P_k $ and put this into  $ f(u_k) $ to obtain  $ u_{k+1} $. This leads to the inductive step where  $ P_k \Rightarrow P_{k+1} $.

## Recurrence relations:

## Matrices:

If  $ \mathbf{A}^n $ and  $ \mathbf{A} $ are given, assume  $ \mathbf{A}^k $ is true for  $ P_k $ and determine  $ \mathbf{A}^k\mathbf{A} $ to show  $ P_k \Rightarrow P_{k+1} $

## Divisibility:

If  $ f(n) $ is given as being divisible by  $ b $, assume  $ f(k) $ is divisible by  $ b $ for  $ P_k $ and show that  $ f(k+1) - f(k) = ab $, which leads to  $ P_k \Rightarrow P_{k+1} $.

<!-- page 163 -->

## Do not use a calculator in this exercise

1 Prove by mathematical induction that, for all non-negative integers $n$, $11^{2n} + 25^{n} + 22$ is divisible by 24.

Cambridge International AS & A Level Further Mathematics 9231 Paper 11 Q3 June 2014

2 It is given that  $ u_r = r \times r! $ for  $ r = 1, 2, 3, \ldots $. Let  $ S_n = u_1 + u_2 + u_3 + \cdots + u_n $. Write down the values of  $ 2! - S_1, 3! - S_2, 4! - S_3, 5! - S_4 $.

Conjecture a formula for  $ S_{n} $.

Prove, by mathematical induction, a formula for $S_{n}$, for all positive integers $n$.

Cambridge International AS & A Level Further Mathematics 9231 Paper 11 Q3 November 2014

3 The sequence  $ a_{1}, a_{2}, a_{3}, \ldots $ is such that  $ a_{1} > 5 $ and  $ a_{n+1} = \frac{4a_{n}}{5} + \frac{5}{a_{n}} $ for every positive integer n.

Prove by mathematical induction that $a_{n}>5$ for every positive integer $n$.

Prove also that  $ a_n > a_{n+1} $ for every positive integer n.

Cambridge International AS & A Level Further Mathematics 9231 Paper 11 Q3 June 2015

<!-- page 164 -->

Hence, determine an expression for  $ \sum_{r=n+1}^{2n}(r^2-r) $.

1 Prove by mathematical induction that  $ \sum_{r=1}^{n}(r^{2}-r)=\frac{1}{3}n(n^{2}-1) $.

2 The cubic equation  $ x^{3}-5x^{2}+1=0 $ has roots  $ \alpha,\beta,\gamma $.

a Find the values of  $ S_{1} $ and  $ S_{3} $.

Another cubic equation has roots  $ \alpha^{2}, \beta^{2}, \gamma^{2} $.

b Find the cubic equation with these roots.

c Hence, or otherwise, determine the result of $S_{6}$.

3 The curve C is given as  $ y=\frac{2+x}{x^{2}+5x+4} $

a Write down the asymptotes of C.

b Find  $ \frac{dy}{dx} $.

c Determine the number of turning points.

4 Three planes are given as:

d Sketch the curve C, showing all asymptotes, and stating intercepts with the coordinate axes.

 $ \Pi_1: x - 2y + 3z = 5 $,  $ \Pi_2: -x + 4y + z = -5 $ and  $ \Pi_3: 2x - 2y + 9z = 9 $.

By writing these three equations in the form $Ax = b$, state the matrix $A$ and perform row operations on your augmented matrix until it is in row echelon form.

5 The polar curve $C$ is given as $r=2\sin 2\theta$, for $0\leqslant\theta\leqslant\frac{\pi}{2}$.

a Sketch the curve C.

c Evaluate the area inside the polar curve C, for the interval  $ 0 \leqslant \theta \leqslant \frac{\pi}{2} $.

b Find the greatest distance of the curve from the y-axis.

Four points $A(2,3,1)$, $B(0,4,-3)$, $C(2,2,0)$ and $D(-1,0,1)$ are given.

The line $l_{1}$ passes through $A$ and $B$, and the line $l_{2}$ passes through $C$ and $D$.

a Find the angle between the lines  $ l_{1} $ and  $ l_{2} $

b Find the shortest distance between the lines  $ l_{1} $ and  $ l_{2} $.

Prove by mathematical induction that, for all values $n\geq1,7^{n}+2^{3n}-1$ is divisible by 7.

The equation  $ x^{3}-4x+2=0 $ has roots  $ \alpha $,  $ \beta $,  $ \gamma $.

a Find the value of  $ \frac{1}{\alpha^{2}}+\frac{1}{\beta^{2}}+\frac{1}{\gamma^{2}} $.

b Show that the matrix  $ \begin{pmatrix} 1 & \alpha & 1 \\ 2\gamma & 0 & \beta \\ \gamma & 0 & 3\beta \end{pmatrix} $ is non-singular.

<!-- page 165 -->

9 Express  $ u_{n}=\frac{1}{4n^{2}-1} $ in partial fractions, and hence find  $ \sum_{n=1}^{n}u_{n} $ in terms of n.

Deduce that the infinite series  $ u_{1}+u_{2}+u_{3}+\ldots $ is convergent and state the sum to infinity.

Cambridge International AS & A Level Mathematics 9231 Paper 1 Q1 June 2006

10 The curve C has equation  $ y=\frac{5(x-1)(x+2)}{(x-2)(x+3)} $

i Express $y$ in the form $P + \frac{Q}{x-2} + \frac{R}{x+3}$.

ii Show that  $ \frac{dy}{dx}=0 $ for exactly one value of x and find the corresponding value of y.

iii Write down the equations of all the asymptotes of C.

iv Find the set of values of k for which the line y = k does not intersect C.

Cambridge International AS & A Level Further Mathematics 9231 Paper 1 Q11a November 2003

Given that the matrix  $  \mathbf{A} = \begin{pmatrix} 2 & 2 & 4 \\ 2 & 2 & 2 \\ 2 & 3 & 2 \end{pmatrix}  $ is non-singular, find the matrix B such that  $  B A^2 = I  $.

2 Given that  $ u_{n+1} = \frac{4u_n + 7}{u_n + 2} $ has first term  $ u_1 = 3 $, prove, by mathematical induction, that  $ u_n < 4 $ for all  $ n \geq 1 $.

