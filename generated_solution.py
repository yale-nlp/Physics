import sympy as sp
import pickle

# Step 1: Define the symbols used in the problem
alpha_1, alpha_2 = sp.symbols('alpha_1 alpha_2')  # Linear expansion coefficients
x = sp.symbols('x')  # Total thickness of the bimetallic strip
delta_T = sp.symbols('Delta_T')  # Temperature change
R = sp.symbols('R')  # Radius of curvature

# Step 2: Calculate the strain in each metal due to the temperature change
# Strain for metal 1
strain_1 = alpha_1 * delta_T

# Strain for metal 2
strain_2 = alpha_2 * delta_T

# Step 3: Calculate the difference in strain between the two metals
delta_strain = strain_2 - strain_1

# Step 4: Relate the change in strain to the curvature
# Using the approximation for small curvatures:
# delta_strain = (x / (2 * R))
R_solution = sp.solve(x / (2 * R) - delta_strain, R)

# Final result for the radius of curvature
R_curvature = R_solution[0]

# Step 5: Convert the result to a LaTeX formatted string
latex_result = sp.latex(R_curvature)

# Step 6: Save the result to a pickle file
with open('result.pkl', 'wb') as file:
    pickle.dump(latex_result, file)