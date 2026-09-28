# Alternating currents

<!-- Cambridge International AS and a Level Physics Students Book 3rd Edition (Crundell, Mike Goodwin, Geoff).pdf p356-364 -->

<!-- page 356 -->

#### Learning outcomes

By the end of this topic, you will be able to:

**21.1 Characteristics of alternating currents**

**1** understand and use the terms period, frequency and peak value as applied to an alternating current or voltage

**2** use equations of the form **x =** $\mathbf{x}_{0}$ **sin**ω **t** representing a sinusoidally alternating current or voltage

**3** recall and use the fact that the mean power in a resistive load is half the maximum power for a sinusoidal alternating current

**4** distinguish between root-mean-square (r.m.s.) and peak values and recall and use $\mathbf{I}_{r.m.s}$ = $\mathbf{I}_{0}$**/ 2** and $\mathbf{V}_{r.m.s}$ = $\mathbf{V}_{0}$**/ 2** for a sinusoidal alternating current

**21.2 Rectification and smoothing**

**1** distinguish graphically between half-wave and full-wave rectification

**2** explain the use of a single diode for the half-wave rectification of an alternating current

**3** explain the use of four diodes (bridge rectifier) for the full-wave rectification of an alternating current

**4** analyse the effect of a single capacitor in smoothing, including the effect of the value of capacitance and the load resistance

#### Starting points

- Frequency **f** is related to period **T** by the expression **f = 1/T**.

- Power is dissipated in a resistor and the magnitude of the power is given by the expressions **P =** $\mathbf{I}^{2}$**R** or **P = VI** or **P =** $\mathbf{V}^{2}$**/R**.

- A diode is a device that allows current to move in one direction only.

## 21.1 Characteristics of alternating currents

Up to this point in our studies, we have dealt with systems in which a battery is connected to a circuit and there is a steady current in one direction. You will know this sort of current as a **direct current**, abbreviated to d.c. However, the domestic electricity supply, produced by generators, is one which uses **alternating current** (a.c.). An alternating current or voltage reverses its direction regularly and is usually sinusoidal, as shown in Figure 21.1.

**Figure 21.1** Direct and alternating currents

The time T taken for one complete cycle of the alternating current is the period of the current.

<!-- page 357 -->

We can represent the current and the voltage by the equations

I = $I_{0}$ sin ωt V = $V_{0}$ sin ωt

The graphs of I = $I_{0}$ sin ωt and V = $V_{0}$ sin ωt have the same sinusoidal shape as the graphs used to represent simple harmonic motion and so the electrons in a wire carrying a.c. move backwards and forwards with s.h.m. Hence we can describe the angular frequency of the current in rad $\mathrm{s}^{-1}$ as ω where T = 2π/ω. The reciprocal of the period is the frequency f. That is, f = 1/T and f = ω/2π. The frequency is the number of complete cycles per unit time. The unit of frequency is the hertz (Hz) where 1 Hz = 1 cycle per second.

The **peak value** of the current or voltage is $I_{0}$ or $V_{0}$, the amplitude of the oscillating current or voltage. Sometimes the term peak-to-peak value is used; this means $2I_{0}$ or $2V_{0}$, or twice the amplitude.

### WORKED EXAMPLE 21A

The variation with time t (in seconds) of the potential difference V (in volts) of an alternating supply is given by V = 24 sin 380t. Determine, for this supply:

**a** the peak potential difference

**b** the frequency.

#### Answers

**a** peak potential difference = **24 V**

**b** ω = 2πf = 380 frequency = 380/2π = **60 Hz**

#### Question

**1** The peak value of the mains potential difference delivered to homes in India is 325 V and the frequency is 50 Hz. Write an equation for the variation in the mains potential difference in terms of time t.

### Measuring period and frequency using a cathode-ray oscilloscope

A **cathode-ray oscilloscope (CRO)** has a calibrated time-base, so that measurements from the screen of the CRO can be used to give values of time intervals. One application is to measure the frequency of a sinusoidally varying current or voltage. The signal is connected to the Y-input of the CRO, and the y-gain and time-base controls are adjusted until a trace of at least one, but fewer than about five, complete cycles of the signal is obtained on the screen. The distance L on the graticule (the scale on the screen) corresponding to one complete cycle is measured (Figure 21.2).

**Figure 21.2** The use of a CRO to measure frequency

<!-- page 358 -->

It is good practice to measure the length of, say, four cycles, and then divide by 4 so as to obtain an average value of L. The graticule will probably be divided into centimetre and perhaps millimetre or two-millimetre divisions. If the time-base setting is x (which will be in units of seconds, milliseconds or microseconds per centimetre), the time T for one cycle is given by T = Lx. The frequency f of the signal is then obtained from f = 1/T.

The uncertainty of the determination will depend on how well you can estimate the measurement of the length of the cycle from the graticule. Remembering that the trace has a finite width, you can probably measure this length to an uncertainty of about ±2 mm.

### WORKED EXAMPLE 21B

An alternating current is connected to the Y-input of a CRO. When the time-base control is set at 0.50 milliseconds per centimetre, the trace shown in Figure 21.3 is obtained. What is the frequency of the current?

#### Answer

Two complete cycles of the trace occupy 6.0 cm on the graticule. The length of one cycle is therefore 3.0 cm. The time-base setting is 0.50 ms $\mathrm{cm}^{-1}$, so 3.0 cm is equivalent to 3.0 × 0.50 = 1.5 ms. The frequency is thus 1/1.5 × $10^{-3}$ = **670 Hz**.

**Figure 21.3**

#### Question

**2** The same signal is applied to the Y-input of the CRO as in Worked Example 21B, but the time-base control is changed to 2.0 milliseconds per centimetre. How many complete cycles of the trace will appear on the screen, which is 8.0 cm wide?

### Measuring voltage or current using a cathode-ray oscilloscope

The cathode-ray oscilloscope, with its calibrated y-gain, may be used to measure the amplitude of an alternating voltage signal.

(We have already seen how the time-base of the CRO may be used to measure time.) The signal is connected to the Y-input, and the y-gain and time-base settings are adjusted until a suitable trace is obtained (Figure 21.4). The amplitude A of the trace is measured. If the y-gain setting is Q (in units of volts per centimetre), the peak value $V_{0}$ of the signal is given by $V_{0}$ = AQ. The peak-to-peak value is $2V_{0}$.

If the time base is switched off a straight vertical line will be displayed on the screen. The peak-to-peak value of this trace from bottom to top can be measured. The peak value $V_{0}$ is half the peak-to-peak voltage.

Once we know the peak voltage ($V_{0}$) and the resistance (R) of the component the oscilloscope is connected across, we can calculate the peak current ($I_{0}$) using the equation V = IR.

<!-- page 359 -->

**Figure 21.4** Measurement of alternating voltage

### WORKED EXAMPLE 21C

An alternating voltage is connected to the Y-input of a CRO. When the Y-amplifier control is set to 5.0 millivolts per centimetre, the trace shown in Figure 21.5 is obtained. Find the peak voltage of the signal.

#### Answer

Measure the amplitude of the trace on the graticule: this is 1.4 cm. The y-gain setting is 5.0 mV $\mathrm{cm}^{-1}$. 1.4 cm is thus equivalent to 1.4 × 5.0 = **7.0 mV**. The peak voltage of the signal is 7.0 mV.

**Figure 21.5**

#### Question

**3** The Y-input of a CRO is connected to an alternating voltage source. When the y-gain control is set to 20 millivolts per centimetre, the trace shown in Figure 21.6 is obtained. Find the peak-to-peak voltage of the signal.

**Figure 21.6**

### Power in an a.c. circuit

It is clear from Figure 21.1 that the average value of an alternating current is zero. However, this does not mean that when an a.c. source is connected to a resistor, no power is generated in the resistor. An alternating current in a wire can be thought of as electrons moving backwards and forwards, and passing on their energy by collision.

<!-- page 360 -->

The power generated in a resistance R is given by the usual formula

P = $I^{2}$R but here the current I must be written as

I = $I_{0}$ sin ωt

Thus

P = $I_{0}^{2}$R $\mathrm{sin}^{2}$ ωt

Since $I_{0}^{2}$ and $\mathrm{sin}^{2}$ ωt are always positive, we see that the power P is also always positive.

The expression we have just derived for P gives the power at any instant. What is much more useful is the average or mean power. This is the quantity which must be used in assessing the power generated in the resistor. Because $I_{0}$ and R are constants, the average value of P will depend on the average value of $\mathrm{sin}^{2}$ ωt, which is $\frac{1}{2}$ . So the average power <P> delivered to the resistor is

<P> = $\frac{1}{2}$ $I^{0}$ ${}^{2}$R = $\frac{1}{2}$ $V^{0}$ ${}^{2}$/R or

For a sinusoidal alternating current the mean power is half the maximum power.

We could use the average value of the square of the current or the voltage in these relations, since

<$I^{2}$> = $\frac{1}{2}$ $I^{0}$ ${}^{2}$ and <$V^{2}$> = $\frac{1}{2}$ $V^{02}$

The square root of <$I^{2}$> is called the **root-mean-square**, or **r.m.s.** value of the current $I_{rms}$ and similarly the square root of <$V^{2}$> the root-mean-square, or r.m.s. value of the voltage $V_{rms}$. The numerical relations are $I_{rms}$ = <$I^{2}$> = $I_{0}$ / 2 = $\mathrm{0.707I}_{0}$ $V_{rms}$ = <$V^{2}$> = $V_{0}$ / 2 = $\mathrm{0.707V}_{0}$

The r.m.s. values are useful because they represent the effective values of current and voltage in an a.c. circuit. A direct current with a value of I, equal to the r.m.s current $I_{rms}$ of an a.c. circuit, will produce exactly the same heating effect in a resistor. In specifying a domestic supply voltage, it is the r.m.s. value that is quoted, not the peak value.

The r.m.s. value of the alternating current or voltage is that value of the direct current or direct voltage that would produce thermal energy at the same rate in a resistor.

### WORKED EXAMPLE 21D

A 1.5 kW heater is connected to the domestic supply, which is quoted as 230 V. Calculate the peak current in the heater, and its resistance.

#### Answer

The r.m.s version of the power/current/voltage equation is $I_{rms}V_{rms}$ = mean power.

This gives $I_{rms}$ = (1.5 × $10^{3}$)/230 = 6.5 A.

The peak current $I_{0}$ = $2I_{rms}$ = **9.2 A**

The resistance R = $V_{rms}$/$I_{rms}$ = 230/6.5 = **35 Ω**

<!-- page 361 -->

#### Questions

**4** The peak voltage of an alternating signal is 28 mV. Find the r.m.s. voltage.

**5** For the alternating supply given by V = 24 sin 380t where V is in volts, determine the r.m.s. voltage.

**6** A heater of resistance 35 Ω is connected to a domestic supply, quoted as 230 V.

**a** Calculate:

**i** the peak voltage of the supply

**ii** the average power in the resistor.

**b** What are the maximum and minimum values of the instantaneous power in the resistor?

## 21.2 Rectification and smoothing

It is sometimes necessary to convert an alternating current into a direct current. This is because most electronic devices require direct current, whereas the domestic supply is alternating. The conversion can be done by a process known as **rectification**.

Suppose a single diode (see Topic 9.3) is connected into the a.c. circuit of Figure 21.7.

**Figure 21.7** Single-diode circuit for half-wave rectification

We know that the diode allows current to flow in one direction only. This means that the output voltage across the resistor will consist only of the positive half-cycles of the input voltage, as shown in Figure 21.8. The diode has rejected the negative part of the input, producing a unidirectional voltage across the output resistor which fluctuates considerably, rather than a constant direct voltage. Nevertheless, we have achieved what is called **half-wave rectification**.

**Figure 21.8** Half-wave rectification

It is more satisfactory, and energy efficient, to make use of the negative half-cycles of the input and reverse their polarity, as shown in Figure 21.9. This process is called **full-wave rectification**.

**Figure 21.9** Full-wave rectification

<!-- page 362 -->

One circuit used for full-wave rectification is illustrated in Figure 21.10.

**Figure 21.10** Four-diode (bridge) circuit for full-wave rectification

It uses four diodes arranged in a diamond pattern and is referred to as a **bridge rectifier** circuit. The input terminals are P and Q. If P is positive during the first half-cycle, diodes 1 and 2 on opposite sides of the diamond will conduct. In the next half-cycle Q is positive, and diodes 3 and 4 conduct. Thus the resistor acting as a load will always have its upper terminal positive and its lower terminal negative.

The circuit has produced a unidirectional voltage, but the output is still not a good approximation to steady direct voltage, as required by most electronic equipment. We can improve the situation by inserting a capacitor across the output terminals of the bridge circuit as in Figure 21.11.

**Figure 21.11** Smoothing by capacitor

The capacitor charges up on the rising part of the half-cycle, and then discharges through the resistor as the output voltage falls. The effect is to reduce the fluctuations in the unidirectional output. This process is called **smoothing**.

The discharge of a capacitor was discussed in Topic 19.3. The important factor is the time constant of the resistor–capacitor circuit. If the product of the capacitance C and the load resistance R is much larger than the half-period of the original supply to the rectifier

<!-- page 363 -->

circuit, the ripple on the direct voltage or current will be small. Ripple is the magnitude of the variation of the voltage or current that is superimposed on the direct voltage or current. Reducing the time constant will increase the ripple, as illustrated in Figure 21.12.

**Figure 21.12** Magnitude of the ripple

### SUMMARY

- Alternating current or voltage is represented by an » A single diode gives half-wave rectification:

equation of the form x = $x_{0}$ sin ωt.

- The r.m.s. value of the alternating current or negative half-cycles are blocked.

- A bridge circuit of four diodes can give full-wave voltage is that value of the direct current or direct voltage that would produce thermal energy at the same rate in a resistor.

- Peak and root-mean-square (r.m.s.) values rectification.

- A capacitor connected across the output reduces the fluctuations of the rectified output voltage applied to the load resistor.

- The degree of ripple depends on the time of sinusoidal current or voltage are related by an equation of the form $x_{0}$ = $2x_{rms}$.

- For a sinusoidal input, mean power in a resistive constant RC of the discharge of the smoothing capacitor through the load resistor. Larger RC gives smaller ripple.

load is one half of the peak power.

### END OF TOPIC QUESTIONS

**1** A stereo system has two output channels, each connected to a loudspeaker of effective resistance 8.0 Ω. Each channel can deliver a maximum average power output of 48 W to its speaker. Calculate the r.m.s. voltage and the r.m.s. current fed to one speaker at this maximum power. Assume that the loudspeaker can be treated as a simple resistance and that the voltage is sinusoidal.

**2** The full-wave rectifier circuit of Fig. 21.10 is used to rectify an a.c. input voltage of 240 V r.m.s. The output resistor has resistance 17 kΩ.

**a** Calculate the peak value of the input voltage.

**b** Estimate the average current in the output resistor.

**3 a** Complete a copy of Fig. 21.13 to show four diodes connected to form a full-wave rectifier.

**Figure 21.13**

**b** The root-mean-square input potential difference to the completed full-wave rectifier is 12 V. The frequency of the input potential difference is 50 Hz.

<!-- page 364 -->

On the axes of Fig. 21.14, sketch the variation with time t of the potential difference V across the load resistor for 3 periods of the input potential difference.

**Figure 21.14**

**c** On the completed circuit diagram of Fig. 21.13, draw the symbol for a capacitor, connected so as to produce smoothing of the output potential difference.

**d** The output load resistor in a circuit providing half-wave rectification is 23 kΩ. The variation with time t of the output voltage V across the load is shown in Fig. 21.15.

**Figure 21.15**

A capacitor of capacitance 2 µF is now connected in parallel with the load resistor. On a copy of Fig. 21.15, sketch a line to show the variation with time t of the smoothed output voltage.

