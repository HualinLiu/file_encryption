import os
import binascii
from docx import Document

def key_generator():
    return os.urandom(16)

def shift_rows(matrix):
    matrix[1] = matrix[1][1:] + matrix[1][:1]  # Shift second row by 1
    matrix[2] = matrix[2][2:] + matrix[2][:2]  # Shift third row by 2
    matrix[3] = matrix[3][3:] + matrix[3][:3]  # Shift fourth row by 3
    return matrix

def galois_mult(a, b):
    p = 0
    for i in range(8):
        if b & 1:
            p ^= a
        carry = a & 0x80
        a <<= 1
        if carry:
            a ^= 0x1b  # AES irreducible polynomial
        b >>= 1
    return p % 256

def mix_single_column(column):
    temp = column[:]
    column[0] = galois_mult(temp[0], 2) ^ galois_mult(temp[1], 3) ^ temp[2] ^ temp[3]
    column[1] = temp[0] ^ galois_mult(temp[1], 2) ^ galois_mult(temp[2], 3) ^ temp[3]
    column[2] = temp[0] ^ temp[1] ^ galois_mult(temp[2], 2) ^ galois_mult(temp[3], 3)
    column[3] = galois_mult(temp[0], 3) ^ temp[1] ^ temp[2] ^ galois_mult(temp[3], 2)

def mix_columns(matrix):
    for i in range(4):
        mix_single_column(matrix[i])
    return matrix

def add_round_key(matrix, round_key):
    for i in range(4):
        for j in range(4):
            matrix[i][j] ^= round_key[i][j]
    return matrix

def pad(data):
    padding_length = 16 - len(data) % 16
    return data + bytes([padding_length]) * padding_length

def aes_encrypt(block, key):
    # Convert the block (16 bytes) into a 4x4 matrix
    state = [list(block[i:i+4]) for i in range(0, 16, 4)]
    
    # Convert key to a 4x4 matrix (for simplicity)
    round_key = [list(key[i:i+4]) for i in range(0, 16, 4)]
    
    # Step 1: Add the round key
    state = add_round_key(state, round_key)
    
    # Step 2: Perform AES Rounds
    for round in range(9):  # Perform 9 rounds of transformation
        state = shift_rows(state)
        state = mix_columns(state)
        state = add_round_key(state, round_key)  # Reuse the key for simplicity
    
    # Final round: No MixColumns
    state = shift_rows(state)
    state = add_round_key(state, round_key)

    # Flatten the state matrix back into a 16-byte block
    encrypted_block = bytes(sum(state, []))  # Flatten the 4x4 matrix
    return encrypted_block

# Get the file path from user input
file_path = input("Please provide the path to the input file: ")

# Initialize the Word document
output_file_path = "encrypted_output_file.docx"
doc = Document()


# Open the file in binary read mode and output file in binary write mode
with open(file_path, 'rb') as fp:
    while True:
        block = fp.read(16)
        if not block:
            print("End of file reached.")
            break
        print(f"Processing block of size {len(block)} bytes")
        
        # If the block is less than 16 bytes, it's the last block. Pad it and stop further reading
        if len(block) < 16:
            block = pad(block)
            encrypted_block = aes_encrypt(block, key_generator())
            out_fp.write(encrypted_block)
            break  # End the loop after processing the last block
        
        # Encrypt the block
        encrypted_block = aes_encrypt(block, key_generator())
        
        # Write the encrypted block (in hex format) to the Word document
        doc.add_paragraph(binascii.hexlify(encrypted_block).decode('utf-8'))
        
        print(f"Processed block (encrypted and written): {binascii.hexlify(encrypted_block).decode()}")

doc.save(output_file_path)
print(f"Encryption complete. Encrypted file saved to {output_file_path}")
