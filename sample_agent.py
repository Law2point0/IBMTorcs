# import numpy as np
# import matplotlib.pyplot as plt

# class Agent(object):
#     def __init__(self, dim_action):
#         self.dim_action = dim_action

#     def act(self, ob, reward, done, vision_on):
#         #print("ACT!")

#         # Get an Observation from the environment.
#         # Each observation vectors are numpy array.
#         # focus, opponents, track sensors are scaled into [0, 1]. When the agent
#         # is out of the road, sensor variables return -1/200.
#         # rpm, wheelSpinVel are raw values and then needed to be preprocessed.
#         # vision is given as a tensor with size of (64*64, 3) = (4096, 3) <-- rgb
#         # and values are in [0, 255]
#         if vision_on is False:
#             focus, speedX, speedY, speedZ, opponents, rpm, track, wheelSpinVel = ob
#         else:
#             focus, speedX, speedY, speedZ, opponents, rpm, track, wheelSpinVel, vision = ob

#             """ The code below is for checking the vision input. This is very heavy for real-time Control
#                 So you may need to remove.
#             """
#             print(vision.shape)
#             """
#             img = np.ndarray((64,64,3))
#             for i in range(3):
#                 img[:, :, i] = 255 - vision[:, i].reshape((64, 64))

#             plt.imshow(img, origin='lower')
#             plt.draw()
#             plt.pause(0.001)
#             """
#         return np.tanh(np.random.randn(self.dim_action)) # random action
import numpy as np
import matplotlib.pyplot as plt
import csv

class Agent(object):
    def init(self, dim_action):
        self.dim_action = dim_action

    def act(self, ob, reward, done, vision_on):
        if vision_on:
            focus, speedX, speedY, speedZ, opponents, rpm, track, wheelSpinVel, *telemetry = ob
            # Process and analyze the telemetry data as needed
            print("Telemetry Data:")
            for entry in telemetry[:5]:  # Print the first few entries (adjust as needed)
                print(entry)

        if vision_on:
            with open('telemetrycsv', 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['timestamp', 'position_x', 'position_y', 'velocity_x', 'velocity_y'])
                for entry in telemetry:
                    timestamp, position_x, position_y, velocity_x, velocity_y = entry
                    writer.writerow([timestamp, position_x, position_y, velocity_x, velocity_y])

        return np.tanh(np.random.randn(self.dim_action))  # random action

