# Non-parametric tests

<!-- Cambridge International AS  A Level Further Mathematics Coursebook (Lee Mckelvey Martin Crozier) .pdf p261-290 -->

<!-- page 261 -->

<div style="text-align: center;"><img src="imgs/img_in_image_box_2_6_1186_771.jpg" alt="Image" width="96%" /></div>


# Chapter 11 Non-parametric tests

## In this chapter you will learn how to:

understand the idea of a non-parametric test and when it might be useful

understand the basis of the sign test, the Wilcoxon signed-rank test and the Wilcoxon rank-sum test

use a single-sample sign test and a single-sample Wilcoxon signed-rank test to test a hypothesis concerning a population median

use a paired-sample sign test, a Wilcoxon matched-pairs signed-rank test and a Wilcoxon rank-sum test, as appropriate, to test for identity of populations.

<div style="text-align: center;"><img src="imgs/img_in_image_box_6_1244_1178_1570.jpg" alt="Image" width="95%" /></div>

<!-- page 262 -->

<div style="text-align: center;">PREREQUISITE KNOWLEDGE</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Where it comes from</td><td style='text-align: center; word-wrap: break-word;'>What you should be able to do</td><td style='text-align: center; word-wrap: break-word;'>Check your skills</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>AS &amp; A Level Mathematics Probability &amp; Statistics 1, Chapter 7</td><td style='text-align: center; word-wrap: break-word;'>Find probabilities from the binomial distribution.</td><td style='text-align: center; word-wrap: break-word;'>1 Given  $ X \sim \text{Bin}(10, 0.5) $, find  $ P(X \leq 2 \cup X \geq 9) $.</td></tr></table>

## Hypothesis testing with few distributional assumptions

In Chapter 9 we carried out hypothesis tests for the mean. We specified a number of conditions such as large/small sample size and known/unknown variance and we assumed that there was a underlying normal distribution. We carried out a test using the normal distribution or a t-test.

All of these tests are called parametric tests because we know the underlying distribution. There is a population mean which is a parameter we can test.

If we do not know the underlying distribution then we carry out a non-parametric test. If the sample size is small, we must develop new tests to be able to gather information regarding the data. The measure of centrality in these cases is usually the median.

### 11.1 Non-parametric tests

Sometimes when we wish to perform a hypothesis test, we are not able to assume the type of distribution from which the sample data came. In fact, it may not have a distribution. This causes some problems as we cannot assume a population parameter, for example, the mean or variance. In this case, we say that the data is non-parametric. A variety of non-parametric tests have been developed to cater for this. Each test is based on certain assumptions so, depending what we can assume, we can choose the correct test.

This chapter is split into two main parts, but the ideas are interlinked. In the first part we focus on single-sample statistics. In the second part we focus on two-sample statistics. Most of the ideas in the second part will be introduced in the first part. The assumptions for each test are listed in the following table.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Type of test</td><td style='text-align: center; word-wrap: break-word;'>Test</td><td style='text-align: center; word-wrap: break-word;'>Assumptions</td></tr><tr><td rowspan="2">Single sample</td><td style='text-align: center; word-wrap: break-word;'>Sign test</td><td style='text-align: center; word-wrap: break-word;'>• The underlying data are continuous\n• The data are independent</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Wilcoxon signed-rank test</td><td style='text-align: center; word-wrap: break-word;'>• The underlying data are symmetric\n• The underlying data are continuous\n• The data are independent</td></tr><tr><td rowspan="3">Two sample</td><td style='text-align: center; word-wrap: break-word;'>Paired sign test</td><td style='text-align: center; word-wrap: break-word;'>• The data are in matched pairs\n• The differences between matched pairs are continuous\n• The data are independent</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Wilcoxon matched-pairs signed-rank test</td><td style='text-align: center; word-wrap: break-word;'>• The data are in matched pairs\n• The differences between matched pairs are symmetric\n• The differences between matched pairs are continuous\n• The data are independent</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Wilcoxon rank-sum test</td><td style='text-align: center; word-wrap: break-word;'>• The two samples are independent\n• The underlying data are symmetric\n• The underlying data are continuous</td></tr></table>

<!-- page 263 -->

### 11.2 Single-sample sign test

We can use the single-sample sign test when we wish to see whether data differ from a stated value for the median. It is important to understand that the median is not a parameter, as we do not know the underlying distribution. This test is based on the assumptions listed in the previous table.

To perform the single-sample sign test, mark the values that are greater than the stated median with a + sign, and mark those that are less than the stated median with a - sign. If the data are well distributed about the median, we would expect an equal number of + and - signs. So there should be a probability of 0.5 that any data point is above the median and a probability of 0.5 that it is below the median.

Some people think that the single-sample sign test is quite a crude method, but it does give some useful information. The single-sample sign test is a special case of the binomial test, when n is the number of data points and the probability of ‘success’ is 0.5, as shown in Key point 11.1.

<div style="text-align: center;"><img src="imgs/img_in_image_box_26_570_69_606.jpg" alt="Image" width="3%" /></div>


### KEY POINT 11.1

Given $n$ data points, a single-sample sign test is created using $X \sim \mathrm{Bin}(n, 0.5)$. The test statistic can be the number of + signs, that is the number of data points greater than the median. We can calculate the probability that $X$ is above this test statistic, below this test statistic, or either in the case of a two-tailed test.

This can be expressed as  $ \mathrm{P}(X \leq ts \mid X \sim \mathrm{Bin}(n, 0.5)) $ or  $ \mathrm{P}(X \geq ts \mid X \sim \mathrm{Bin}(n, 0.5)) $ where ts stands for test statistic.

### WORKED EXAMPLE 11.1

It is believed that the following dataset comes from a population with median 135.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>150</td><td style='text-align: center; word-wrap: break-word;'>130</td><td style='text-align: center; word-wrap: break-word;'>125</td><td style='text-align: center; word-wrap: break-word;'>140</td><td style='text-align: center; word-wrap: break-word;'>170</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>140</td><td style='text-align: center; word-wrap: break-word;'>190</td><td style='text-align: center; word-wrap: break-word;'>180</td><td style='text-align: center; word-wrap: break-word;'>175</td><td style='text-align: center; word-wrap: break-word;'>165</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>160</td><td style='text-align: center; word-wrap: break-word;'>130</td><td style='text-align: center; word-wrap: break-word;'>140</td><td style='text-align: center; word-wrap: break-word;'>140</td><td style='text-align: center; word-wrap: break-word;'>145</td></tr></table>

Perform a single-sample sign test, at the 5% significance level, to test this claim.

## Answer

H $ _{0} $: The population median is 135.

H $ _{1} $: The population median is not 135.

First, state the hypotheses.

Notice that this is a two-tailed test.

<!-- page 264 -->

<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Value</td><td style='text-align: center; word-wrap: break-word;'>Sign</td><td style='text-align: center; word-wrap: break-word;'>Value</td><td style='text-align: center; word-wrap: break-word;'>Sign</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>150</td><td style='text-align: center; word-wrap: break-word;'>+</td><td style='text-align: center; word-wrap: break-word;'>140</td><td style='text-align: center; word-wrap: break-word;'>+</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>140</td><td style='text-align: center; word-wrap: break-word;'>+</td><td style='text-align: center; word-wrap: break-word;'>140</td><td style='text-align: center; word-wrap: break-word;'>+</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>160</td><td style='text-align: center; word-wrap: break-word;'>+</td><td style='text-align: center; word-wrap: break-word;'>175</td><td style='text-align: center; word-wrap: break-word;'>+</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>130</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>140</td><td style='text-align: center; word-wrap: break-word;'>+</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>190</td><td style='text-align: center; word-wrap: break-word;'>+</td><td style='text-align: center; word-wrap: break-word;'>170</td><td style='text-align: center; word-wrap: break-word;'>+</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>130</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>165</td><td style='text-align: center; word-wrap: break-word;'>+</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>125</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>145</td><td style='text-align: center; word-wrap: break-word;'>+</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>180</td><td style='text-align: center; word-wrap: break-word;'>+</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr></table>

Consider which values are above or below the stated median.

Here, the test statistic is 12, as there are 12 values above the stated median.

 $$ X\sim\operatorname{B i n}(15,0.5); $$ 

Since 12 is greater than $\frac{n}{2}$, which is 7.5, we need consider only the top tail.

 $$ P(X\geqslant12)={}^{15}C_{12}(0.5){}^{15}+{}^{15}C_{13}(0.5){}^{15} $$ 

 $$ +{}^{15}C_{14}(0.5)^{15}+{}^{15}C_{15}(0.5)^{15} $$ 

 $$ P(X\geqslant12)=0.017578 $$ 

Since we are looking at a two-tailed test, we consider 2.5% as our critical value.

There is sufficient evidence to suggest the population median is not 135.

E In a situation where we have zero instead of + or -, the data point is discounted. This is not required in this course.

It is possible to approximate the sign test to a normal distribution for large $n$ ($n>10$ is considered large here), as shown in Key point 11.2.

<div style="text-align: center;"><img src="imgs/img_in_image_box_98_1031_140_1067.jpg" alt="Image" width="3%" /></div>


### KEY POINT 11.2

Let $S = \min(\text{number of} + \text{signs}, \text{number of} - \text{signs})$ then $\mathrm{E}(S) = \frac{n}{2}, \mathrm{Var}(S) = \frac{n}{4}$.

For large $n (> 10)$, $T \sim \mathrm{N}\left(\frac{n}{2}, \frac{n}{4}\right)$, we can use the normal approximation of the binomial with $p = 0.5$. We must also make sure that we use a continuity correction. As we are approximating a discrete distribution with a continuous distribution, our $z$-value is:

 $$ z=\frac{S^{+}-\mu+0.5}{\sigma} $$ 

For example, if the test statistic is $S^{+}=5$, and we have approximated to $T\sim\mathrm{N}(15,7.5)$, we calculate the $z$-value as $z=\frac{5.5-15}{\sqrt{7.5}}$ since any value from 5 up to 5.5 rounds down to 5, and we are looking in this case at $\mathrm{P}(X<15)$.

<!-- page 265 -->

1 For the following dataset, calculate  $ S^{+} $based on each of the stated null hypotheses.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>133</td><td style='text-align: center; word-wrap: break-word;'>132</td><td style='text-align: center; word-wrap: break-word;'>155</td><td style='text-align: center; word-wrap: break-word;'>145</td><td style='text-align: center; word-wrap: break-word;'>157</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>140</td><td style='text-align: center; word-wrap: break-word;'>152</td><td style='text-align: center; word-wrap: break-word;'>167</td><td style='text-align: center; word-wrap: break-word;'>148</td><td style='text-align: center; word-wrap: break-word;'>158</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>163</td><td style='text-align: center; word-wrap: break-word;'>126</td><td style='text-align: center; word-wrap: break-word;'>179</td><td style='text-align: center; word-wrap: break-word;'>126</td><td style='text-align: center; word-wrap: break-word;'>149</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>182</td><td style='text-align: center; word-wrap: break-word;'>138</td><td style='text-align: center; word-wrap: break-word;'>172</td><td style='text-align: center; word-wrap: break-word;'>178</td><td style='text-align: center; word-wrap: break-word;'>166</td></tr></table>

a $\mathrm{H}_{0}$: population median is 150.

c $\mathrm{H}_{0}$: population median is 156.

b  $ H_{0} $: population median is 141.

d  $ H_{0} $: population median is 165.

2 For each of the following, find  $ \mathrm{P}(X \leqslant S^{+}|X \sim \mathrm{Bin}(n, 0.5)) $.

a  $ S^{+}=3, n=12 $ b  $ S^{+}=2, n=9 $ c  $ S^{+}=4, n=15 $ d  $ S^{+}=5, n=20 $

3 For each of the following, find  $ P(X \geq S^+ | X \sim \text{Bin}(n, 0.5)) $.

a  $ S^{+}=11, n=14 $ b  $ S^{+}=10, n=12 $ c  $ S^{+}=13, n=15 $ d  $ S^{+}=17, n=25 $

4 For the given hypotheses, sample size and value of  $ S^{+} $, state whether the null hypothesis should be rejected or not rejected at the 5% significance level. Do not use a normal approximation.

a  $ H_{0} $: the population median is 38.

 $ H_{1} $: the population median is less than 38.

 $ S^{+}=4, n=15 $

b  $ H_{0} $: the population median is 16.2.

 $ H_{1} $: the population median is not 16.2.

 $ S^{+}=5, n=20 $

c  $ H_{0} $: the population median is 154.

 $ H_{1} $: the population median is greater than 154.

 $ S^{+}=11, n=15 $

5 For each of the tests in question 4a–c, state E(S) and Var(S) and hence the value of the test statistic, when approximating to the normal distribution.

6 Acid rain is a problem for many areas. Rain is described as being acidic if its pH level is below 5.2. In a city, a biologist takes 12 water samples and measures the pH.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>4.73</td><td style='text-align: center; word-wrap: break-word;'>5.06</td><td style='text-align: center; word-wrap: break-word;'>4.87</td><td style='text-align: center; word-wrap: break-word;'>4.88</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>5.04</td><td style='text-align: center; word-wrap: break-word;'>5.16</td><td style='text-align: center; word-wrap: break-word;'>5.07</td><td style='text-align: center; word-wrap: break-word;'>5.09</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>5.11</td><td style='text-align: center; word-wrap: break-word;'>5.24</td><td style='text-align: center; word-wrap: break-word;'>5.25</td><td style='text-align: center; word-wrap: break-word;'>5.25</td></tr></table>

Test, at the 5% significance level, whether the rain in this city is acidic.

7 During 2017, the weekly amount of pocket money given to a random sample of 15-year-old children living in Chicago is:

20.00

During 2016, the median amount of pocket money given to 15-year-olds in Chicago was $11.00. Carry out a sign test to investigate the claim that the median weekly amount of pocket money given to 15-year-old children in Chicago has increased since 2016. Test this claim at the 10% level of significance.

<!-- page 266 -->

M 8 A website advertises used cars for sale. During September 2018, 12 cars of similar age and of the same model are for sale. The asking prices for the cars ($AUS) are:

5999, 8900, 7000, 6499, 7500, 7999, 8450, 6500, 7250, 8150, 4999, 5600

Investigate, at the 10% significance level, whether the median asking price for such cars is $7675.

b Still using the 10% level of significance, above what value would the median need to be to make the test significant?

M 9 The tax office claims that it takes 60 minutes to fill out their tax form. A researcher believes that it takes longer than this. A random sample of 20 people are selected, and the recorded times taken to complete the form are listed below.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>55</td><td style='text-align: center; word-wrap: break-word;'>62</td><td style='text-align: center; word-wrap: break-word;'>63</td><td style='text-align: center; word-wrap: break-word;'>68</td><td style='text-align: center; word-wrap: break-word;'>70</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>71</td><td style='text-align: center; word-wrap: break-word;'>58</td><td style='text-align: center; word-wrap: break-word;'>62</td><td style='text-align: center; word-wrap: break-word;'>64</td><td style='text-align: center; word-wrap: break-word;'>69</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>69</td><td style='text-align: center; word-wrap: break-word;'>72</td><td style='text-align: center; word-wrap: break-word;'>59</td><td style='text-align: center; word-wrap: break-word;'>62</td><td style='text-align: center; word-wrap: break-word;'>66</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>68</td><td style='text-align: center; word-wrap: break-word;'>69</td><td style='text-align: center; word-wrap: break-word;'>72</td><td style='text-align: center; word-wrap: break-word;'>69</td><td style='text-align: center; word-wrap: break-word;'>63</td></tr></table>

Use a suitable approximation to test the claim, at the 5% significance level, that the time taken to complete the form is more than 60 minutes.

### 11.3 Single-sample Wilcoxon signed-rank test

If we know that our underlying data are symmetric, we can refine the sign test by performing a Wilcoxon signed-rank test. This test factors in the magnitude of the rank, as well as whether it is above or below the median. Another condition placed on the use of this test is that the underlying data are continuous.

To perform the single-sample Wilcoxon signed-rank test, we rank the differences in the data points from the stated population median. The test statistic is the smaller value of the sums of the negative ranks and the sums of the positive ranks.

As shown in Key point 11.3, a Wilcoxon signed-rank test can be performed under the conditions that:

the underlying data are symmetric

the underlying data are continuous

the data are independent.

### KEY POINT 11.3

Where P is the sum of the ranks corresponding to the positive differences from the stated median and N is the sum of ranks corresponding to the negative differences from the stated median.

 $$ T=\min(P,N) $$ 

T is the test statistic for the Wilcoxon signed-rank test. Critical values can be found in the statistical tables. If the test statistic is below the critical value, we reject  $ H_{0} $.

<!-- page 267 -->

Even though the data are continuous, we are measuring the sums of ranks, and so the distribution of $T$ is discrete. Also, it is worth noting that $P$ can fall between the values 0 and $\frac{n(n+1)}{2}$. As all of the data points lie about the stated population median, their ranks will be between 1 and $n$, and the sum of these integers is $\frac{n(n+1)}{2}$.

The closer our test statistic is to 0, the more extreme the data; that is, the more likely data are to be above or below the stated population median. This is why we need our test statistic to be below the critical value from the tables.

### WORKED EXAMPLE 11.2

The weights (in kg) of ten randomly selected Spanish mackerel are recorded:

1.6, 1.1, 2.1, 2.4, 2.2, 2.9, 2.6, 2.3, 2.7, 1.9

Test, at the 5% significance level, whether the median weight is greater than 1.8kg.

## Answer

H₀: The population median weight of Spanish mackerel is 1.8kg.

Define the hypotheses.



 $ H_{1} $: The population median weight of Spanish mackerel is greater than 1.8kg.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Weight,  $ W_{i} $</td><td style='text-align: center; word-wrap: break-word;'>$ W_{i} $ - Median</td><td style='text-align: center; word-wrap: break-word;'>P</td><td style='text-align: center; word-wrap: break-word;'>N</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>1.6</td><td style='text-align: center; word-wrap: break-word;'>-0.2</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>1.1</td><td style='text-align: center; word-wrap: break-word;'>-0.7</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>7</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>2.1</td><td style='text-align: center; word-wrap: break-word;'>0.3</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>2.4</td><td style='text-align: center; word-wrap: break-word;'>0.6</td><td style='text-align: center; word-wrap: break-word;'>6</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>2.2</td><td style='text-align: center; word-wrap: break-word;'>0.4</td><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>2.9</td><td style='text-align: center; word-wrap: break-word;'>1.1</td><td style='text-align: center; word-wrap: break-word;'>10</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>2.6</td><td style='text-align: center; word-wrap: break-word;'>0.8</td><td style='text-align: center; word-wrap: break-word;'>8</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>2.3</td><td style='text-align: center; word-wrap: break-word;'>0.5</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>2.7</td><td style='text-align: center; word-wrap: break-word;'>0.9</td><td style='text-align: center; word-wrap: break-word;'>9</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>1.9</td><td style='text-align: center; word-wrap: break-word;'>0.1</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>Sums:</td><td style='text-align: center; word-wrap: break-word;'>46</td><td style='text-align: center; word-wrap: break-word;'>9</td></tr></table>

So the test statistic here is $T = \min(P, N) = 9$.

To perform this test, we first need to rank the magnitude of differences of each data point from the stated population median. Ignoring signs, start with the smallest difference and give this rank 1, the next smallest difference is given rank 2 and so on.



We can check P and N here using the fact that:

 $$ P+N=\frac{n(n+1)}{2} $$

<!-- page 268 -->

We look up the critical value in the statistical tables:


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td colspan="5">Level of significance</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>One-tailed</td><td style='text-align: center; word-wrap: break-word;'>0.05</td><td style='text-align: center; word-wrap: break-word;'>0.025</td><td style='text-align: center; word-wrap: break-word;'>0.01</td><td style='text-align: center; word-wrap: break-word;'>0.005</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Two-tailed</td><td style='text-align: center; word-wrap: break-word;'>0.1</td><td style='text-align: center; word-wrap: break-word;'>0.05</td><td style='text-align: center; word-wrap: break-word;'>0.02</td><td style='text-align: center; word-wrap: break-word;'>0.01</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>n=6</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>8</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>0</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>9</td><td style='text-align: center; word-wrap: break-word;'>8</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>10</td><td style='text-align: center; word-wrap: break-word;'>10</td><td style='text-align: center; word-wrap: break-word;'>8</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>11</td><td style='text-align: center; word-wrap: break-word;'>13</td><td style='text-align: center; word-wrap: break-word;'>10</td><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'>5</td></tr></table>

Since 9 < 10, (test statistic < critical value), there is sufficient evidence to reject  $ H_{0} $.

We are conducting a one-tailed test here at the 5% significance level.



There is sufficient evidence to suggest that the population median is not 1.8kg.

The critical value here is 10.



Be careful, as we require test statistic < critical value to reject $H_{0}$ here. This is different from the other tests performed in Chapter 9. We are testing whether the test statistic is significantly smaller than would happen by chance.

Write a conclusion in context.

If the ranks are tied, for example, two values both have rank 3, they occupy the 3rd and 4th placings and so we allocate them a tied rank of 3.5. However, this is beyond the scope of this course.

It is possible to approximate the Wilcoxon signed-rank test to a normal distribution for large $n$, as shown in Key point 11.4.

<div style="text-align: center;"><img src="imgs/img_in_image_box_99_998_142_1033.jpg" alt="Image" width="3%" /></div>


### KEY POINT 11.4

Given the statistic  $ T = \min(P, N) $, then:

 $$ \mathrm{E}(T)=\frac{n(n+1)}{4} $$ 

 $$  Var(T)=\frac{n(n+1)(2n+1)}{24} $$ 

And for large n:

 $$ T\sim\mathrm{N}\left(\frac{n(n+1)}{4},\frac{n(n+1)(2n+1)}{24}\right) $$ 

We use a continuity correction since we are approximating a discrete distribution with a continuous distribution. Our z-value is:

 $$ z=\frac{T-\mu+0.5}{\sigma} $$

<!-- page 269 -->

In a clinical trial, the survival times, in weeks, for 19 patients with non-Hodgkin's lymphoma are recorded.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>37</td><td style='text-align: center; word-wrap: break-word;'>54</td><td style='text-align: center; word-wrap: break-word;'>73</td><td style='text-align: center; word-wrap: break-word;'>89</td><td style='text-align: center; word-wrap: break-word;'>94</td><td style='text-align: center; word-wrap: break-word;'>110</td><td style='text-align: center; word-wrap: break-word;'>112</td><td style='text-align: center; word-wrap: break-word;'>123</td><td style='text-align: center; word-wrap: break-word;'>129</td><td style='text-align: center; word-wrap: break-word;'>132</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>148</td><td style='text-align: center; word-wrap: break-word;'>151</td><td style='text-align: center; word-wrap: break-word;'>173</td><td style='text-align: center; word-wrap: break-word;'>189</td><td style='text-align: center; word-wrap: break-word;'>201</td><td style='text-align: center; word-wrap: break-word;'>204</td><td style='text-align: center; word-wrap: break-word;'>213</td><td style='text-align: center; word-wrap: break-word;'>276</td><td style='text-align: center; word-wrap: break-word;'>281</td><td style='text-align: center; word-wrap: break-word;'></td></tr></table>

Test, at the 5% significance level, whether the median differs from 150.

## Answer

H $ _{0} $: The population median is 150.

<div style="text-align: center;">H $ _{1} $: The population median is different from 150.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>$ W_{i} $</td><td style='text-align: center; word-wrap: break-word;'>$ W_{i} - \text{Med} $</td><td style='text-align: center; word-wrap: break-word;'>$ |W_{i} - \text{Med}| $</td><td style='text-align: center; word-wrap: break-word;'>P</td><td style='text-align: center; word-wrap: break-word;'>N</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>37</td><td style='text-align: center; word-wrap: break-word;'>-113</td><td style='text-align: center; word-wrap: break-word;'>113</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>17</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>54</td><td style='text-align: center; word-wrap: break-word;'>-96</td><td style='text-align: center; word-wrap: break-word;'>96</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>16</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>73</td><td style='text-align: center; word-wrap: break-word;'>-77</td><td style='text-align: center; word-wrap: break-word;'>77</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>15</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>89</td><td style='text-align: center; word-wrap: break-word;'>-61</td><td style='text-align: center; word-wrap: break-word;'>61</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>13</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>94</td><td style='text-align: center; word-wrap: break-word;'>-56</td><td style='text-align: center; word-wrap: break-word;'>56</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>12</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>110</td><td style='text-align: center; word-wrap: break-word;'>-40</td><td style='text-align: center; word-wrap: break-word;'>40</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>9</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>112</td><td style='text-align: center; word-wrap: break-word;'>-38</td><td style='text-align: center; word-wrap: break-word;'>38</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>7</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>123</td><td style='text-align: center; word-wrap: break-word;'>-27</td><td style='text-align: center; word-wrap: break-word;'>27</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>129</td><td style='text-align: center; word-wrap: break-word;'>-21</td><td style='text-align: center; word-wrap: break-word;'>21</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>132</td><td style='text-align: center; word-wrap: break-word;'>-18</td><td style='text-align: center; word-wrap: break-word;'>18</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>148</td><td style='text-align: center; word-wrap: break-word;'>-2</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>151</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>173</td><td style='text-align: center; word-wrap: break-word;'>23</td><td style='text-align: center; word-wrap: break-word;'>23</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>189</td><td style='text-align: center; word-wrap: break-word;'>39</td><td style='text-align: center; word-wrap: break-word;'>39</td><td style='text-align: center; word-wrap: break-word;'>8</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>201</td><td style='text-align: center; word-wrap: break-word;'>51</td><td style='text-align: center; word-wrap: break-word;'>51</td><td style='text-align: center; word-wrap: break-word;'>10</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>204</td><td style='text-align: center; word-wrap: break-word;'>54</td><td style='text-align: center; word-wrap: break-word;'>54</td><td style='text-align: center; word-wrap: break-word;'>11</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>213</td><td style='text-align: center; word-wrap: break-word;'>63</td><td style='text-align: center; word-wrap: break-word;'>63</td><td style='text-align: center; word-wrap: break-word;'>14</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>276</td><td style='text-align: center; word-wrap: break-word;'>126</td><td style='text-align: center; word-wrap: break-word;'>126</td><td style='text-align: center; word-wrap: break-word;'>18</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>281</td><td style='text-align: center; word-wrap: break-word;'>131</td><td style='text-align: center; word-wrap: break-word;'>131</td><td style='text-align: center; word-wrap: break-word;'>19</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>Sum</td><td style='text-align: center; word-wrap: break-word;'>86</td><td style='text-align: center; word-wrap: break-word;'>104</td></tr></table>

 $$ T=\min(P,N)=86 $$ 

State the hypotheses.

 $$ \mathrm{E}(T)=\frac{n(n+1)}{4}=\frac{19\times20}{4}=95 $$ 

 $$  Var(T)=\frac{n(n+1)(2n+1)}{24}=\frac{19\times20\times39}{24}=617.5 $$ 

Set up the table of ranks for the data.

Ignoring signs, start with the smallest difference and give this rank 1, the next smallest difference is given rank 2 and so on.

We can check

 $$ P+N=86+104=190=\frac{19(19+1)}{2}=\frac{n(n+1)}{2} $$ 

Calculate $\mathrm{E}(T)$ and $\mathrm{Var}(T)$ so we can approximate to the normal.

<!-- page 270 -->

<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>$ z = \frac{86.5 - 95}{\sqrt{617.5}} $\n= -0.342</td><td style='text-align: center; word-wrap: break-word;'>Use this statistic from  $ T \sim \mathrm{N}(95, 617.5) $ and standardise it using  $ z = \frac{T - \mu + 0.5}{\sigma} $.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ \mathrm{P}(Z \leqslant -0.342) = 0.3662 $</td><td rowspan="2">Since this is negative, but two-tailed, we consider only the bottom tail.\nSince this is greater than 2.5%, it is not in the critical region.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Since 0.3662 &gt; 0.025, we do not reject  $ \mathrm{H}_{0} $.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>We could instead have compared -0.342 with the critical value for the two-tailed test, -1.96.</td><td rowspan="2">Since -0.342 &gt; -1.96, we do not reject  $ \mathrm{H}_{0} $.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>There is insufficient evidence to suggest that the population median differs from 150.</td></tr></table>

When using tied ranks (which is beyond this course) the calculation for the variance overestimates the variance. To compensate, we count the number of ranks that are tied, $t$, and reduce the variance by $\frac{t^{3}-t}{48}$. So:

 $$  Var(T)=\frac{n(n+1)(2n+1)}{24}-\frac{t^{3}-t}{48} $$ 

## EXERCISE 11B

1 Assuming that a Wilcoxon signed-rank test is appropriate for the data, calculate $T$ (the test statistic) based on the null hypotheses stated.

 $$ \begin{array}{l} 67 \quad 81 \quad 94\\71 \quad 88 \quad 97\\72 \quad 90 \quad 102\\75 \quad 91 \quad 104\\77 \quad 92 \quad 105 \end{array} $$ 

a  $ H_{0} $: population median is 85.

b  $ H_{0} $: population median is 100.

c  $ H_{0} $: population median is 70.

2 For each sample size and significance level given, state the critical value for a Wilcoxon signed-rank test.

a $n=8,5\%$ significance, one-tailed

b $n=15,1\%$ significance, one-tailed

c n = 18, 2% significance, two-tailed

d $n=9,10\%$ significance, two-tailed

<!-- page 271 -->

3 State the assumptions required for the use of the Wilcoxon signed-rank test.

4 For each of the following tests, find:

• E(T) and Var(T)

- the test statistic when approximating to the normal distribution.

Also state whether you would reject or not reject the null hypothesis.

a  $ H_{0} $: the population median is 142.1.

H $ _{1} $: the population median is less than 142.1.

5% significance level

T=175, n=30

b  $ H_{0} $: the population median is 40.6.

H $ _{1} $: the population median is not 40.6.

10% significance level

T=59, n=20

c  $ H_{0} $: the population median is 16.3.

H $ _{1} $: the population median is greater than 16.3.

2.5% significance level

T=260, n=40

5 A psychology student carries out a test on short-term memory. She shows 20 commonly used words to ten 18-year-old males. As soon as the 20 words have been shown, the psychologist asks the participants to write down as many words as they can remember in five minutes. The sample of 18-year-old males can be seen as representative of the population of 18-year-old males.

The number of words correctly remembered by the participants are:

## 15 , 7, 12, 14, 11, 10, 4, 13, 9, 2

The median number of words remembered by 65-year-old males in this test is four. Carry out a Wilcoxon signed-rank test, at the 5% level of significance, to investigate whether the median number of words remembered by the 18-year-old males is greater than that for the 65-year-old males.

6 Trials are carried out on a new tablet to help ease joint pain for people with chronic arthritis. A randomly selected sample of eight patients who have been suffering from arthritis are given the new tablets. Each participant measures the time it takes for the pain to stop after taking a new tablet as soon as they wake in the morning. The times, in minutes, are:

## 34 ,44,25,30,8,27,41,31

The average waiting time for the old type of tablet is 43 minutes after awakening.

a Carry out a Wilcoxon signed-rank test, at the 5% significance level, to investigate whether the new tablets offer faster pain relief.

b Give a reason why the Wilcoxon signed-rank test might be preferred to a sign test.

7 The student council of a large school believes that the average time that the A Level students spend on individual study has increased because students are more aware of the need to achieve high grades. In 2018, the average time per week of the school term that students spent on individual study was 11.2 hours.

<!-- page 272 -->

A random sample of ten students are asked to record the amount of time on individual study for three weeks during October 2016. The average times, in hours, per week are then calculated:

12, 13.2, 14.1, 10.8, 9.6, 11.3, 17.6, 14.3, 12.1, 19.2

Test, at the 5% level of significance, whether the average amount of time spent on individual study has increased from 2015.

Managers at a busy international airport are studying the times taken by arriving passengers to pass immigration, collect their luggage, then pass through customs. It is known that in the past this was 50 minutes. Some changes have been made to the queuing system in the hope of reducing this time. A random sample of 45 arriving passengers is taken and the rank sums calculated as $P = 55$, $N = 410$. Using a suitable approximation, test, with a 1% significance level, whether the median waiting time has reduced.

### 11.4 Paired-sample sign test

We can extend the idea of the sign test to work with paired-sample data by looking for a positive or negative difference. Nevertheless, the principles behind the sign test remain the same.

### WORKED EXAMPLE 11.4

Data are collected on the time, in seconds, it takes nine children to tie up their left shoelace and their right shoelace.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Child</td><td style='text-align: center; word-wrap: break-word;'>Left (s)</td><td style='text-align: center; word-wrap: break-word;'>Right (s)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>42</td><td style='text-align: center; word-wrap: break-word;'>45</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>B</td><td style='text-align: center; word-wrap: break-word;'>38</td><td style='text-align: center; word-wrap: break-word;'>36</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>C</td><td style='text-align: center; word-wrap: break-word;'>51</td><td style='text-align: center; word-wrap: break-word;'>52</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>D</td><td style='text-align: center; word-wrap: break-word;'>42</td><td style='text-align: center; word-wrap: break-word;'>39</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>E</td><td style='text-align: center; word-wrap: break-word;'>31</td><td style='text-align: center; word-wrap: break-word;'>35</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>F</td><td style='text-align: center; word-wrap: break-word;'>48</td><td style='text-align: center; word-wrap: break-word;'>49</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>G</td><td style='text-align: center; word-wrap: break-word;'>61</td><td style='text-align: center; word-wrap: break-word;'>62</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>H</td><td style='text-align: center; word-wrap: break-word;'>38</td><td style='text-align: center; word-wrap: break-word;'>39</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>I</td><td style='text-align: center; word-wrap: break-word;'>44</td><td style='text-align: center; word-wrap: break-word;'>45</td></tr></table>

Test, at the 10% level of significance, whether there is a difference in the time it takes for the children to tie each shoelace.

## Answer

 $ H_{0} $: There is no difference in the time taken to tie their left and right shoelaces.

H_{1}: There is a difference in the time taken to tie their left and right shoelaces.

<!-- page 273 -->

<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Child</td><td style='text-align: center; word-wrap: break-word;'>Left (s)</td><td style='text-align: center; word-wrap: break-word;'>Right (s)</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>42</td><td style='text-align: center; word-wrap: break-word;'>45</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>B</td><td style='text-align: center; word-wrap: break-word;'>38</td><td style='text-align: center; word-wrap: break-word;'>36</td><td style='text-align: center; word-wrap: break-word;'>+</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>C</td><td style='text-align: center; word-wrap: break-word;'>51</td><td style='text-align: center; word-wrap: break-word;'>52</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>D</td><td style='text-align: center; word-wrap: break-word;'>42</td><td style='text-align: center; word-wrap: break-word;'>39</td><td style='text-align: center; word-wrap: break-word;'>+</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>E</td><td style='text-align: center; word-wrap: break-word;'>31</td><td style='text-align: center; word-wrap: break-word;'>35</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>F</td><td style='text-align: center; word-wrap: break-word;'>48</td><td style='text-align: center; word-wrap: break-word;'>49</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>G</td><td style='text-align: center; word-wrap: break-word;'>61</td><td style='text-align: center; word-wrap: break-word;'>62</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>H</td><td style='text-align: center; word-wrap: break-word;'>38</td><td style='text-align: center; word-wrap: break-word;'>39</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>I</td><td style='text-align: center; word-wrap: break-word;'>44</td><td style='text-align: center; word-wrap: break-word;'>45</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr></table>

Set  $ L_{i} - R_{i} $ as the difference.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>The test statistic is 2.</td><td style='text-align: center; word-wrap: break-word;'>Let the number of + signs be the test statistic.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ P(X \le 2) = {}^{9}C_{0}(0.5)^{9} + {}^{9}C_{1}(0.5)^{9} + {}^{9}C_{2}(0.5)^{9} $</td><td style='text-align: center; word-wrap: break-word;'>Use:  $ X \sim \text{Bin}(9, 0.5) $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ P(X \le 2) = 0.089844 $</td><td style='text-align: center; word-wrap: break-word;'>The test is two-tailed, but we need to consider only the lower tail.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Since 0.089844 &gt; 0.05, the test statistic of 2 is not in the critical region. Therefore, there is insufficient evidence to reject  $ H_{0} $. There is insufficient evidence to say there is a difference in the times taken for children to tie their left and right shoelaces.</td><td style='text-align: center; word-wrap: break-word;'>The probability will be 5%, as the test is two-tailed.</td></tr></table>

## EXERCISE 11C

1 For the following paired datasets, a paired sign test will be performed. Calculate  $ S^{+} $.

a


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>11</td><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'>10</td><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'>13</td><td style='text-align: center; word-wrap: break-word;'>6</td><td style='text-align: center; word-wrap: break-word;'>6</td><td style='text-align: center; word-wrap: break-word;'>9</td><td style='text-align: center; word-wrap: break-word;'>11</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>12</td><td style='text-align: center; word-wrap: break-word;'>13</td><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'>8</td><td style='text-align: center; word-wrap: break-word;'>8</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>6</td><td style='text-align: center; word-wrap: break-word;'>8</td><td style='text-align: center; word-wrap: break-word;'>12</td></tr></table>

b


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>16</td><td style='text-align: center; word-wrap: break-word;'>22</td><td style='text-align: center; word-wrap: break-word;'>12</td><td style='text-align: center; word-wrap: break-word;'>23</td><td style='text-align: center; word-wrap: break-word;'>19</td><td style='text-align: center; word-wrap: break-word;'>15</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>17</td><td style='text-align: center; word-wrap: break-word;'>22</td><td style='text-align: center; word-wrap: break-word;'>14</td><td style='text-align: center; word-wrap: break-word;'>22</td><td style='text-align: center; word-wrap: break-word;'>18</td><td style='text-align: center; word-wrap: break-word;'>17</td></tr></table>


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>163</td><td style='text-align: center; word-wrap: break-word;'>162</td><td style='text-align: center; word-wrap: break-word;'>166</td><td style='text-align: center; word-wrap: break-word;'>157</td><td style='text-align: center; word-wrap: break-word;'>158</td><td style='text-align: center; word-wrap: break-word;'>153</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>160</td><td style='text-align: center; word-wrap: break-word;'>162</td><td style='text-align: center; word-wrap: break-word;'>163</td><td style='text-align: center; word-wrap: break-word;'>158</td><td style='text-align: center; word-wrap: break-word;'>167</td><td style='text-align: center; word-wrap: break-word;'>156</td></tr></table>

<!-- page 274 -->

2 a For the following dataset, state the value of n to be used in the paired sign test. Give a reason for your answer.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>160</td><td style='text-align: center; word-wrap: break-word;'>158</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>B</td><td style='text-align: center; word-wrap: break-word;'>159</td><td style='text-align: center; word-wrap: break-word;'>159</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>C</td><td style='text-align: center; word-wrap: break-word;'>167</td><td style='text-align: center; word-wrap: break-word;'>158</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>D</td><td style='text-align: center; word-wrap: break-word;'>166</td><td style='text-align: center; word-wrap: break-word;'>163</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>E</td><td style='text-align: center; word-wrap: break-word;'>162</td><td style='text-align: center; word-wrap: break-word;'>163</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>F</td><td style='text-align: center; word-wrap: break-word;'>163</td><td style='text-align: center; word-wrap: break-word;'>166</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>G</td><td style='text-align: center; word-wrap: break-word;'>166</td><td style='text-align: center; word-wrap: break-word;'>165</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>H</td><td style='text-align: center; word-wrap: break-word;'>159</td><td style='text-align: center; word-wrap: break-word;'>164</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>I</td><td style='text-align: center; word-wrap: break-word;'>166</td><td style='text-align: center; word-wrap: break-word;'>166</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>J</td><td style='text-align: center; word-wrap: break-word;'>166</td><td style='text-align: center; word-wrap: break-word;'>164</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>K</td><td style='text-align: center; word-wrap: break-word;'>161</td><td style='text-align: center; word-wrap: break-word;'>161</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>L</td><td style='text-align: center; word-wrap: break-word;'>159</td><td style='text-align: center; word-wrap: break-word;'>162</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>M</td><td style='text-align: center; word-wrap: break-word;'>158</td><td style='text-align: center; word-wrap: break-word;'>157</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>N</td><td style='text-align: center; word-wrap: break-word;'>161</td><td style='text-align: center; word-wrap: break-word;'>166</td></tr></table>

b Find the value of  $ S^{+} $ for the dataset in part a.

3 In each case, state whether you would reject or not reject  $ H_{0} $ at the stated significance level.

H $ _{0} $: the population medians are equal.

 $ H_{1} $: the population medians are not equal.

a n = 9,  $ S^{+} = 3 $, 10% significance level

b n = 6,  $ S^{+} = 1 $, 5% significance level

c n = 8,  $ S^{+} = 1 $, 10% significance level

4 For the dataset in question 2a:

a state whether a normal approximation would be appropriate, giving a reason for your answer

b find  $ E(S^{+}) $ and  $ \mathrm{Var}(S^{+}) $

c by assuming that a normal approximation would be appropriate, find the test statistic that would be used in performing a hypothesis test.

5 A new drug to help ease bronchitis, a lung infection, is developed and needs to be inhaled using an aerosol. Two types of aerosol (X and Y) have been developed and the company wishes to test whether there is a difference in the average effectiveness of the aerosols. Ten patients participate in the trial, in which the patient breathes in before using the aerosol and afterwards. The percentage increase in air intake is measured and recorded.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>B</td><td style='text-align: center; word-wrap: break-word;'>C</td><td style='text-align: center; word-wrap: break-word;'>D</td><td style='text-align: center; word-wrap: break-word;'>E</td><td style='text-align: center; word-wrap: break-word;'>F</td><td style='text-align: center; word-wrap: break-word;'>G</td><td style='text-align: center; word-wrap: break-word;'>H</td><td style='text-align: center; word-wrap: break-word;'>I</td><td style='text-align: center; word-wrap: break-word;'>J</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>X</td><td style='text-align: center; word-wrap: break-word;'>27</td><td style='text-align: center; word-wrap: break-word;'>22</td><td style='text-align: center; word-wrap: break-word;'>11</td><td style='text-align: center; word-wrap: break-word;'>41</td><td style='text-align: center; word-wrap: break-word;'>19</td><td style='text-align: center; word-wrap: break-word;'>57</td><td style='text-align: center; word-wrap: break-word;'>48</td><td style='text-align: center; word-wrap: break-word;'>41</td><td style='text-align: center; word-wrap: break-word;'>35</td><td style='text-align: center; word-wrap: break-word;'>37</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Y</td><td style='text-align: center; word-wrap: break-word;'>23</td><td style='text-align: center; word-wrap: break-word;'>18</td><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'>18</td><td style='text-align: center; word-wrap: break-word;'>24</td><td style='text-align: center; word-wrap: break-word;'>63</td><td style='text-align: center; word-wrap: break-word;'>31</td><td style='text-align: center; word-wrap: break-word;'>23</td><td style='text-align: center; word-wrap: break-word;'>21</td><td style='text-align: center; word-wrap: break-word;'>28</td></tr></table>

Test, at the 5% significance level, whether or not there is any difference in the average effectiveness of the aerosols.

6 An eye hospital treats a large number of patients who have one eye normal, and the other eye suffers from a thinning of the cornea. Seven such patients are randomly selected and the thickness of their cornea on their good eye and poor eye is measured, in micrometres.

<!-- page 275 -->

<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>B</td><td style='text-align: center; word-wrap: break-word;'>C</td><td style='text-align: center; word-wrap: break-word;'>D</td><td style='text-align: center; word-wrap: break-word;'>E</td><td style='text-align: center; word-wrap: break-word;'>F</td><td style='text-align: center; word-wrap: break-word;'>G</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Good eye</td><td style='text-align: center; word-wrap: break-word;'>512</td><td style='text-align: center; word-wrap: break-word;'>502</td><td style='text-align: center; word-wrap: break-word;'>516</td><td style='text-align: center; word-wrap: break-word;'>484</td><td style='text-align: center; word-wrap: break-word;'>476</td><td style='text-align: center; word-wrap: break-word;'>390</td><td style='text-align: center; word-wrap: break-word;'>498</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Poor eye</td><td style='text-align: center; word-wrap: break-word;'>503</td><td style='text-align: center; word-wrap: break-word;'>505</td><td style='text-align: center; word-wrap: break-word;'>493</td><td style='text-align: center; word-wrap: break-word;'>480</td><td style='text-align: center; word-wrap: break-word;'>477</td><td style='text-align: center; word-wrap: break-word;'>355</td><td style='text-align: center; word-wrap: break-word;'>491</td></tr></table>

Using a sign test, at the 10% significance level, investigate whether there is any difference in the thickness of the cornea between the two eyes.

7 At a research centre, a trial is conducted to see if a new fertiliser gives a better yield of potatoes than the usual fertiliser. Ten plots of land are available for the trial. Each plot is split into two equal halves: one half is treated with the new fertiliser, the other half with the usual fertiliser. The following table gives the yield, in kg, per half plot.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td colspan="11">Plot</td></tr><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>6</td><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'>8</td><td style='text-align: center; word-wrap: break-word;'>9</td><td style='text-align: center; word-wrap: break-word;'>10</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Usual</td><td style='text-align: center; word-wrap: break-word;'>20.2</td><td style='text-align: center; word-wrap: break-word;'>22.0</td><td style='text-align: center; word-wrap: break-word;'>17.8</td><td style='text-align: center; word-wrap: break-word;'>20.6</td><td style='text-align: center; word-wrap: break-word;'>26.8</td><td style='text-align: center; word-wrap: break-word;'>20.9</td><td style='text-align: center; word-wrap: break-word;'>21.2</td><td style='text-align: center; word-wrap: break-word;'>16.5</td><td style='text-align: center; word-wrap: break-word;'>20.8</td><td style='text-align: center; word-wrap: break-word;'>12.9</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>New</td><td style='text-align: center; word-wrap: break-word;'>20.8</td><td style='text-align: center; word-wrap: break-word;'>24.3</td><td style='text-align: center; word-wrap: break-word;'>17.0</td><td style='text-align: center; word-wrap: break-word;'>21.2</td><td style='text-align: center; word-wrap: break-word;'>27.7</td><td style='text-align: center; word-wrap: break-word;'>19.4</td><td style='text-align: center; word-wrap: break-word;'>22.6</td><td style='text-align: center; word-wrap: break-word;'>17.3</td><td style='text-align: center; word-wrap: break-word;'>20.9</td><td style='text-align: center; word-wrap: break-word;'>13.1</td></tr></table>

Using a sign test, at the 5% significance level, investigate whether the new fertiliser produces an increased average yield.

### 11.5 Wilcoxon matched-pairs signed-rank test

The Wilcoxon matched-pairs signed-rank test is used when we have matched pairs of data, as for the sign test, but when we can assume that the differences in the pairs of the data are symmetric, as shown in Key point 11.5. The process is the same as for the single-sample Wilcoxon signed-rank test. Worked example 11.5 demonstrates how to use the Wilcoxon matched-pairs signed-rank test.

<div style="text-align: center;"><img src="imgs/img_in_image_box_21_933_62_970.jpg" alt="Image" width="3%" /></div>


### KEY POINT 11.5

When we have matched pairs of data of unknown distributions, but the differences between them are thought to be symmetric, it is appropriate to use a Wilcoxon matched-pairs signed-rank test. We test to see whether the paired-difference median is 0.

### WORKED EXAMPLE 11.5

An investigation is carried out into the effectiveness of two types of post-operative pain relief drug: Drug 1 and Drug 2. Seven adults agree to take Drug 1 on one day, and Drug 2 on the second. The time, in hours, of pain relief is recorded.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>Drug 1</td><td style='text-align: center; word-wrap: break-word;'>Drug 2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>4.1</td><td style='text-align: center; word-wrap: break-word;'>3.9</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>B</td><td style='text-align: center; word-wrap: break-word;'>3.2</td><td style='text-align: center; word-wrap: break-word;'>3.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>C</td><td style='text-align: center; word-wrap: break-word;'>5.3</td><td style='text-align: center; word-wrap: break-word;'>5.0</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>D</td><td style='text-align: center; word-wrap: break-word;'>5.1</td><td style='text-align: center; word-wrap: break-word;'>4.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>E</td><td style='text-align: center; word-wrap: break-word;'>4.2</td><td style='text-align: center; word-wrap: break-word;'>4.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>F</td><td style='text-align: center; word-wrap: break-word;'>3.8</td><td style='text-align: center; word-wrap: break-word;'>3.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>G</td><td style='text-align: center; word-wrap: break-word;'>3.6</td><td style='text-align: center; word-wrap: break-word;'>4.3</td></tr></table>

<!-- page 276 -->

Test, using the matched-pairs Wilcoxon signed-rank test, at the 5% significance level, whether Drug 2 gives longer pain relief than Drug 1.

## Answer


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Before</td><td style='text-align: center; word-wrap: break-word;'>After</td><td style='text-align: center; word-wrap: break-word;'>Difference</td><td style='text-align: center; word-wrap: break-word;'>P</td><td style='text-align: center; word-wrap: break-word;'>N</td><td style='text-align: center; word-wrap: break-word;'>Define the hypotheses. This is a one-tailed test.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>4.1</td><td style='text-align: center; word-wrap: break-word;'>3.9</td><td style='text-align: center; word-wrap: break-word;'>0.2</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'></td><td rowspan="8">First calculate the test statistic. Calculate differences and rank them, keeping track of positive and negative differences.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>3.2</td><td style='text-align: center; word-wrap: break-word;'>3.3</td><td style='text-align: center; word-wrap: break-word;'>-0.1</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>5.3</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>0.3</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>5.1</td><td style='text-align: center; word-wrap: break-word;'>4.6</td><td style='text-align: center; word-wrap: break-word;'>0.5</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>4.2</td><td style='text-align: center; word-wrap: break-word;'>4.6</td><td style='text-align: center; word-wrap: break-word;'>-0.4</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>3.8</td><td style='text-align: center; word-wrap: break-word;'>3.2</td><td style='text-align: center; word-wrap: break-word;'>0.6</td><td style='text-align: center; word-wrap: break-word;'>6</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>3.6</td><td style='text-align: center; word-wrap: break-word;'>4.3</td><td style='text-align: center; word-wrap: break-word;'>-0.7</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>7</td></tr><tr><td colspan="2">Sum</td><td style='text-align: center; word-wrap: break-word;'>16</td><td style='text-align: center; word-wrap: break-word;'>12</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td colspan="5">T =  $ \min(P, N) = 12 $ And so the test statistic = 12. Find the critical value in the statistical tables:</td><td style='text-align: center; word-wrap: break-word;'>We are carrying out a 5% one-tailed test.</td></tr><tr><td colspan="6">Level of significance</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>One-tailed</td><td style='text-align: center; word-wrap: break-word;'>0.05</td><td style='text-align: center; word-wrap: break-word;'>0.025</td><td style='text-align: center; word-wrap: break-word;'>0.01</td><td colspan="2">0.005</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Two-tailed</td><td style='text-align: center; word-wrap: break-word;'>0.1</td><td style='text-align: center; word-wrap: break-word;'>0.05</td><td style='text-align: center; word-wrap: break-word;'>0.02</td><td colspan="2">0.01</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>n = 6</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'></td><td colspan="2"></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>0</td><td colspan="2"></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>8</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>1</td><td colspan="2">0</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>9</td><td style='text-align: center; word-wrap: break-word;'>8</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>3</td><td colspan="2">1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>10</td><td style='text-align: center; word-wrap: break-word;'>10</td><td style='text-align: center; word-wrap: break-word;'>8</td><td style='text-align: center; word-wrap: break-word;'>5</td><td colspan="2">3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>11</td><td style='text-align: center; word-wrap: break-word;'>13</td><td style='text-align: center; word-wrap: break-word;'>10</td><td style='text-align: center; word-wrap: break-word;'>7</td><td colspan="2">5</td></tr><tr><td colspan="6">Since 12 &gt; 3 (test statistic &gt; critical value), there is insufficient evidence to reject  $ H_{0} $. There is insufficient evidence to suggest that Drug 2 gives longer pain relief.</td></tr></table>

<!-- page 277 -->

1 For the following pairs of data, calculate the value of  $ T = \min(P, N) $.

a


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>B</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>6.2</td><td style='text-align: center; word-wrap: break-word;'>6.7</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>7.6</td><td style='text-align: center; word-wrap: break-word;'>7.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>5.7</td><td style='text-align: center; word-wrap: break-word;'>5.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>6.2</td><td style='text-align: center; word-wrap: break-word;'>6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>8.4</td><td style='text-align: center; word-wrap: break-word;'>7.8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>7.2</td><td style='text-align: center; word-wrap: break-word;'>7.3</td></tr></table>

<div style="text-align: center;">b</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>B</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>15.4</td><td style='text-align: center; word-wrap: break-word;'>13.8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>13.1</td><td style='text-align: center; word-wrap: break-word;'>13.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>14</td><td style='text-align: center; word-wrap: break-word;'>14.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>13.8</td><td style='text-align: center; word-wrap: break-word;'>14.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>15.4</td><td style='text-align: center; word-wrap: break-word;'>15</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>14</td><td style='text-align: center; word-wrap: break-word;'>14.7</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>15.2</td><td style='text-align: center; word-wrap: break-word;'>15</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>15.4</td><td style='text-align: center; word-wrap: break-word;'>14.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>15.1</td><td style='text-align: center; word-wrap: break-word;'>13.6</td></tr></table>

<div style="text-align: center;">C</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>B</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>12.1</td><td style='text-align: center; word-wrap: break-word;'>13</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>13.6</td><td style='text-align: center; word-wrap: break-word;'>13</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>14.2</td><td style='text-align: center; word-wrap: break-word;'>13.5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>15.3</td><td style='text-align: center; word-wrap: break-word;'>14.5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>14.7</td><td style='text-align: center; word-wrap: break-word;'>14.5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>14.9</td><td style='text-align: center; word-wrap: break-word;'>13</td></tr></table>

2 For the hypotheses, sample size and test statistic given, state whether you would reject or not reject the null hypothesis.

a  $ H_{0} $: the population medians are equal.

 $ H_{1} $: the population medians are not equal.

n = 8, T = 4, significance level 5%

b  $ H_{0} $: the scores are the same.

H $ _{1} $: the scores have decreased.

n = 14, T = 20, significance level 5%

c  $ H_{0} $: the weights are the same.

H $ _{1} $: the weights have increased.

n = 9, T = 6, significance level 2%

3 For a sample size of n = 18, a Wilcoxon signed-rank test is to be carried out. Where  $ T = \min(P, N) $:

a Find E(T).

b Find Var(T).

Given that the value of T is 59 and that a normal approximation is appropriate, calculate the test statistic to be used.

d For the given hypotheses, state whether at 5% you would reject or not reject the null hypothesis.

H $ _{0} $: the population medians are equal.

H $ _{1} $: the population medians are not equal.

4 Percentage marks are obtained for a random sample of eight A Level students for their AS & A Level examinations in Statistics and in Mechanics. The following table shows their results.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>Statistics</td><td style='text-align: center; word-wrap: break-word;'>Mechanics</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>53</td><td style='text-align: center; word-wrap: break-word;'>57</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>B</td><td style='text-align: center; word-wrap: break-word;'>64</td><td style='text-align: center; word-wrap: break-word;'>62</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>C</td><td style='text-align: center; word-wrap: break-word;'>72</td><td style='text-align: center; word-wrap: break-word;'>79</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>D</td><td style='text-align: center; word-wrap: break-word;'>61</td><td style='text-align: center; word-wrap: break-word;'>58</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>E</td><td style='text-align: center; word-wrap: break-word;'>72</td><td style='text-align: center; word-wrap: break-word;'>67</td></tr></table>

<!-- page 278 -->

<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>Statistics</td><td style='text-align: center; word-wrap: break-word;'>Mechanics</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>F</td><td style='text-align: center; word-wrap: break-word;'>58</td><td style='text-align: center; word-wrap: break-word;'>52</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>G</td><td style='text-align: center; word-wrap: break-word;'>59</td><td style='text-align: center; word-wrap: break-word;'>60</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>H</td><td style='text-align: center; word-wrap: break-word;'>71</td><td style='text-align: center; word-wrap: break-word;'>79</td></tr></table>

a Test, at the 10% significance level, whether there is a difference in the students' scores in Mechanics and Statistics.

b State any assumptions you have made.

5 The manufacturer of a brand of smartphone wishes to know what its customers think about the performance of the phone before and after introducing a new processor. The manufacturer selects, at random, ten customers. Each customer is given a phone without the new processor and a phone with the new processor. Each customer is then asked to rate ‘on a scale of 1–20’ the performance of each smartphone (20 being the best).


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>B</td><td style='text-align: center; word-wrap: break-word;'>C</td><td style='text-align: center; word-wrap: break-word;'>D</td><td style='text-align: center; word-wrap: break-word;'>E</td><td style='text-align: center; word-wrap: break-word;'>F</td><td style='text-align: center; word-wrap: break-word;'>G</td><td style='text-align: center; word-wrap: break-word;'>H</td><td style='text-align: center; word-wrap: break-word;'>I</td><td style='text-align: center; word-wrap: break-word;'>J</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Original processor</td><td style='text-align: center; word-wrap: break-word;'>15</td><td style='text-align: center; word-wrap: break-word;'>17</td><td style='text-align: center; word-wrap: break-word;'>13</td><td style='text-align: center; word-wrap: break-word;'>17</td><td style='text-align: center; word-wrap: break-word;'>14</td><td style='text-align: center; word-wrap: break-word;'>12</td><td style='text-align: center; word-wrap: break-word;'>13</td><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'>10</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>New processor</td><td style='text-align: center; word-wrap: break-word;'>12</td><td style='text-align: center; word-wrap: break-word;'>15</td><td style='text-align: center; word-wrap: break-word;'>18</td><td style='text-align: center; word-wrap: break-word;'>18</td><td style='text-align: center; word-wrap: break-word;'>10</td><td style='text-align: center; word-wrap: break-word;'>19</td><td style='text-align: center; word-wrap: break-word;'>19</td><td style='text-align: center; word-wrap: break-word;'>15</td><td style='text-align: center; word-wrap: break-word;'>17</td><td style='text-align: center; word-wrap: break-word;'>19</td></tr></table>

Test, at the 5% significance level, whether customers think that the phone with the new processor is better.

6 A particular type of tree can develop a virus that creates black spots on the leaves. The more spots, the more the virus has infected the tree. Two different virus treatments have been developed: treatment X and treatment Y. A sample of eight leaves is chosen. Each leaf is divided into two equal sections without removing it from the tree. On one half, treatment X is used and on the other, treatment Y. The number of black spots on each half is given in the table.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>B</td><td style='text-align: center; word-wrap: break-word;'>C</td><td style='text-align: center; word-wrap: break-word;'>D</td><td style='text-align: center; word-wrap: break-word;'>E</td><td style='text-align: center; word-wrap: break-word;'>F</td><td style='text-align: center; word-wrap: break-word;'>G</td><td style='text-align: center; word-wrap: break-word;'>H</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>X</td><td style='text-align: center; word-wrap: break-word;'>41</td><td style='text-align: center; word-wrap: break-word;'>37</td><td style='text-align: center; word-wrap: break-word;'>34</td><td style='text-align: center; word-wrap: break-word;'>12</td><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'>19</td><td style='text-align: center; word-wrap: break-word;'>23</td><td style='text-align: center; word-wrap: break-word;'>16</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Y</td><td style='text-align: center; word-wrap: break-word;'>24</td><td style='text-align: center; word-wrap: break-word;'>21</td><td style='text-align: center; word-wrap: break-word;'>30</td><td style='text-align: center; word-wrap: break-word;'>11</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>14</td><td style='text-align: center; word-wrap: break-word;'>20</td><td style='text-align: center; word-wrap: break-word;'>9</td></tr></table>

Test, at the 5% significance level, whether there is a difference between the two treatments.

M 7 It is believed that identical twins have similar IQ levels. Thirty pairs of identical twins participate in an IQ test and their results are recorded. There are no tied or zero ranks. The sum of positive ranks is 272, and the sum of negative ranks is 193.

a Find E(T).

b Find Var(T).

c Using a suitable approximation, test, at the 5% significance level, whether there is a difference between the IQ scores of a set of identical twins.

### 11.6 Wilcoxon rank-sum test

The Wilcoxon matched-pairs signed-rank test requires data to be paired, and groups of data must be of equal size. What if we have two independent groups of different sizes and we want to test for a difference in their medians? To do this, we perform the Wilcoxon rank-sum test to see whether the data are from the same distribution. This test is very similar in design to the independent t-test.

<!-- page 279 -->

To perform the Wilcoxon rank-sum test, we rank the data first, as if it were from one population. We then sum the ranks for each group separately. These sums are the test statistics.

The calculation of the Wilcoxon rank-sum test statistic is quite tricky. We have two samples, one of size $m$ and the other of size $n$, and we let $m \leq n$. Let $R_m$ be the sum of the ranks from the group of size $m$. We have not defined which way we should rank the data.

Let  $ R_m $ be the ranking given, then  $ m(n + m + 1) - R_m $ will create the rank sum of the smaller sample when ranked the opposite way round, explained as follows.

There are  $ n+m $ data points in total. If a data point is the  $ a $th value when ranked one way and the  $ b $th value when ranked the other, then the sum of these two ranks will be  $ n+m+1 $.

We have $m$ data points in the smaller sample, so the sum of all of these sums of ranks is $m(n+m+1)$. To find the rank sum when they are ranked the other way round, we use $m(n+m+1) - R_{m}$.

To avoid having to think too carefully about the ranking order, we define the test statistic as  $ W = \min(R_m, m(n + m + 1) - R_m) $, as shown in Key point 11.6.

We can find the critical values from the data tables given.

<div style="text-align: center;"><img src="imgs/img_in_image_box_25_650_68_686.jpg" alt="Image" width="3%" /></div>


### KEY POINT 11.6

If two samples have sizes $m$ and $n$, where $m \leq n$, $R_m$ is the sum of the ranks of the items in the sample of size $m$, the test statistic is:

 $$ W=\min\left(R_{m},m(n+m+1)-R_{m}\right) $$ 

### WORKED EXAMPLE 11.6

Researchers are investigating the effect of vitamin B12 on the size of the brain. A sample of males aged between 25 and 40 years is selected. Nine of them are known to have low B12 levels and seven are known to have high B12 levels. After a brain scan, the ratio of brain volume to skull capacity is recorded.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Low B12 levels</td><td style='text-align: center; word-wrap: break-word;'>0.795</td><td style='text-align: center; word-wrap: break-word;'>0.798</td><td style='text-align: center; word-wrap: break-word;'>0.802</td><td style='text-align: center; word-wrap: break-word;'>0.805</td><td style='text-align: center; word-wrap: break-word;'>0.806</td><td style='text-align: center; word-wrap: break-word;'>0.807</td><td style='text-align: center; word-wrap: break-word;'>0.808</td><td style='text-align: center; word-wrap: break-word;'>0.81</td><td style='text-align: center; word-wrap: break-word;'>0.812</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>High B12 levels</td><td style='text-align: center; word-wrap: break-word;'>0.786</td><td style='text-align: center; word-wrap: break-word;'>0.789</td><td style='text-align: center; word-wrap: break-word;'>0.792</td><td style='text-align: center; word-wrap: break-word;'>0.796</td><td style='text-align: center; word-wrap: break-word;'>0.799</td><td style='text-align: center; word-wrap: break-word;'>0.8</td><td style='text-align: center; word-wrap: break-word;'>0.803</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr></table>

Carry out a Wilcoxon rank-sum test, at the 5% significance level, to see whether the level of vitamin B12 affects the size of the brain.

## Answer

 $ H_{0} $: level of B12 has no effect on brain size.

H $ _{1} $: level of B12 has an effect on brain size.

We can also state  $ H_{0} $ as the samples are from the same population.

<!-- page 280 -->

<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td colspan="2"></td><td style='text-align: center; word-wrap: break-word;'>Low B12</td><td style='text-align: center; word-wrap: break-word;'>High B12</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.812</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.810</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.808</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.807</td><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.806</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.805</td><td style='text-align: center; word-wrap: break-word;'>6</td><td style='text-align: center; word-wrap: break-word;'>6</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.803</td><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>7</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.802</td><td style='text-align: center; word-wrap: break-word;'>8</td><td style='text-align: center; word-wrap: break-word;'>8</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.800</td><td style='text-align: center; word-wrap: break-word;'>9</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>9</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.799</td><td style='text-align: center; word-wrap: break-word;'>10</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>10</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.798</td><td style='text-align: center; word-wrap: break-word;'>11</td><td style='text-align: center; word-wrap: break-word;'>11</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.796</td><td style='text-align: center; word-wrap: break-word;'>12</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>12</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.795</td><td style='text-align: center; word-wrap: break-word;'>13</td><td style='text-align: center; word-wrap: break-word;'>13</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.792</td><td style='text-align: center; word-wrap: break-word;'>14</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>14</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.789</td><td style='text-align: center; word-wrap: break-word;'>15</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>15</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.786</td><td style='text-align: center; word-wrap: break-word;'>16</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>16</td></tr><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>Sum</td><td style='text-align: center; word-wrap: break-word;'>53</td><td style='text-align: center; word-wrap: break-word;'>83</td></tr></table>

 $ R_{m} = 83 $ since this is the rank sum from the smaller-sized sample.

 $$ m(n+m+1)-R_{m}=7(9+7+1)-83=36 $$ 

The test statistic is the minimum of 83 and 36, which is $W=36$.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td colspan="4">Level of significance</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>One-tailed</td><td style='text-align: center; word-wrap: break-word;'>0.05</td><td style='text-align: center; word-wrap: break-word;'>0.025</td><td style='text-align: center; word-wrap: break-word;'>0.01</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Two-tailed</td><td style='text-align: center; word-wrap: break-word;'>0.1</td><td style='text-align: center; word-wrap: break-word;'>0.05</td><td style='text-align: center; word-wrap: break-word;'>0.02</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>n</td><td colspan="3">$ m=7 $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'>39</td><td style='text-align: center; word-wrap: break-word;'>36</td><td style='text-align: center; word-wrap: break-word;'>34</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>8</td><td style='text-align: center; word-wrap: break-word;'>41</td><td style='text-align: center; word-wrap: break-word;'>38</td><td style='text-align: center; word-wrap: break-word;'>35</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>9</td><td style='text-align: center; word-wrap: break-word;'>43</td><td style='text-align: center; word-wrap: break-word;'>40</td><td style='text-align: center; word-wrap: break-word;'>37</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>10</td><td style='text-align: center; word-wrap: break-word;'>45</td><td style='text-align: center; word-wrap: break-word;'>42</td><td style='text-align: center; word-wrap: break-word;'>39</td></tr></table>

Since 36 < 40, there is sufficient evidence to reject  $ H_{0} $.

Use the value of sums of the group with the smaller sample size.

First, rank the whole dataset. Note which group each value comes from. Then add up the ranks for each category.

There is evidence to suggest that level of vitamin B12 affects brain size.

The following table shows what we would get if we ranked them the other way round.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td colspan="2"></td><td colspan="2">Low B12</td><td style='text-align: center; word-wrap: break-word;'>High B12</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.812</td><td style='text-align: center; word-wrap: break-word;'>16</td><td style='text-align: center; word-wrap: break-word;'>16</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.810</td><td style='text-align: center; word-wrap: break-word;'>15</td><td style='text-align: center; word-wrap: break-word;'>15</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.808</td><td style='text-align: center; word-wrap: break-word;'>14</td><td style='text-align: center; word-wrap: break-word;'>14</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.807</td><td style='text-align: center; word-wrap: break-word;'>13</td><td style='text-align: center; word-wrap: break-word;'>13</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.806</td><td style='text-align: center; word-wrap: break-word;'>12</td><td style='text-align: center; word-wrap: break-word;'>12</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.805</td><td style='text-align: center; word-wrap: break-word;'>11</td><td style='text-align: center; word-wrap: break-word;'>11</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.803</td><td style='text-align: center; word-wrap: break-word;'>10</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>10</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.802</td><td style='text-align: center; word-wrap: break-word;'>9</td><td style='text-align: center; word-wrap: break-word;'>9</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.800</td><td style='text-align: center; word-wrap: break-word;'>8</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.799</td><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>7</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.798</td><td style='text-align: center; word-wrap: break-word;'>6</td><td style='text-align: center; word-wrap: break-word;'>6</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.796</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.795</td><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.792</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.789</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.786</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>Sum</td><td colspan="2">100</td><td style='text-align: center; word-wrap: break-word;'>36</td></tr></table>

Calculate the test statistic.

Find the critical value.

<!-- page 281 -->

For large $n$ and $m$ ($n \geq 10$, $m \geq 10$) it is possible to approximate $W$ as a normal distribution, $W = \min (R_m, m(n + m + 1) - R_m)$ as shown in Key point 11.7.

<div style="text-align: center;"><img src="imgs/img_in_image_box_33_218_76_256.jpg" alt="Image" width="3%" /></div>


### KEY POINT 11.7

For large n and m (n ≥ 10, m ≥ 10) it is possible to approximate W as a normal distribution:

 $$ \mathrm{E}(W)=\frac{m(n+m+1)}{2} $$ 

 $$  Var(W)=\frac{mn(n+m+1)}{12} $$ 

We must also make sure that we use a continuity correction. Since we are approximating a discrete distribution with a continuous distribution, our $z$-value is $z=\frac{W-\mu+0.5}{\sigma}$.

<div style="text-align: center;"><img src="imgs/img_in_image_box_869_148_913_188.jpg" alt="Image" width="3%" /></div>


## DID YOU KNOW?

There is another test that is statistically equivalent to the Wilcoxon rank-sum test. This is the Mann–Whitney U-test. The only difference is the measure of the test statistic, and hence the table of critical values, but it is equivalent. You may come across Mann–Whitney U-test in the Social Sciences

### WORKED EXAMPLE 11.7

A company is investigating a new production technique to improve the quality of camera lenses for a phone. Samples of the lenses are given to a camera expert who is asked to rank the lenses, with rank 1 being the highest quality. The expert does not know which production technique has been used.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Lens</td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>B</td><td style='text-align: center; word-wrap: break-word;'>C</td><td style='text-align: center; word-wrap: break-word;'>D</td><td style='text-align: center; word-wrap: break-word;'>E</td><td style='text-align: center; word-wrap: break-word;'>F</td><td style='text-align: center; word-wrap: break-word;'>G</td><td style='text-align: center; word-wrap: break-word;'>H</td><td style='text-align: center; word-wrap: break-word;'>I</td><td style='text-align: center; word-wrap: break-word;'>J</td><td style='text-align: center; word-wrap: break-word;'>K</td><td style='text-align: center; word-wrap: break-word;'>L</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Method</td><td style='text-align: center; word-wrap: break-word;'>old</td><td style='text-align: center; word-wrap: break-word;'>new</td><td style='text-align: center; word-wrap: break-word;'>new</td><td style='text-align: center; word-wrap: break-word;'>old</td><td style='text-align: center; word-wrap: break-word;'>old</td><td style='text-align: center; word-wrap: break-word;'>new</td><td style='text-align: center; word-wrap: break-word;'>old</td><td style='text-align: center; word-wrap: break-word;'>new</td><td style='text-align: center; word-wrap: break-word;'>old</td><td style='text-align: center; word-wrap: break-word;'>old</td><td style='text-align: center; word-wrap: break-word;'>old</td><td style='text-align: center; word-wrap: break-word;'>new</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Rank</td><td style='text-align: center; word-wrap: break-word;'>12</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>9</td><td style='text-align: center; word-wrap: break-word;'>10</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>21</td><td style='text-align: center; word-wrap: break-word;'>6</td><td style='text-align: center; word-wrap: break-word;'>20</td><td style='text-align: center; word-wrap: break-word;'>22</td><td style='text-align: center; word-wrap: break-word;'>23</td><td style='text-align: center; word-wrap: break-word;'>17</td></tr></table>


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Lens</td><td style='text-align: center; word-wrap: break-word;'>M</td><td style='text-align: center; word-wrap: break-word;'>N</td><td style='text-align: center; word-wrap: break-word;'>O</td><td style='text-align: center; word-wrap: break-word;'>P</td><td style='text-align: center; word-wrap: break-word;'>Q</td><td style='text-align: center; word-wrap: break-word;'>R</td><td style='text-align: center; word-wrap: break-word;'>S</td><td style='text-align: center; word-wrap: break-word;'>T</td><td style='text-align: center; word-wrap: break-word;'>U</td><td style='text-align: center; word-wrap: break-word;'>V</td><td style='text-align: center; word-wrap: break-word;'>W</td><td style='text-align: center; word-wrap: break-word;'>X</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Method</td><td style='text-align: center; word-wrap: break-word;'>new</td><td style='text-align: center; word-wrap: break-word;'>new</td><td style='text-align: center; word-wrap: break-word;'>old</td><td style='text-align: center; word-wrap: break-word;'>old</td><td style='text-align: center; word-wrap: break-word;'>old</td><td style='text-align: center; word-wrap: break-word;'>new</td><td style='text-align: center; word-wrap: break-word;'>old</td><td style='text-align: center; word-wrap: break-word;'>new</td><td style='text-align: center; word-wrap: break-word;'>old</td><td style='text-align: center; word-wrap: break-word;'>new</td><td style='text-align: center; word-wrap: break-word;'>new</td><td style='text-align: center; word-wrap: break-word;'>old</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Rank</td><td style='text-align: center; word-wrap: break-word;'>14</td><td style='text-align: center; word-wrap: break-word;'>13</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>19</td><td style='text-align: center; word-wrap: break-word;'>11</td><td style='text-align: center; word-wrap: break-word;'>24</td><td style='text-align: center; word-wrap: break-word;'>16</td><td style='text-align: center; word-wrap: break-word;'>18</td><td style='text-align: center; word-wrap: break-word;'>8</td><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'>15</td></tr></table>

Using a suitable approximation as shown in Key point 11.7, test, at the 5% significance level, whether there is a difference in the quality of production techniques.

## Answer

 $ H_{0} $: There is no difference in the quality of the two samples.

 $ H_{1} $: There is a difference in the quality of the two samples.

Define the hypotheses.



m = 11 (new)

n = 13 (old)

Since we are approximating, we need to know only the sizes of the two samples and the rank sum.

 $$ \mathrm{E}(R_{m})=\frac{m(n+m+1)}{2}=\frac{11(25)}{2}=137.5 $$ 

 $$  Var(R_{m})=\frac{mn(n+m+1)}{12}=\frac{11\times13(25)}{12}=297\frac{11}{12} $$ 

Find  $ \mathrm{E}(X) $ and  $ \mathrm{Var}(X) $.

<!-- page 282 -->

<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>$ R_m = 1 + 2 + 5 + 6 + 17 + 14 + 13 + 11 + 16 + 8 + 7 $</td><td style='text-align: center; word-wrap: break-word;'>The test statistic is the minimum of  $ R_m $ and  $ m(n + m + 1) - R_m $.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ R_m = 100 $</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ m(n + m + 1) - R_m = 175 $</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>And so  $ W = \min(R_m, m(n + m + 1) - R_m) = 100 $.</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ z = \frac{100.5 - 137.5}{\sqrt{(297\frac{11}{12})}} = -2.144 $</td><td style='text-align: center; word-wrap: break-word;'>Find the z-test statistic, remembering to make the continuity correction.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ P(Z \leq -2.144) = 1 - 0.984 = 0.0160 $</td><td style='text-align: center; word-wrap: break-word;'>Since we have a two-tailed test, compare the probability with the critical value for 2.5%.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Since 0.0160 &lt; 0.025, the test statistic is in the critical region and so we have sufficient evidence to reject  $ H_0 $.</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>We could have compared -2.144 with the critical value for the two-tailed test, -1.96.</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Since -2.144 &lt; -1.96, the test statistic is in the critical region and so we have sufficient evidence to reject  $ H_0 $.</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>There is a difference in quality between samples of camera lenses made by different production techniques.</td><td style='text-align: center; word-wrap: break-word;'></td></tr></table>

### EXPLORE 11.1

We are given a table of critical values for all of the tests that we carry out. Sometimes it is not clear where these values come from. In this activity, we shall find some of the critical values of the Wilcoxon rank-sum test.

Let us consider the situation where we have sample sizes $m=4$ and $n=6$. Here we have ten ranks, four of which must be assigned to the sample of size four.

The first case is the rankings {1, 2, 3, 4}, with the rank sum of 10.

The second case is a rank sum of 11, created with the rankings {1, 2, 3, 5}.

1 Find the sets of ranks that give a rank sum of:

a 12

b 13

[three sets]

c 14 [five sets]

d 15 [six sets]

2 How many possible sets of four ranks are there from ten?

3 Copy and complete the following table.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>P(rank sum = 10)</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1}{210} $</td><td style='text-align: center; word-wrap: break-word;'>0.004762</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>P(rank sum ≤ 11)</td><td style='text-align: center; word-wrap: break-word;'>$ \frac{1+1}{210} $</td><td style='text-align: center; word-wrap: break-word;'>0.009524</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>P(rank sum ≤ 12)</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>P(rank sum ≤ 13)</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>P(rank sum ≤ 14)</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>P(rank sum ≤ 15)</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr></table>

<!-- page 283 -->

The critical value,  $ c $, of a 5% one-tailed test is the greatest value of  $ c $ that satisfies  $ \mathrm{P}(X \leq c) \leq 0.05 $.

From the work shown, we can see that this is c = 13.

And so we conclude that for m=4, n=6 the critical value for a one-tailed test at the 5% significance level is 13.

This is reflected in the critical value table.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">One-tailed</td><td colspan="6">Level of significance</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.05</td><td style='text-align: center; word-wrap: break-word;'>0.025</td><td style='text-align: center; word-wrap: break-word;'>0.01</td><td style='text-align: center; word-wrap: break-word;'>0.05</td><td style='text-align: center; word-wrap: break-word;'>0.025</td><td style='text-align: center; word-wrap: break-word;'>0.01</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Two-tailed</td><td style='text-align: center; word-wrap: break-word;'>0.1</td><td style='text-align: center; word-wrap: break-word;'>0.05</td><td style='text-align: center; word-wrap: break-word;'>0.02</td><td style='text-align: center; word-wrap: break-word;'>0.1</td><td style='text-align: center; word-wrap: break-word;'>0.05</td><td style='text-align: center; word-wrap: break-word;'>0.02</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>n</td><td colspan="3">m=3</td><td colspan="3">m=4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>6</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>6</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>11</td><td style='text-align: center; word-wrap: break-word;'>10</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'>6</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>12</td><td style='text-align: center; word-wrap: break-word;'>11</td><td style='text-align: center; word-wrap: break-word;'>10</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>6</td><td style='text-align: center; word-wrap: break-word;'>8</td><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>13</td><td style='text-align: center; word-wrap: break-word;'>12</td><td style='text-align: center; word-wrap: break-word;'>11</td></tr></table>

We can now also confirm that the critical values for tests at the 2.5% and 1% significance levels are correct.

### EXPLORE 11.2

Use the internet to research the Kruskal–Wallis test for non-parametric data. We can use the Kruskal–Wallis test to compare three or more samples.

## EXERCISE 11E

1 For each of the following datasets, calculate the values of:

i  $ R_{m} $

ii  $ m(n+m+1)-R_{m} $

iii W

<div style="text-align: center;">a</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>X</td><td style='text-align: center; word-wrap: break-word;'>Y</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>5.7</td><td style='text-align: center; word-wrap: break-word;'>4.8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>4.4</td><td style='text-align: center; word-wrap: break-word;'>3.9</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>4.9</td><td style='text-align: center; word-wrap: break-word;'>4.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>4.6</td><td style='text-align: center; word-wrap: break-word;'>4.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>5.2</td><td style='text-align: center; word-wrap: break-word;'>4.7</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>4.5</td><td style='text-align: center; word-wrap: break-word;'>4.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>5.3</td></tr></table>

<div style="text-align: center;">b</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>X</td><td style='text-align: center; word-wrap: break-word;'>Y</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>17.3</td><td style='text-align: center; word-wrap: break-word;'>19.8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>19.7</td><td style='text-align: center; word-wrap: break-word;'>18.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>19.4</td><td style='text-align: center; word-wrap: break-word;'>19.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>18.3</td><td style='text-align: center; word-wrap: break-word;'>18.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>18.7</td><td style='text-align: center; word-wrap: break-word;'>18.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>18.9</td><td style='text-align: center; word-wrap: break-word;'>18.0</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>19.1</td><td style='text-align: center; word-wrap: break-word;'>18.5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>17.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>17.8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>17.7</td></tr></table>

<div style="text-align: center;">C</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>x</td><td style='text-align: center; word-wrap: break-word;'>y</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>21.5</td><td style='text-align: center; word-wrap: break-word;'>22.0</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>21.6</td><td style='text-align: center; word-wrap: break-word;'>22.9</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>21.8</td><td style='text-align: center; word-wrap: break-word;'>22.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>22.4</td><td style='text-align: center; word-wrap: break-word;'>22.5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>23.0</td><td style='text-align: center; word-wrap: break-word;'>22.8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>22.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>23.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>22.7</td></tr></table>

<div style="text-align: center;">d</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>X</td><td style='text-align: center; word-wrap: break-word;'>Y</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>114.2</td><td style='text-align: center; word-wrap: break-word;'>115.8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>116.1</td><td style='text-align: center; word-wrap: break-word;'>115.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>115.4</td><td style='text-align: center; word-wrap: break-word;'>116.0</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>116.8</td><td style='text-align: center; word-wrap: break-word;'>117.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>116.2</td><td style='text-align: center; word-wrap: break-word;'>117.2</td></tr></table>

<!-- page 284 -->

2 For the corresponding dataset in question 1a–d, state the critical value for the following significance levels.

a Significance level 5% one-tailed b Significance level 10% two-tailed c Significance level 5% two-tailed d Significance level 1% one-tailed

3 For the following dataset sizes, find  $ \mathrm{E}(R_{m}) $ and  $ \mathrm{Var}(R_{m}) $.

a n = 12, m = 9

4 a For the following dataset sizes and W values, find the test statistic if a normal approximation is used.

n = 18, m = 12; W = 146

b These hypotheses are given:

H₀: Population medians are equal.

 $ H_{1} $: Population medians are not equal.

M 5 It is believed that the calorie content of a chicken sausage is different to that of a vegetarian sausage. The calorie contents of eight vegetarian sausages and seven chicken sausages are measured and tabulated.

Testing at 10%, state whether you would reject or not reject the null hypothesis.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Vegetarian</td><td style='text-align: center; word-wrap: break-word;'>186</td><td style='text-align: center; word-wrap: break-word;'>181</td><td style='text-align: center; word-wrap: break-word;'>176</td><td style='text-align: center; word-wrap: break-word;'>135</td><td style='text-align: center; word-wrap: break-word;'>184</td><td style='text-align: center; word-wrap: break-word;'>190</td><td style='text-align: center; word-wrap: break-word;'>111</td><td style='text-align: center; word-wrap: break-word;'>132</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Chicken</td><td style='text-align: center; word-wrap: break-word;'>129</td><td style='text-align: center; word-wrap: break-word;'>137</td><td style='text-align: center; word-wrap: break-word;'>102</td><td style='text-align: center; word-wrap: break-word;'>106</td><td style='text-align: center; word-wrap: break-word;'>94</td><td style='text-align: center; word-wrap: break-word;'>142</td><td style='text-align: center; word-wrap: break-word;'>149</td><td style='text-align: center; word-wrap: break-word;'></td></tr></table>

Using a Wilcoxon rank-sum test, investigate this claim with a 5% significance level.

6 Plants of the same species grow on opposite sides of a river. It is thought that plants on the north side grow taller than those on the south side. Eight randomly selected plants are chosen from each side of the river, removed and their lengths measured to the nearest cm. By using a Wilcoxon rank-sum test, investigate this claim with a 5% significance level.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>North side</td><td style='text-align: center; word-wrap: break-word;'>23</td><td style='text-align: center; word-wrap: break-word;'>21</td><td style='text-align: center; word-wrap: break-word;'>20</td><td style='text-align: center; word-wrap: break-word;'>28</td><td style='text-align: center; word-wrap: break-word;'>27</td><td style='text-align: center; word-wrap: break-word;'>19</td><td style='text-align: center; word-wrap: break-word;'>24</td><td style='text-align: center; word-wrap: break-word;'>25</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>South side</td><td style='text-align: center; word-wrap: break-word;'>18</td><td style='text-align: center; word-wrap: break-word;'>15</td><td style='text-align: center; word-wrap: break-word;'>22</td><td style='text-align: center; word-wrap: break-word;'>14</td><td style='text-align: center; word-wrap: break-word;'>16</td><td style='text-align: center; word-wrap: break-word;'>22</td><td style='text-align: center; word-wrap: break-word;'>17</td><td style='text-align: center; word-wrap: break-word;'>26</td></tr></table>

7 A supermarket manager wishes to investigate the quality of plums. Plums can be delivered from source to the supermarket either chilled (below  $ 5^{\circ} $C) or at a constant temperature of  $ 12^{\circ} $C. The amount of time (in days) it takes for the plums to become soft and therefore overripe is measured and ranked. The highest rank is the quickest to become overripe.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Stored at 12°C</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>8</td><td style='text-align: center; word-wrap: break-word;'>9</td><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>11</td><td style='text-align: center; word-wrap: break-word;'>10</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Chilled</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>6</td><td style='text-align: center; word-wrap: break-word;'></td></tr></table>

Carry out an appropriate non-parametric test, at the 5% level of significance, to investigate whether the chilled plums take longer to become overripe.

<!-- page 285 -->

Mr Sum wishes to investigate whether a student's test score depends on whether the test is taken in the morning or in the afternoon. He selects a random sample of 35 students of similar ability, and randomly assigns some of them to take the test in the morning and the rest to take the test in the afternoon. The students taking the test in the morning are kept away from the students taking the test in the afternoon. The ordered scores are given in the following table (M for morning sitting, A for afternoon sitting).


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>M</td><td style='text-align: center; word-wrap: break-word;'>31</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>M</td><td style='text-align: center; word-wrap: break-word;'>64</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>M</td><td style='text-align: center; word-wrap: break-word;'>32</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>65</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>M</td><td style='text-align: center; word-wrap: break-word;'>38</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>66</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>M</td><td style='text-align: center; word-wrap: break-word;'>39</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>M</td><td style='text-align: center; word-wrap: break-word;'>67</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>41</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>68</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>43</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>69</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>M</td><td style='text-align: center; word-wrap: break-word;'>44</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>M</td><td style='text-align: center; word-wrap: break-word;'>70</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>47</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>72</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>M</td><td style='text-align: center; word-wrap: break-word;'>48</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>73</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>49</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>75</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>M</td><td style='text-align: center; word-wrap: break-word;'>51</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>76</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>56</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>78</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>M</td><td style='text-align: center; word-wrap: break-word;'>57</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>M</td><td style='text-align: center; word-wrap: break-word;'>81</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>58</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>82</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>M</td><td style='text-align: center; word-wrap: break-word;'>59</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>85</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>M</td><td style='text-align: center; word-wrap: break-word;'>60</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>86</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>M</td><td style='text-align: center; word-wrap: break-word;'>62</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>88</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>63</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr></table>

Using a suitable approximation, test, at a 2% level of significance, whether exam performance is affected by the session in which a student takes the examination.

## WORKED EXAM-STYLE QUESTION

The following table shows the systolic blood pressure (mm Hg) of a random sample of eight students before and after a six-week training period.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Student</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>6</td><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'>8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Before training</td><td style='text-align: center; word-wrap: break-word;'>130</td><td style='text-align: center; word-wrap: break-word;'>170</td><td style='text-align: center; word-wrap: break-word;'>125</td><td style='text-align: center; word-wrap: break-word;'>170</td><td style='text-align: center; word-wrap: break-word;'>130</td><td style='text-align: center; word-wrap: break-word;'>130</td><td style='text-align: center; word-wrap: break-word;'>145</td><td style='text-align: center; word-wrap: break-word;'>160</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>After training</td><td style='text-align: center; word-wrap: break-word;'>120</td><td style='text-align: center; word-wrap: break-word;'>163</td><td style='text-align: center; word-wrap: break-word;'>120</td><td style='text-align: center; word-wrap: break-word;'>135</td><td style='text-align: center; word-wrap: break-word;'>143</td><td style='text-align: center; word-wrap: break-word;'>136</td><td style='text-align: center; word-wrap: break-word;'>144</td><td style='text-align: center; word-wrap: break-word;'>120</td></tr></table>

a Stating clearly your hypotheses, test, using the Wilcoxon signed-rank test, whether or not there is evidence that the training has reduced blood pressure. Use a 5% level of significance.

At a later date a random sample of 30 students undertake a six-week training period. Analysis of their results using the Wilcoxon signed-rank test gives T = 132.

b Stating clearly your hypotheses and using a 5% level of significance, test whether or not there is evidence that the training has reduced blood pressure.

<!-- page 286 -->

## Answer

 $ H_{0} $: Population median blood pressure is unchanged.

H $ _{1} $: Population median blood pressure has decreased.

Define the hypotheses.




<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>6</td><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'>8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Before-after</td><td style='text-align: center; word-wrap: break-word;'>10</td><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>35</td><td style='text-align: center; word-wrap: break-word;'>-13</td><td style='text-align: center; word-wrap: break-word;'>-6</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>40</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Rank</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'>6</td><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Signed rank</td><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'>-6</td><td style='text-align: center; word-wrap: break-word;'>-3</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>8</td></tr></table>

Calculate the sums of positive ranks, $P$, the sums of negative ranks, $N$, and the test statistic, $T$.

 $$ P=27,N=9 $$ 

 $$ T=\min(P,N)=9 $$ 

Critical value is 5.

Since 9 > 5, do not reject  $ H_{0} $.

There is no evidence to suggest that the median blood pressure has decreased.

b  $ H_{0} $: Population median blood pressure is unchanged.

H $ _{1} $: Population median blood pressure has decreased.

The test is one-tailed.



Compare the test statistic with the critical value.

 $$ \mathrm{E}(T)=\frac{n(n+1)}{4}=232.5 $$ 

Conclude in context.

 $$  Var(X)=\frac{n(n+1)(2n+1)}{24}=2363.75 $$ 

Define the hypotheses.

 $$ \begin{array}{l} \text{Test statistic} = z = \frac{T - \mu + 0.5}{\sigma} \\\qquad = \frac{132 - 232.5 + 0.5}{\sqrt{2363.75}} \\ \qquad = -2.06  \end{array} $$ 

Calculate $E(T)$ and $\mathrm{Var}(T)$. We can approximate to the normal distribution as $n$ is large.

Calculate the test statistic, remembering continuity corrections.

Critical value = -1.645

Since -2.06 < -1.645, reject  $ H_{0} $.

Find the critical value.

The population median blood pressure has decreased.

Compare the test statistic with the critical value.



Conclude in context.

<!-- page 287 -->

## Checklist of learning and understanding

## Single-sample sign test:

Given $n$ data points, a sign test is created using $X \sim \mathrm{Bin}(n, 0.5)$. The test statistic can be the number of + signs, that is the number of data points greater than the median. We can calculate the probability that $X$ is above this test statistic, below this test statistic, or either in the case of a two-tailed test.

## Wilcoxon signed-rank test:

A Wilcoxon signed-rank test can be performed when:

the underlying data are symmetric

the underlying data are continuous.

Where:

P is the sum of the ranks corresponding to the positive differences from the stated median

N is the sum of the ranks corresponding to the negative differences from the stated median

 $ T = \min(P, N) $ is the test statistic.

Given the statistic  $ T = \min(P, N) $, then  $ \mathrm{E}(T) = \frac{n(n+1)}{4} $,  $ \mathrm{Var}(T) = \frac{n(n+1)(2n+1)}{24} $.

For large n:  $ T \sim \mathrm{N}\left(\frac{n(n+1)}{4}, \frac{n(n+1)(2n+1)}{24}\right) $ allowing for an approximate z-test to be done using  $ z = \frac{T - \mu + 0.5}{\sigma} $.

## Wilcoxon matched-pairs signed-rank test:

the difference between matched-pairs is symmetric

- A Wilcoxon matched-pairs signed-rank test can be performed when:

the difference between matched-pairs is continuous.

Where:

P is the sum of the ranks corresponding to the positive differences between the matched pairs

N is the sum of ranks corresponding to the negative differences between the matched pairs

 $ T = \min(P, N) $ is the test statistic.

Given the statistic  $ T = \min(P, N) $, then  $ \mathrm{E}(T) = \frac{n(n+1)}{4} $ and  $ \mathrm{Var}(T) = \frac{n(n+1)(2n+1)}{24} $.

For large  $ n $,  $ T \sim \mathrm{N}\left(\frac{n(n+1)}{4}, \frac{n(n+1)(2n+1)}{24}\right) $, allowing for an approximate z-test with  $ z = \frac{T - \mu + 0.5}{\sigma} $.

<!-- page 288 -->

## Wilcoxon rank-sum test:

A Wilcoxon rank-sum test can be performed when the two samples are independent, where:

the two samples have sizes m and n, where  $ m \leq n $

 $ R_{m} $ is the sum of the ranks of the items in the sample of size m

the test statistic is  $ W = \min(R_m, m(n + m + 1) - R_m) $.

Given the test statistic $W$, then $E(W)=\frac{m(n+m+1)}{2}$ and $\mathrm{Var}(W)=\frac{mn(n+m+1)}{12}$.

For large $n$ and $m$ ($n \geq 10, m \geq 10$) it is possible to approximate $W$ as a normal distribution:

 $ W \sim \mathrm{N}\left(\frac{m(n+m+1)}{2}, \frac{mn(n+m+1)}{12}\right) $, allowing for an approximate z-test with  $ z = \frac{W - \mu + 0.5}{\sigma} $.

<!-- page 289 -->

The dining room in a school is some distance away from the building that has all of the classrooms in it. The school believes that students take longer walking back from the dining room after lunch than they do walking there. The school records the time taken (in seconds) by ten randomly chosen students to walk to the dining room and ten students to walk back to the main school. The recorded times are presented in the following tables.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">To the dining hall</td><td style='text-align: center; word-wrap: break-word;'>62</td><td style='text-align: center; word-wrap: break-word;'>58</td><td style='text-align: center; word-wrap: break-word;'>69</td><td style='text-align: center; word-wrap: break-word;'>84</td><td style='text-align: center; word-wrap: break-word;'>45</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>96</td><td style='text-align: center; word-wrap: break-word;'>116</td><td style='text-align: center; word-wrap: break-word;'>89</td><td style='text-align: center; word-wrap: break-word;'>51</td><td style='text-align: center; word-wrap: break-word;'>75</td></tr></table>


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">From the dining hall</td><td style='text-align: center; word-wrap: break-word;'>67</td><td style='text-align: center; word-wrap: break-word;'>85</td><td style='text-align: center; word-wrap: break-word;'>68</td><td style='text-align: center; word-wrap: break-word;'>100</td><td style='text-align: center; word-wrap: break-word;'>49</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>121</td><td style='text-align: center; word-wrap: break-word;'>139</td><td style='text-align: center; word-wrap: break-word;'>87</td><td style='text-align: center; word-wrap: break-word;'>54</td><td style='text-align: center; word-wrap: break-word;'>88</td></tr></table>

a i Using these data, state which non-parametric test would be most appropriate. Give a reason for your choice and any assumptions you need to make.

ii Carry out a test of the school's belief at the 5% significance level.

b Later on, the school discovers that the person who collected the data has used the same ten students and has recorded them in the same order.

i Which test is now most appropriate to use? Give a reason for your answer.

ii Using this new information, carry out a test of the school's belief at the 5% significance level.

M 2 The blood cholesterol levels of 30 males and 20 females are measured. These data are shown in the following table.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="6">Males</td><td style='text-align: center; word-wrap: break-word;'>621</td><td style='text-align: center; word-wrap: break-word;'>550</td><td style='text-align: center; word-wrap: break-word;'>104</td><td style='text-align: center; word-wrap: break-word;'>303</td><td style='text-align: center; word-wrap: break-word;'>384</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>1080</td><td style='text-align: center; word-wrap: break-word;'>1061</td><td style='text-align: center; word-wrap: break-word;'>771</td><td style='text-align: center; word-wrap: break-word;'>206</td><td style='text-align: center; word-wrap: break-word;'>1203</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>810</td><td style='text-align: center; word-wrap: break-word;'>259</td><td style='text-align: center; word-wrap: break-word;'>610</td><td style='text-align: center; word-wrap: break-word;'>770</td><td style='text-align: center; word-wrap: break-word;'>382</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>829</td><td style='text-align: center; word-wrap: break-word;'>385</td><td style='text-align: center; word-wrap: break-word;'>479</td><td style='text-align: center; word-wrap: break-word;'>1301</td><td style='text-align: center; word-wrap: break-word;'>551</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>92</td><td style='text-align: center; word-wrap: break-word;'>723</td><td style='text-align: center; word-wrap: break-word;'>105</td><td style='text-align: center; word-wrap: break-word;'>478</td><td style='text-align: center; word-wrap: break-word;'>417</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>1081</td><td style='text-align: center; word-wrap: break-word;'>383</td><td style='text-align: center; word-wrap: break-word;'>205</td><td style='text-align: center; word-wrap: break-word;'>207</td><td style='text-align: center; word-wrap: break-word;'>258</td></tr><tr><td rowspan="4">Females</td><td style='text-align: center; word-wrap: break-word;'>208</td><td style='text-align: center; word-wrap: break-word;'>482</td><td style='text-align: center; word-wrap: break-word;'>94</td><td style='text-align: center; word-wrap: break-word;'>194</td><td style='text-align: center; word-wrap: break-word;'>370</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>973</td><td style='text-align: center; word-wrap: break-word;'>683</td><td style='text-align: center; word-wrap: break-word;'>72</td><td style='text-align: center; word-wrap: break-word;'>50</td><td style='text-align: center; word-wrap: break-word;'>162</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>149</td><td style='text-align: center; word-wrap: break-word;'>215</td><td style='text-align: center; word-wrap: break-word;'>304</td><td style='text-align: center; word-wrap: break-word;'>127</td><td style='text-align: center; word-wrap: break-word;'>233</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>189</td><td style='text-align: center; word-wrap: break-word;'>529</td><td style='text-align: center; word-wrap: break-word;'>191</td><td style='text-align: center; word-wrap: break-word;'>974</td><td style='text-align: center; word-wrap: break-word;'>710</td></tr></table>

Using a suitable approximation, test, at the 5% significance level, whether the blood cholesterol levels of females and males differ. Is the assumption that the dataset is symmetric justified?

<!-- page 290 -->

3 An investigation is conducted into the pollution levels in a major city. The number of 2.5 mm particles can be measured using the Air Quality Index (AQI). The World Health Organization recommends that an AQI of 50 or below will not have a significant effect on health. The AQI is measured for 14 consecutive days. The data are shown in the following table.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>45</td><td style='text-align: center; word-wrap: break-word;'>132</td><td style='text-align: center; word-wrap: break-word;'>87</td><td style='text-align: center; word-wrap: break-word;'>103</td><td style='text-align: center; word-wrap: break-word;'>67</td><td style='text-align: center; word-wrap: break-word;'>46</td><td style='text-align: center; word-wrap: break-word;'>90</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>78</td><td style='text-align: center; word-wrap: break-word;'>54</td><td style='text-align: center; word-wrap: break-word;'>79</td><td style='text-align: center; word-wrap: break-word;'>81</td><td style='text-align: center; word-wrap: break-word;'>44</td><td style='text-align: center; word-wrap: break-word;'>65</td><td style='text-align: center; word-wrap: break-word;'>82</td></tr></table>

a Explain why the following tests cannot be carried out:

i a t-test

ii a single-sample Wilcoxon signed-rank test.

b Carry out an appropriate test, at the 5% significance level, to establish whether there is evidence that the AQI is above 50 in the city.

