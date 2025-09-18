# --- Define the Data ---
# Let X be the variable for the statistics score.
# The data is a realization of X.
X <- c(7, 8, 9, 5, 7, 8, 7, 9, 6, 8)

# --- a. Calculate the average score ---
# Use the built-in mean() function.
average_score <- mean(X)
cat("a. The average score is:", average_score, "\n\n")

# --- b. Construct the frequency table with x, f, xf ---
freq_table <- table(X)

scores <- as.numeric(names(freq_table))
frequencies <- as.numeric(freq_table)
xf <- scores * frequencies

freq_table_matrix <- cbind(x = scores, f = frequencies, xf = xf)
cat("b. Frequency table (x | f | xf):\n")
print(freq_table_matrix)
cat("\n")

# --- c. Calculate the mean from the frequency table ---
# This demonstrates the weighted average formula for the mean.
# Extract unique scores and their corresponding frequencies.
scores <- as.numeric(names(freq_table))
frequencies <- as.numeric(freq_table)

# Apply the formula: sum(score * frequency) / total_observations
mean_from_freq <- sum(scores * frequencies) / sum(frequencies)
cat("c. The mean calculated from the frequency table is:", mean_from_freq, "\n\n")

# --- d. Calculate the sum of deviations from the mean ---
# The formula is sum(X_i - mean(X)).
sum_of_deviations <- sum(X - average_score)
cat("d. The sum of deviations from the mean is:", sum_of_deviations, "\n")
cat("   Interpretation: The result of 0 shows that the mean is the 'balancing point' of the data.\n")