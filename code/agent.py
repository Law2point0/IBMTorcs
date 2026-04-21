'''import torch
import torch.nn as nn
import numpy as np
import os
from collections import deque

class A2CAgent:
    def __init__(self, actor, critic, device, gamma=0.95, lr_actor=1e-4, lr_critic=3e-4):
        self.actor = actor.to(device)
        self.critic = critic.to(device)
        self.device = device
        self.gamma = gamma
        self.std = 0.3

        self.actor_opt = torch.optim.Adam(actor.parameters(), lr=lr_actor)
        self.critic_opt = torch.optim.Adam(critic.parameters(), lr=lr_critic)

        # Learning rate schedulers - reduce by 5% every 50 episodes
        self.actor_scheduler = torch.optim.lr_scheduler.StepLR(
            self.actor_opt, step_size=50, gamma=0.95)
        self.critic_scheduler = torch.optim.lr_scheduler.StepLR(
            self.critic_opt, step_size=50, gamma=0.95)

        # Target critic for stable value estimates
        import copy
        self.target_critic = copy.deepcopy(critic).to(device)
        self.tau = 0.005  # soft update rate

        # Running reward normalisation
        self.reward_mean = 0.0
        self.reward_std = 1.0
        self.reward_count = 0

    def _normalise_reward(self, r):
        self.reward_count += 1
        self.reward_mean += (r - self.reward_mean) / self.reward_count
        self.reward_std = max(1.0, abs(r - self.reward_mean))
        return (r - self.reward_mean) / self.reward_std

    def _soft_update_target(self):
        for param, target_param in zip(
            self.critic.parameters(),
            self.target_critic.parameters()
        ):
            target_param.data.copy_(
                self.tau * param.data + (1 - self.tau) * target_param.data
            )

    def select_action(self, obs):
        obs_t = torch.FloatTensor(obs).unsqueeze(0).to(self.device)
        mean = self.actor(obs_t)
        dist = torch.distributions.Normal(mean, self.std)
        action = dist.sample()
        log_prob = dist.log_prob(action).sum(dim=1)

        with torch.no_grad():
            value = self.target_critic(obs_t)  # use target critic for stability

        action_np = action.detach().cpu().numpy().flatten()
        action_np[0] = np.clip(action_np[0], -1, 1)
        action_np[1] = np.clip(action_np[1], 0, 1)
        action_np[2] = np.clip(action_np[2], 0, 1)

        return action_np, log_prob, value

    def update(self, log_probs, values, rewards, obs_list):
        if len(rewards) < 2:
            return 0, 0

        # Normalise rewards
        normalised_rewards = [self._normalise_reward(r) for r in rewards]

        # Compute returns from normalised rewards
        returns = []
        R = 0
        for r in reversed(normalised_rewards):
            R = r + self.gamma * R
            returns.insert(0, R)

        returns = torch.tensor(returns, dtype=torch.float32).to(self.device)

        # Recompute values with gradients using main critic
        obs_t = torch.FloatTensor(np.array(obs_list)).to(self.device)
        values_t = self.critic(obs_t).squeeze()

        # Advantages using target critic for stability
        with torch.no_grad():
            target_values = self.target_critic(obs_t).squeeze()
        advantages = returns - target_values
        advantages = torch.clamp(advantages, -5.0, 5.0)

        # Recompute distribution for entropy
        mean = self.actor(obs_t)
        dist = torch.distributions.Normal(mean, self.std)
        entropy = dist.entropy().sum(dim=1).mean()

        # Actor loss with entropy bonus
        actor_loss = -(torch.stack(log_probs) * advantages).mean() - 0.01 * entropy

        # Critic loss
        critic_loss = nn.functional.mse_loss(values_t, returns)

        # Update actor
        self.actor_opt.zero_grad()
        actor_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.actor.parameters(), 0.5)
        self.actor_opt.step()

        # Update critic
        self.critic_opt.zero_grad()
        critic_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.critic.parameters(), 1.0)
        self.critic_opt.step()

        # Soft update target critic
        self._soft_update_target()

        return actor_loss.item(), critic_loss.item()
    
    def step_schedulers(self):
        """Call once per episode to decay learning rates."""
        self.actor_scheduler.step()
        self.critic_scheduler.step()

    def get_lr(self):
        return {
            'actor_lr': self.actor_opt.param_groups[0]['lr'],
            'critic_lr': self.critic_opt.param_groups[0]['lr']
        }

    def save(self, episode, path='checkpoints'):
        os.makedirs(path, exist_ok=True)
        torch.save({
            'episode': episode,
            'actor': self.actor.state_dict(),
            'critic': self.critic.state_dict(),
            'target_critic': self.target_critic.state_dict(),
            'actor_opt': self.actor_opt.state_dict(),
            'critic_opt': self.critic_opt.state_dict(),
            'reward_mean': self.reward_mean,
            'reward_std': self.reward_std,
            'reward_count': self.reward_count,
        }, f'{path}/latest.pt')
        if episode % 50 == 0:
            torch.save({
                'episode': episode,
                'actor': self.actor.state_dict(),
                'critic': self.critic.state_dict(),
            }, f'{path}/ep{episode}.pt')
        print(f"Saved checkpoint at episode {episode}")

    def load(self, path='checkpoints/latest.pt'):
        if os.path.exists(path):
            ckpt = torch.load(path, map_location=self.device)
            self.actor.load_state_dict(ckpt['actor'])
            self.critic.load_state_dict(ckpt['critic'])
            if 'target_critic' in ckpt:
                self.target_critic.load_state_dict(ckpt['target_critic'])
            else:
                import copy
                self.target_critic.load_state_dict(ckpt['critic'])
            if 'actor_opt' in ckpt:
                self.actor_opt.load_state_dict(ckpt['actor_opt'])
            if 'critic_opt' in ckpt:
                self.critic_opt.load_state_dict(ckpt['critic_opt'])
            if 'reward_mean' in ckpt:
                self.reward_mean = ckpt['reward_mean']
                self.reward_std = ckpt['reward_std']
                self.reward_count = ckpt['reward_count']
            print(f"Resumed from episode {ckpt.get('episode', 0)}")
            return ckpt.get('episode', 0)
        return 0
'''


import torch
import torch.nn as nn
import numpy as np
import os

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
        bias = torch.tensor([[0.0, bias_strength, -bias_strength]]).to(self.device)
        mean = mean + bias
        
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
        action_np[1] = np.clip(action_np[1], 0, 1)
        action_np[2] = np.clip(action_np[2], 0, 1)
        
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

    def load(self, path='checkpoints/latest.pt'):
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