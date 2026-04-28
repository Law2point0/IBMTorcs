import torch
import torch.nn as nn
import numpy as np
import os

CHECKPOINT_DIR = os.path.join(os.path.dirname(__file__), 'checkpoints')

class A2CAgent:
    def __init__(self, actor, critic, device, gamma=0.95, lr_actor=3e-5, lr_critic=1e-4):
        self.actor = actor.to(device)
        self.critic = critic.to(device)
        self.device = device
        self.gamma = gamma
        self.actor_opt = torch.optim.Adam(actor.parameters(), lr=lr_actor)
        self.critic_opt = torch.optim.Adam(critic.parameters(), lr=lr_critic)
        self.std = 0.4  # exploration noise



    def select_action(self, obs, episode = 0):
        obs_t = torch.FloatTensor(obs).unsqueeze(0).to(self.device)
        mean = self.actor(obs_t)
        
        # add acceleration bias to initial exploration
        bias_strength = max(0.2, 0.8 * (1 - episode / 500))
        bias = torch.tensor([[0.0, bias_strength]]).to(self.device)
        mean = mean #+ bias
        
        #builds current poloicy distribution and samples action
        dist = torch.distributions.Normal(mean, self.std)
        action = dist.sample()
        log_prob = dist.log_prob(action).sum(dim=1)
        
        # gets critic prediction
        with torch.no_grad():
            value = self.critic(obs_t)
        
        #reconverts to numpy array for torcs 
        action_np = action.detach().cpu().numpy().flatten()
        action_np[0] = np.clip(action_np[0], -1, 1)
        action_np[1] = np.clip(action_np[1], -1, 1)
        
        return action_np, log_prob, value

    def update(self, log_probs, values, rewards, obs_list):
        if len(rewards) < 2:
            return 0, 0

        # computes decreasing reward returns 
        returns = []
        R = 0
        for r in reversed(rewards):
            R = r + self.gamma * R
            returns.insert(0, R)

        returns = torch.tensor(returns, dtype=torch.float32).to(self.device)

        # recomputes values with gradients for critic
        obs_t = torch.FloatTensor(np.array(obs_list)).to(self.device)
        values_t = self.critic(obs_t).squeeze()

        mean = self.actor(obs_t)
        dist = torch.distributions.Normal(mean, self.std)
        entropy = dist.entropy().sum(dim=1).mean() # ENTROPY HELL YEAH


        advantages = returns - values_t.detach()
        #advantages = torch.clamp(advantages, -5.0, 5.0)
        print(f"[ADV] mean={advantages.mean():.4f} std={advantages.std():.4f} min={advantages.min():.4f} max={advantages.max():.4f}")
        #if len(advantages) > 1:
            #advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        #actor loss reduces with hiogher advantgages + entropy for exploration
        actor_loss = -(torch.stack(log_probs) * advantages).mean() - 0.01 * entropy
        #actor_loss = torch.clamp(actor_loss, -1.0, 1.0)
        #critic loss stays as mse for more stable predictions
        critic_loss = nn.functional.mse_loss(values_t, returns)
        

        #backfills loses,k clips gradients applys changes 
        self.actor_opt.zero_grad()
        actor_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.actor.parameters(), 0.5)
        self.actor_opt.step()

        self.critic_opt.zero_grad()
        critic_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.critic.parameters(), 1.0)
        self.critic_opt.step()


        return actor_loss.item(), critic_loss.item()

    def save(self, episode, path='checkpoints'):
        os.makedirs(path, exist_ok=True)
        torch.save({
            'episode': episode,
            'actor': self.actor.state_dict(),
            'critic': self.critic.state_dict(),
            'actor_opt': self.actor_opt.state_dict(),
            'critic_opt': self.critic_opt.state_dict(),

        }, f'{path}/latest.pt')
        if episode % 50 == 0:
            torch.save({
                'episode': episode,
                'actor': self.actor.state_dict(),
                'critic': self.critic.state_dict(),
            }, f'{path}/ep{episode}.pt')
        print(f"Saved checkpoint at episode {episode}")

    def load(self, path=os.path.join(CHECKPOINT_DIR, 'latest.pt')):
        if os.path.exists(path):
            ckpt = torch.load(path, map_location=self.device)

            self.actor.load_state_dict(ckpt['actor'])
            self.critic.load_state_dict(ckpt['critic'])

            if 'actor_opt' in ckpt:
                self.actor_opt.load_state_dict(ckpt['actor_opt'])
            if 'critic_opt' in ckpt:
                self.critic_opt.load_state_dict(ckpt['critic_opt'])

            print(f"Resumed from episode {ckpt.get('episode', 0)}")
            return ckpt.get('episode', 0)
        return 0