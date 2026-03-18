import torch.nn as nn

class ActorHead(nn.Module):
    def __init__(self, input_dim, action_dim=3):  # steer, accel, brake
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 512),
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, action_dim),
            nn.Tanh()
        )
    def forward(self, x):
        return self.net(x)
    