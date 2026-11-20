# ADAS Collision Avoidance

An autonomous RC vehicle that detects obstacles with a 2D LiDAR and steers or brakes to avoid them. A ROS2 perception stack (targeting an NVIDIA Jetson) decides what to do; an STM32 microcontroller turns those decisions into real-time steering and throttle signals and can hand control back to a human driver at any time.

This repository holds the two pieces that talk to the hardware: the **STM32 firmware** and the **LiDAR packet parser**. The project is in active development (see [Status](#status)).

## System overview

```
LDROBOT LiDAR --> LiDAR driver --> perception --> avoidance logic --> STM32 bridge
                                                                         |
                                                                      UART (USB)
                                                                         v
                                              STM32F446RE (Nucleo-F446RE): command parser, watchdog, PWM
                                                       |                        |
                                                   TIM1 PWM                 GPIO gates
                                                       v                        v
                                        steering servo + VXL-3m ESC     MOSFET switches <-- RC receiver (manual)
```

- The ROS2 side publishes drive decisions; a bridge node serializes them to text commands over UART.
- The STM32 generates the PWM that drives the steering servo and the ESC.
- Two GPIO-controlled MOSFET switches select who drives the servo and ESC: the RC receiver (manual) or the STM32 (autonomous).

## Repository layout

| Path | What it is |
| --- | --- |
| `UART_TX_POLLING/` | STM32CubeIDE project for the STM32F446RE. Application code is `Src/main.c`; `Drivers/` is ST's HAL and CMSIS. The folder name is from the first version of the project, which used polling; UART receive is now interrupt-driven. |
| `Lidar_Parser.py` | Python script that reads the LiDAR's serial stream, finds and checks packets, and decodes them into distance, intensity and angle per point. |

## STM32 firmware

Target: STM32F446RE (Nucleo-F446RE), written in C against the STM32 HAL.

**Clocks and timing.** The 16 MHz HSI feeds the PLL to give a 180 MHz system clock. TIM1 is prescaled to a 1 MHz tick with a 20 ms period, which gives the 50 Hz PWM that hobby servos and ESCs expect. Pulse widths are set in microseconds (1000 to 2000, with 1500 as neutral).

**Outputs**

| Signal | Pin | Peripheral |
| --- | --- | --- |
| Steering servo PWM | PA8 | TIM1 channel 1 |
| Throttle / ESC PWM | PA9 | TIM1 channel 2 |
| Manual/auto gate 1 | PB0 | GPIO output |
| Manual/auto gate 2 | PB1 | GPIO output |

**UART command interface.** USART2 (PA2 TX, PA3 RX) runs at 115200 baud, 8N1. On the Nucleo board this is the ST-LINK USB virtual COM port. Receive is interrupt-driven: the RXNE interrupt fires for each byte, and a callback assembles bytes into a line buffer and parses a command when it sees a newline. Commands are plain text, one per line:

| Command | Effect |
| --- | --- |
| `T<1000-2000>` | Set the steering pulse width in microseconds. Values outside the range are ignored. |
| `S<1000-2000>` | Set the throttle pulse width in microseconds. Values outside the range are ignored. |
| `AUTO` | Drive PB0 and PB1 low so the STM32 controls the servo and ESC. |
| `MANUAL` | Drive PB0 and PB1 high so the RC receiver controls the servo and ESC, and zero the STM32's PWM outputs. |

**Fail-safe.** A watchdog runs in the main loop. If no command arrives for 5 seconds, the firmware switches the gates back to manual and returns both PWM outputs to neutral (1500 microseconds).

**Build and flash.** Open `UART_TX_POLLING` in STM32CubeIDE, build, and flash to a Nucleo-F446RE over ST-LINK. To test without the Jetson, open the board's virtual COM port in any serial terminal at 115200 baud and send, for example, `AUTO`, then `T1600`.

## LiDAR parser

`Lidar_Parser.py` reads the LDROBOT LiDAR's serial stream (230400 baud) and decodes it:

- Packets are 47 bytes, starting with the header bytes `0x54 0x2C`.
- Each packet is validated with a CRC-8 (polynomial `0x4D`) over the first 46 bytes before it is decoded. If the check fails, the parser drops one byte and searches for the next header so it can recover from a corrupted or misaligned stream.
- A valid packet yields the rotation speed, the start and end angles, and 12 measurement points. Each point has a distance, an intensity, and an angle interpolated between the start and end angles.

**Run**

```
pip install pyserial
python Lidar_Parser.py
```

The serial port is set at the top of the file (`port_name`, currently `COM3`); change it to match your machine.

## Status

| Component | State |
| --- | --- |
| STM32 firmware: UART command parsing, dual-channel PWM, manual/auto switching, watchdog | Working on the vehicle |
| LiDAR packet parser | Working; prints decoded points |
| ROS2 nodes (driver, perception, avoidance logic, STM32 bridge) | Not in this repository yet |
| Obstacle classifier (pedestrian / vehicle / wall) and gap-finding avoidance logic | In development |

## Hardware

- NVIDIA Jetson (target for the ROS2 perception and planning stack)
- STM32 Nucleo-F446RE (real-time control)
- LDROBOT 2D LiDAR
- RC car with a steering servo, a VXL-3m ESC and motor, and a TQi receiver for manual driving
- MOSFET switches for manual/autonomous selection
