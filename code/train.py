import torch
import numpy as np
from env import TorcsEnv
from actor import Actor
from critic import Critic
from agent import A2CAgent

def train():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Training on: {device}")

    env = TorcsEnv(host='localhost', port=3001)
    actor = Actor(obs_dim=29, action_dim=3)
    critic = Critic(obs_dim=29)
    agent = A2CAgent(actor, critic, device)

    # starts from exisiting checkpoint
    start_ep = agent.load()

    episode_history = []

    for episode in range(start_ep, 10000):
        obs = env.reset()


        done = False
        log_probs, values, rewards = [], [], []
        total_reward = 0
        step = 0

        obs_list = []
        reason = 'unknown'

        while not done:
            obs_list.append(obs)  # store obs before step
            action, log_prob, value = agent.select_action(obs, episode)
            obs, reward, done, reason = env.step(action)
            log_probs.append(log_prob)
            values.append(value)
            rewards.append(reward)
            total_reward += reward
            step += 1

            if step < 10 and episode < start_ep + 3:
                S = env.client.S.d
                print(f"  [DEBUG] speed={S.get('speedX',0):.1f} "
                f"rpm={S.get('rpm',0):.0f} "
                f"steer={action[0]:.3f} "
                f"accel={action[1]:.3f} "
                f"brake={action[2]:.3f} ")

        actor_loss, critic_loss = agent.update(log_probs, values, rewards, obs_list)


        episode_history.append({
            'episode': episode,
            'reward': total_reward,
            'steps': step,
            'reason': reason
        })


        #print(f"  [DEBUG] gear={env.client.R.d.get('gear')} clutch={env.client.R.d.get('clutch')}")
        
        done, reason = env._is_done()
        if done:
            S = env.client.S.d
            print(f"[TERM] reason={reason} "
                f"trackPos={S.get('trackPos',0):.3f} "
                f"angle={S.get('angle',0):.3f} "
                f"speed={S.get('speedX',0):.1f} "
                f"distRaced={S.get('distRaced',0):.1f}")

        print(f"\nEpisode {episode} | "
              f"Steps: {step} | "
              f"Reward: {total_reward:.2f} | "
              f"End: {reason} | "
              f"Actor loss: {actor_loss:.8f} | "
              f"Critic loss: {critic_loss:.4f}")

        # Progress report every 10 episodes
        if episode % 10 == 0 and len(episode_history) >= 10:
            recent = episode_history[-10:]
            avg_reward = sum(e['reward'] for e in recent) / 10
            avg_steps = sum(e['steps'] for e in recent) / 10
            print(f"\n{'='*50}")
            print(f"  Progress Report - Episode {episode}")
            print(f"  Avg reward (last 10): {avg_reward:.2f}")
            print(f"  Avg steps  (last 10): {avg_steps:.1f}")
            print(f"  Best reward all time: {max(e['reward'] for e in episode_history):.2f}")
            print(f"{'='*50}\n")

        agent.save(episode)

if __name__ == '__main__':
    train()