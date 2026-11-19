# 0.9.6 Full-Flow HackRF RPi MVP

This directory preserves the FM HackRF RPi5 project copy, including its CodeAnvil
artifacts, implemented services, UI, verification kit, and systemd installer.
The target manifest is configured for the Raspberry Pi at `192.168.1.10`.

## What is included

- A recorded V-SIL project cycle with a G3 `HITL: PASS` verdict and its artifacts
  under `.codeanvil/report/01_fm_hackrf_rpi5_mvp/`.
- Real HackRF I/Q capture and an FM-band spectrum UI with receiver-level dBFS
  channel screening. The threshold is the sweep median plus a configurable margin
  (`FM_OCCUPANCY_MARGIN_DB`, default 4 dB); it is not calibrated dBm or a compliance
  determination.
- A refreshable spectrum/waterfall interface and the `uplot` frontend dependency.
- `install-service.sh`, which installs and enables
  `v0.9.6-vsil-v4-fm-hackrf-rpi.service` for the current HackRF-access user. The
  installer chooses a free web port on first installation and retains it on updates.

The G3 report records the verdict and evidence available for that cycle. The
subsequent direct code edits and systemd service operation are preserved in this
snapshot, but are not retroactively covered by that G3 verdict.

## Install and operate the service

On the Raspberry Pi, from this project directory, run as the user with HackRF
access:

```bash
./install-service.sh
```

The installer prints the local spectrum URL. The unit can be controlled with:

```bash
service=v0.9.6-vsil-v4-fm-hackrf-rpi.service
sudo systemctl status "$service"
sudo systemctl start "$service"
sudo systemctl stop "$service"
sudo systemctl restart "$service"
sudo systemctl enable --now "$service"
sudo systemctl disable --now "$service"
sudo journalctl -u "$service" -f
```

The service sets `FM_HAL=real`; mock mode is not used by this service.
