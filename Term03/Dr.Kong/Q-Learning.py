import numpy as np
import matplotlib.pyplot as plt

# Gridworld class
class Gridworld:
    def __init__(self, size, start, goal):
        self.size = size
        self.start = start
        self.goal = goal
        self.state = start
    
    def reset(self):
        self.state = self.start
        return self.state
    
    def step(self, action):
        x, y = self.state
        if action == 0:  # up
            x = max(0, x - 1)
        elif action == 1:  # right
            y = min(self.size - 1, y + 1)
        elif action == 2:  # down
            x = min(self.size - 1, x + 1)
        elif action == 3:  # left
            y = max(0, y - 1)
        
        self.state = (x, y)
        reward = 1 if self.state == self.goal else -1
        done = self.state == self.goal
        return self.state, reward, done

# Q-Learning function
def q_learning(env, alpha=0.1, gamma=0.9, epsilon=0.1, episodes=1000):
    Q = np.zeros((env.size, env.size, 4))
    for episode in range(episodes):
        state = env.reset()
        while True:
            if np.random.rand() < epsilon:
                action = np.random.choice(4)
            else:
                action = np.argmax(Q[state])
            
            next_state, reward, done = env.step(action)
            # Write the formula here
            # You can review the formula from the lesson
            Q[state][action] = Q[state][action] + alpha * (reward + gamma * np.max(Q[next_state]) - Q[state][action])
            state = next_state
            if done:
                break
    return Q

# Subplots visualization
def visualize_subplots(env, Q):
    # Run a single episode to collect the path
    state = env.reset()
    path = [state]
    while True:
        action = np.argmax(Q[state])
        next_state, _, done = env.step(action)
        path.append(next_state)
        state = next_state
        if done:
            break
    
    # Create subplots
    n_moves = len(path)
    cols = 5  # Number of columns in the subplot grid
    rows = (n_moves + cols - 1) // cols  # Calculate required rows

    fig, axes = plt.subplots(rows, cols, figsize=(cols * 2, rows * 2))
    axes = axes.flatten()

    for i, ax in enumerate(axes):
        ax.set_xlim(-0.5, env.size - 0.5)
        ax.set_ylim(-0.5, env.size - 0.5)
        ax.set_xticks(range(env.size))
        ax.set_yticks(range(env.size))
        ax.grid()
        ax.set_title(f"Step {i}" if i < n_moves else "")
        
        if i < n_moves:
            # Plot the grid
            ax.text(env.goal[1], env.goal[0], 'Goal', color='green', ha='center', va='center', fontsize=8)
            ax.plot(path[i][1], path[i][0], 'ro', markersize=8)
        
        else:
            # Hide unused subplots
            ax.axis('off')
    
    plt.tight_layout()
    plt.show()

# Main execution
env = Gridworld(5, (0, 0), (4, 4))
Q = q_learning(env)
print("Q-Values:\n")
print(Q)
visualize_subplots(env, Q)