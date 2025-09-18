classA <- c(5, 6, 4, 7, 8)
classB <- c(10, 7, 2, 9, 3)

mean_classA <- mean(classA)
mean_classB <- mean(classB)

cat("Mean of Class A:", mean_classA, "\n")
cat("Mean of Class B:", mean_classB, "\n")

if (mean_classA > mean_classB){
    cat("Class A has a higher mean.\n")
} else if (mean_classA < mean_classB){
    cat("Class B has a higher mean.\n")
} else {
    cat("Both classes have the same mean.\n")
}

