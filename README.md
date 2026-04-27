# IBM Torcs Race Simulation
This project implements a Machine Learnt racing agent trained using Actor-Critic (A2C) reinforcements learning to drive on the corkscrew circuit within the TORCS environment.

There are implementations of a real-time race commentator and coach, both of which you can prompt and recieve live telemetry information on the race, with context from IBM's Granite AI Models.

---

## Background
This project was built as part of a Group Module at Sheffield Hallam University. The aim of this project was to explore the application of AI within a racing siumulator. Having goals of developing an autonomously controlled driver and a way to interface with the simulators telemetry through an AI chatbot correspondence.

Our AI agent uses reinforcement learning to interpret the data from 30 sensors per step, covering speed, position and distance sensors. These are then fed through a learning policy to predict the best next move, then enacted through a connection over a UDP socket that is established on startup. 

Using the same telemetry access and UDP connection as the RL agent, once connection is established a prompt window will appear, giving access to prompt the models for telemetry data and see the see the commentary text stream.

Two systems were developed in parallel over the course of this project for these features: 

| System | Required by |
|--------|-------------------|
| Primary RL agent | Self Driven Car |
| AI Chatbot Interfacing | Race Engineer and Race Commentator |

## Building
For an in depth build guide visit [Building.md](https://github.com/Law2point0/IBMTorcs/blob/main/BUILDING.md)

## Usage

### Configuring TORCS 
1. Open TORCS
2. Go to Race > Practice > Configure Race
3. Select Corckscrew from Road Tracks
4. Select "scr_server 1" as the Driver
5. Start the race and waut fir UDP connection

### Connecting UDP Features
1. Open a new Terminal
2. Navigate to gym_torcs path
3. run `py run.py`
>(for rules based implementation `run RBrun.py`)

## Contributors

This was a group effort from the Ga-SHU Racing student group from Sheffield Hallam University

**[Contributors](https://github.com/Law2point0/IBMTorcs/graphs/contributors)**


