from crossword_generator import generate_crossword

# This will generate a 5x5 crossword using default settings
# and print the result to your console.
result = generate_crossword(num_rows=5, num_cols=5)

# The 'result' is a CrosswordState object. 
# You can print the grid directly:
print(result)