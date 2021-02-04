import numpy as np


class LogisticPolicy:
    def __init__(self, params, lr, gamma):
        # Initialize paramters, learning rate and discount factor

        self.params = params
        self.lr = lr
        self.gamma = gamma

    def logistic(self, y):
        # definition of logistic function

        return 1 / (1 + np.exp(-y))

    def action_probs(self, x):
        # returns probabilities of two actions

        y = x @ self.params
        prob0 = self.logistic(y)

        return np.array([prob0, 1 - prob0])

    def act(self, x):
        # sample an action in proportion to probabilities

        probs = self.action_probs(x)
        action = np.random.choice([0, 1], p=probs)

        return action, probs[action]

    def grad_log_p(self, x):
        # calculate grad-log-probs

        y = np.dot(x, self.params)
        grad_log_p0 = x - x * self.logistic(y)
        grad_log_p1 = -x * self.logistic(y)

        return grad_log_p0, grad_log_p1

    def grad_log_p_dot_rewards(self, grad_log_p, actions, discounted_rewards):
        # dot grads with future rewards for each action in episode

        return np.dot(grad_log_p.T, discounted_rewards)

    def discount_rewards(self, rewards):
        # calculate temporally adjusted, discounted rewards

        discounted_rewards = np.zeros(len(rewards))
        cumulative_rewards = 0
        for i in reversed(range(0, len(rewards))):
            cumulative_rewards = cumulative_rewards * self.gamma + rewards[i]
            discounted_rewards[i] = cumulative_rewards

        return discounted_rewards

    def update(self, rewards, obs, actions):
        # calculate gradients for each action over all observations
        grad_log_p = np.array(
            [self.grad_log_p(ob)[action] for ob, action in zip(obs, actions)]
        )

        assert grad_log_p.shape == (len(obs), 4)

        # calculate temporaly adjusted, discounted rewards
        discounted_rewards = self.discount_rewards(rewards)

        # gradients times rewards
        dot = self.grad_log_p_dot_rewards(grad_log_p, actions, discounted_rewards)

        # gradient ascent on parameters
        self.params += self.lr * dot


def run_episode(env, policy, render=False):

    observation = env.reset()
    totalreward = 0

    observations = []
    actions = []
    rewards = []
    probs = []

    done = False

    while not done:
        if render:
            env.render()

        observations.append(observation)

        action, prob = policy.act(observation)
        observation, reward, done, info = env.step(action)

        totalreward += reward
        rewards.append(reward)
        actions.append(action)
        probs.append(prob)

    return (
        totalreward,
        np.array(rewards),
        np.array(observations),
        np.array(actions),
        np.array(probs),
    )


def train(
    env,
    params,
    lr,
    gamma,
    policy,
    MAX_EPISODES=1000,
    seed=None,
    evaluate=False,
    video_folder="",
):

    # initialize environment and policy
    if seed is not None:
        env.seed(seed)
    episode_rewards = []
    policy = policy(params, lr, gamma)

    # train until MAX_EPISODES
    import time

    for i in range(MAX_EPISODES):
        # time.sleep(0.1)
        # env.render()
        # run a single episode
        total_reward, rewards, observations, actions, probs = run_episode(env, policy)

        # keep track of episode rewards
        episode_rewards.append(total_reward)

        # update policy
        policy.update(rewards, observations, actions)
        print(
            "EP: " + str(i) + " Score: " + str(total_reward) + " ",
            end="\r",
            flush=False,
        )

    # evaluation call after training is finished - evaluate last trained policy on 100 episodes
    if evaluate:
        env = Monitor(
            env, video_folder, video_callable=True, force=True
        )
        for _ in range(100):
            run_episode(env, policy, render=False)
        env.env.close()

    return episode_rewards, policy


if __name__ == "__main__":
    # additional imports for saving and loading a trained policy
    import gym
    import gym.wrappers
    from gym.wrappers.monitor import Monitor, load_results

    # for reproducibility
    GLOBAL_SEED = 0
    np.random.seed(GLOBAL_SEED)
    env = gym.make("CartPole-v0")

    episode_rewards, policy = train(
        env,
        params=np.random.rand(4),
        lr=0.002,
        gamma=0.99,
        policy=LogisticPolicy,
        MAX_EPISODES=2000,
        seed=GLOBAL_SEED,
        evaluate=False,
        video_folder="Experiments/logistic_pg_cartpole/",
    )

    import matplotlib.pyplot as plt

    plt.plot(episode_rewards)
    plt.show()
