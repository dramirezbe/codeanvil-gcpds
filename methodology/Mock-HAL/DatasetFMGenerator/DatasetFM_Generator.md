# **Conceptual Functionality of DatasetFM\_Generator.ipynb**

*Technical interpretation of the supplied notebook*

#### **Purpose and scope**

The notebook is a configurable synthetic FM-broadcast IQ dataset generator. It combines multiple independently synthesized FM stations into an 8-Msample/s complex-baseband recording and subjects that composite waveform to a sequence of noise, analog front-end, and digitization effects. Its primary outputs are quantized complex IQ recordings and per-capture JSON metadata. The intent is to approximate selected behaviors of a low-cost, HackRF-like directconversion SDR for controlled spectrum-monitoring experiments; it is not a calibrated physical replica of the receiver.

Conceptually, the notebook is a *data synthesis and acquisition emulation layer*, not a station detector, occupancy estimator, temporal predictor, or regulatory compliance assessor. It is useful for algorithm development because transmission parameters, impairment settings, and several quality measurements are known during generation.

#### **End-to-end processing chain**

The processing order established in the notebook is

FM station synthesis → complex AWGN injection → branch-wise IQ imbalance

→ DC offset on summed waveform → ADC drive scaling → utilization measurement → 8-bit quantization/clipping *.*

The generator stores the resulting IQ vector and metadata, and can optionally create PSD plots. Separate signal and noise branches are retained through the imbalance operation for power bookkeeping; the branches are subsequently combined for DC offset and ADC stages.

#### **Multi-station FM synthesis**

Each capture contains between two and four independently generated FM broadcast-like stations. Each station uses an artificial audio message built from sinusoidal components and filtered random noise, with a nominal 48-kHz audio-domain rate and resampling to the 8-Msample/s IQ rate. Carrier offsets are selected on a 200-kHz raster with a 400-kHz minimum separation and a 300-kHz spectral edge guard. A station can be represented schematically by

$$s_k[n] = A_k \exp \left\{ j \left( 2\pi \frac{f_k n}{F_s} + \frac{2\pi \Delta f_k}{F_s} \sum_{m=0}^n a_k[m] + \phi_k \right) \right\}, \quad s[n] = \sum_{k=1}^K s_k[n].$$

Here *ak*[*n*] is the resampled synthetic audio, *f<sup>k</sup>* is the assigned baseband carrier offset, *A<sup>k</sup>* is station amplitude, and ∆*f<sup>k</sup>* is the peak FM deviation. This mathematical expression describes the conceptual modulation operation; implementation-specific waveform normalization and audio construction remain those of the notebook.

### **Noise and analog impairments**

Complex AWGN is introduced at a randomly selected composite SNR between 8 and 30 dB. This quantity is based on the aggregate waveform and does not guarantee an identical SNR for individual stations. The notebook then applies IQ gain and phase mismatch to the signal and AWGN branches, which can be interpreted through the widely linear relation

$$y[n] = \alpha x[n] + \beta x^*[n].$$

The conjugate component is responsible for mirror-frequency artifacts. The gain imbalance varies within ±0*.*9 dB and phase imbalance within ±6 ◦ . A complex constant offset with randomized magnitude and phase is added to the combined analog signal, modeling a central DC artifact. The offset amplitude falls in the interval 0.02–0.12 (normalized units). Finally, a random ADC drive factor of 0.35–1.35 scales the combined waveform before digitization.

#### **ADC utilization and 8-bit conversion**

Before quantization, the generator characterizes signal peaks and RMS amplitude, including separate I/Q statistics, joint-component measures, high percentiles, and levels expressed relative to full scale (dBFS). These metrics indicate under-utilization of the ADC range and potential overload. The I and Q components are then clipped and mapped onto an 8-bit discrete amplitude grid. The saved data are normalized complex samples in complex64 format, even though the representable component values reflect simulated 8-bit quantization. As a result, file data type and effective quantization resolution should not be conflated.

### **Default configuration**

|          | Parameter    |                    |     | Notebook default       |
|----------|--------------|--------------------|-----|------------------------|
|          | Generated    | captures           | 3   |                        |
| Nominal  | center       | frequency          | 98  | MHz                    |
| Sample   | rate         |                    | 8   | MS/s                   |
| Samples  | per          | capture            |     | 524,288                |
| Capture  |              | duration           |     | 65.536 ms              |
| Station  | count        |                    | 2–4 |                        |
| Channel  | raster       |                    | 200 | kHz                    |
|          | Minimum      | carrier separation | 400 | kHz                    |
| Spectral | edge         | guard              | 300 | kHz                    |
| FM       | peak         | deviation          |     | 55–75 kHz              |
|          | Maximum      | audio frequency    | 15  | kHz                    |
| Station  | gain         | range              | −   | 10 to − 1 dB           |
|          | Composite    | AWGN injection SNR |     | 8–30 dB                |
| IQ       | gain         | imbalance          | −   | 0 9 to +0 9 dB         |
| IQ       | phase        | imbalance          | −   | 6                      |
|          |              |                    |     | to +6 ◦                |
| DC       | offset       | magnitude          |     | 0.02–0.12              |
| ADC      | drive        | scaling            |     | 0.35–1.35              |
| ADC      | quantization |                    | 8   | bits per I/Q component |
| Base     | random       | seed               |     | 12345                  |
| PSD      | plots        |                    |     | Disabled by default    |

### **Quality measurements and interpretation**

The notebook distinguishes the pre-impairment AWGN injection SNR from subsequent ratios describing the transformed signal relative to AWGN, additional DC energy, and digitization errors. Among the reported fields are awgn\_injection\_snr\_db, post\_awgn\_snr\_db, post\_signal\_to\_disturbance\_db, and post\_sindr\_db. The last metric accounts for AWGN, DC, and quantization/clipping error in the notebook's internal accounting. It should not be treated uncritically as a calibrated instrument SINAD: IQ-image artifacts remain associated with the transformed signal branch rather than being separately attributed as a distortion term. These measures support controlled within-generator comparisons but do not, by themselves, validate correspondence to a hardware receiver.

#### **Outputs, reproducibility, and execution**

For each example, a NumPy .npy file stores the IQ capture and a JSON file stores station metadata (such as carrier offsets, gains, deviation, and audio composition), impairment parameters, power and quality ratios, and ADC utilization statistics. Optional PSD figures with station markers are produced when plotting is enabled. The implementation uses a per-example seed based on the seed base plus the example index; it also uses ProcessPoolExecutor for parallelizable, independent capture generation. Consequently, dataset generation is designed to be reproducible without requiring all examples to be processed sequentially.

### **Functional boundary and research applicability**

- **Implemented:** synthetic multi-station FM modulation, complex IQ mixture formation, AWGN addition, selected IQ/DC/ADC impairments, utilization statistics, quantization, metadata export, and optional PSD inspection.
- **Not implemented:** blind FM station detection, channel occupancy decisions, temporal state transitions, occupancy forecasting, learned classification, FM program-audio recovery, and regulatory compliance adjudication.
- **Ground truth available:** per-capture station generation parameters. These are valuable supervision ingredients, but the notebook does not itself produce detector-ready time– frequency bounding boxes or a labeled time-indexed channel-occupancy sequence.

## **Methodological limitations**

Synthetic audio is not equivalent to an actual received broadcast program. The model does not explicitly include multipath propagation, frequency-selective fading, oscillator phase noise, timevarying station activation, antenna characteristics, or empirically calibrated analog filtering. The minimum station separation also limits very dense adjacent-channel interference scenarios. The default three short recordings are demonstrations of dataset generation rather than a statistically adequate training or benchmark corpus. Finally, the selected 8–30-dB aggregate SNR range omits a specifically designed negative-SNR regime.

## **Overall conceptual verdict**

The notebook is best understood as a **reproducible synthetic multi-station FM acquisition emulator with staged hardware-impairment modeling and detailed measurement bookkeeping**. Its strongest contribution is the explicit link between controlled source signals, receiver-induced degradation, quantized IQ observations, and machine-readable acquisition metadata. It is a useful foundation for instantaneous FM spectrum-sensing tests, but a separate temporal occupancy model, richer RF channel model, detector-ready labeling pipeline, and real-SDR validation would be required to support robust claims about longitudinal occupancy prediction or real-world spectrum-monitoring performance.