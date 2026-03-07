
import cv2
import sys

# Load the image
filename = 'fruit2.jpg'
readimg = cv2.imread(filename)

# Check if image is loaded successfully
if readimg is None:
    print(f"Error: Could not open load image '{filename}'. Please check if the file exists.")
    sys.exit(1)

print(f"Successfully loaded '{filename}' with shape: {readimg.shape}")

# Define masks
maskSobelX = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
maskSobelY = [[1, 2, 1], [0, 0, 0], [-1, -2, -1]]

# Get dimensions
height, width, channel = readimg.shape

# Initialize output image
mOutImg = readimg.copy() * 0

# Initialize temporary lists for results (using flattened lists for performance similiar to original)
# We need to store the raw calculated values (which can be large/negative) before normalization.
pTmpXB = [0] * (width * height)
pTmpXG = [0] * (width * height)
pTmpXR = [0] * (width * height)
pTmpYB = [0] * (width * height)
pTmpYG = [0] * (width * height)
pTmpYR = [0] * (width * height)

print("Applying Sobel Masks...")

# 1. Apply Mask (Convolution)
for i in range(1, height - 1):
    for j in range(1, width - 1):
        newValueBx = 0; newValueGx = 0; newValueRx = 0
        newValueBy = 0; newValueGy = 0; newValueRy = 0
        
        # Convolve 3x3
        for mr in range(3):
            for mc in range(3):
                # Image pixel I(i+mc-1, j+mr-1). Note: Original code swapped mc/mr indexing match.
                # Let's align with typical correlation: center is (i, j).
                # mr is row offset (0,1,2) -> -1, 0, +1
                # mc is col offset (0,1,2) -> -1, 0, +1
                # To match the original snippet's logic exactly:
                # r,g,b = readimg[i+mc-1,j+mr-1]
                # maskSobelX[mr][mc]
                
                b, g, r = readimg[i + mc - 1, j + mr - 1] # OpenCV uses BGR by default
                
                # Careful with types, ensure calculations are integers/floats not uint8 overflow
                b = int(b); g = int(g); r = int(r)
                
                maskValX = maskSobelX[mr][mc]
                maskValY = maskSobelY[mr][mc]
                
                newValueBx += maskValX * b
                newValueGx += maskValX * g
                newValueRx += maskValX * r
                
                newValueBy += maskValY * b
                newValueGy += maskValY * g
                newValueRy += maskValY * r
                
        # Store results in flat arrays
        idx = i * width + j
        pTmpXB[idx] = newValueBx
        pTmpXG[idx] = newValueGx
        pTmpXR[idx] = newValueRx
        
        pTmpYB[idx] = newValueBy
        pTmpYG[idx] = newValueGy
        pTmpYR[idx] = newValueRy

print("Calculating Gradient Magnitude...")

# 2. Calculate Gradient Magnitude (L1 Norm: |Gx| + |Gy|) and combine
# Reuse pTmpX arrays to store the final combined magnitude magnitude to save memory/steps
for i in range(1, height - 1):
    for j in range(1, width - 1):
        idx = i * width + j
        
        # Absolute values
        gx_b = abs(pTmpXB[idx])
        gx_g = abs(pTmpXG[idx])
        gx_r = abs(pTmpXR[idx])
        
        gy_b = abs(pTmpYB[idx])
        gy_g = abs(pTmpYG[idx])
        gy_r = abs(pTmpYR[idx])
        
        # Combine
        pTmpXB[idx] = gx_b + gy_b
        pTmpXG[idx] = gx_g + gy_g
        pTmpXR[idx] = gx_r + gy_r

print("Finding Min/Max for Normalization...")

# 3. Find global min and max for each channel to normalize
# Initialize with limits
minB = minG = minR = float('inf')
maxB = maxG = maxR = float('-inf')

for i in range(1, height - 1):
    for j in range(1, width - 1):
        idx = i * width + j
        
        valB = pTmpXB[idx]
        valG = pTmpXG[idx]
        valR = pTmpXR[idx]
        
        if valB < minB: minB = valB
        if valB > maxB: maxB = valB
        
        if valG < minG: minG = valG
        if valG > maxG: maxG = valG
        
        if valR < minR: minR = valR
        if valR > maxR: maxR = valR

print(f"B: [{minB}, {maxB}], G: [{minG}, {maxG}], R: [{minR}, {maxR}]")

# 4. Calculate Normalization Constants
# Formula: result = (value - min) * (255 / (max - min))
# This scales the range [min, max] to [0, 255]

def get_norm_constants(min_val, max_val):
    if max_val == min_val:
        return 0.0, 0.0 # Avoid division by zero if image is flat color
    scale = 255.0 / (max_val - min_val)
    offset = -min_val * scale # This is equivalent to: -255 * min / (max - min)
    return scale, offset

scaleB, offsetB = get_norm_constants(minB, maxB)
scaleG, offsetG = get_norm_constants(minG, maxG)
scaleR, offsetR = get_norm_constants(minR, maxR)

print("Applying Normalization to Output Image...")

# 5. Apply Normalization and Write to Output
for i in range(1, height - 1):
    for j in range(1, width - 1):
        idx = i * width + j
        
        # Calculate new normalized values
        newB = pTmpXB[idx] * scaleB + offsetB
        newG = pTmpXG[idx] * scaleG + offsetG
        newR = pTmpXR[idx] * scaleR + offsetR
        
        # Clamping is technically not needed if math is perfect, but good for safety
        # Casting to int truncates
        mOutImg[i, j] = [int(newB), int(newG), int(newR)]

print("Done.")

# Display results
cv2.imshow("Original", readimg)
cv2.imshow("Sobel Edge Detection", mOutImg)

print("Press any key to close windows...")
cv2.waitKey(0)
cv2.destroyAllWindows()
