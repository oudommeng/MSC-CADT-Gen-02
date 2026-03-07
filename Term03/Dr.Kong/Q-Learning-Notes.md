# Q-Learning Quiz Prep

## 1. Core Concept

Q-Learning = model-free, off-policy reinforcement learning algorithm.  
Agent learns optimal actions by trial and error — no prior knowledge of environment.

---

## 2. The Bellman Update (KEY FORMULA)

```
Q(s, a) ← Q(s, a) + α * [r + γ * max Q(s', a') - Q(s, a)]
```

| Symbol | Name | Meaning |
|--------|------|---------|
| `Q(s, a)` | Q-value | Expected future reward from state `s` taking action `a` |
| `α` (alpha) | Learning rate | How fast to update Q-values (0–1) |
| `r` | Reward | Immediate reward received |
| `γ` (gamma) | Discount factor | Weight of future rewards (0=greedy, 1=far-sighted) |
| `max Q(s', a')` | Best future Q | Best Q-value in next state `s'` |
| `[r + γ*max Q(s',a') - Q(s,a)]` | TD Error | How wrong the current estimate is |

**In code (line 47):**
```python
Q[state][action] = Q[state][action] + alpha * (reward + gamma * np.max(Q[next_state]) - Q[state][action])
```

---

## 3. Gridworld Environment

```
5×5 grid
Start: (0,0)  → top-left
Goal:  (4,4)  → bottom-right
```

### Actions (4 total)

| Code | Action | Effect |
|------|--------|--------|
| 0 | Up | `x - 1` (clamped to 0) |
| 1 | Right | `y + 1` (clamped to size-1) |
| 2 | Down | `x + 1` (clamped to size-1) |
| 3 | Left | `y - 1` (clamped to 0) |

### Reward
- Reach goal: `+1`
- Any other step: `-1`

---

## 4. Epsilon-Greedy Policy

```python
if np.random.rand() < epsilon:
    action = np.random.choice(4)   # EXPLORE (random)
else:
    action = np.argmax(Q[state])   # EXPLOIT (best known)
```

- `ε = 0.1` → 10% explore, 90% exploit
- Balances **exploration vs exploitation**

---

## 5. Q-Table Structure

```python
Q = np.zeros((env.size, env.size, 4))
# Shape: (5, 5, 4)
# Meaning: Q[row][col][action]
```

- One entry per (state, action) pair
- Initialized to zeros → agent has no knowledge at start
- Grows more accurate each episode

---

## 6. Algorithm Flow

```
for each episode:
    reset state to start (0,0)
    loop:
        pick action via ε-greedy
        take action → get (next_state, reward, done)
        update Q[state][action] via Bellman equation
        state = next_state
        if done: break
```

---

## 7. Hyperparameters (defaults)

| Param | Value | Effect if increased |
|-------|-------|---------------------|
| `alpha` | 0.1 | Learns faster but unstable |
| `gamma` | 0.9 | More weight on future rewards |
| `epsilon` | 0.1 | More random exploration |
| `episodes` | 1000 | More training = better Q-values |

---

## 8. Convergence

Q-Learning **converges** to optimal policy when:
1. All (state, action) pairs visited enough times
2. Learning rate `α` decays appropriately (or is small enough)
3. `γ < 1` (ensures finite total reward)

---

## 9. Visualization

`visualize_subplots()` runs ONE greedy episode (no randomness) after training:
```python
action = np.argmax(Q[state])  # always pick best action
```
Shows agent's path step-by-step across subplot grid.

---

## 10. Likely Quiz Questions

**Q: What does Q(s,a) represent?**  
Expected cumulative reward from state `s`, taking action `a`, then following optimal policy.

**Q: What is the TD error?**  
`r + γ * max Q(s', a') - Q(s, a)` — difference between estimated and target Q-value.

**Q: What happens when γ=0?**  
Agent only cares about immediate reward, ignores future.

**Q: What happens when γ=1?**  
Agent weighs all future rewards equally — may not converge if episodes are infinite.

**Q: What happens when ε=0?**  
Pure exploitation — agent never explores, may get stuck in suboptimal policy.

**Q: What happens when ε=1?**  
Pure exploration — agent always acts randomly, never exploits learned knowledge.

**Q: Why initialize Q to zeros?**  
Neutral start — no bias. Agent learns purely from experience.

**Q: What is off-policy learning?**  
Agent learns optimal policy (greedy) while behaving with different policy (ε-greedy).

**Q: What is the shape of Q in this code?**  
`(5, 5, 4)` → 5 rows × 5 cols × 4 actions = 100 entries.
