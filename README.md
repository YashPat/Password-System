# Password Generation & Recovery System

A Python system that generates passwords using proof-of-work computation. Both password generation and recovery require the same computationally intensive operations (~15 hours), ensuring security through proof-of-work.

## Features

- **Proof-of-Work Security**: Both generation and recovery require expensive computation (~15 hours)
- **Hexadecimal Passwords**: Generate 15-character hexadecimal passwords (0-9, a-f)
- **Progress Tracking**: Real-time percentage display during computation
- **Deterministic**: Same seed and iterations always produce the same password
- **Hardware Calibration**: Automatically calibrates to your machine's performance

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the main script:
```bash
python main.py
```

### Mode 1: Generate New Password

1. Select option `1` from the menu
2. The system will:
   - Generate a random seed
   - Calibrate computation parameters for your hardware
   - Perform proof-of-work computation (~15 hours) to generate the password
   - Output the password and recovery keys
3. **Save the recovery keys securely** - you'll need them to recover the password

### Mode 2: Recover Password

1. Select option `2` from the menu
2. Paste your recovery keys (JSON format)
3. The system will:
   - Start the proof-of-work computation (~15 hours)
   - Show real-time percentage progress
   - Output the recovered password when complete

## How It Works

### Security Model
The system uses proof-of-work to ensure that passwords cannot be derived without performing the full computation. Both password generation and recovery require the same expensive computation, making it impossible to bypass the security mechanism.

### Generation Process
1. Generates a random 64-character hexadecimal seed (32 bytes)
2. Calibrates iteration count to target ~15 hours on your hardware
3. Performs iterative SHA-256 hashing (millions/billions of iterations)
4. Derives password from the final iterated hash (first 15 hex characters)
5. Outputs password + recovery keys (seed + iterations)

### Recovery Process
1. Takes recovery keys (seed + iterations) as input
2. Performs the same iterative SHA-256 hashing (proof-of-work)
3. Derives password from the final iterated hash
4. Shows real-time percentage progress during computation

### Password Format
Passwords are 15-character hexadecimal strings (0-9, a-f), derived directly from the hash output.

## Recovery Keys Format

The recovery keys are stored as JSON:
```json
{
  "seed": "hexadecimal_seed_string",
  "iterations": 1234567890
}
```

## Notes

- **Computation Time**: Both generation and recovery take approximately 15 hours (calibrated to your hardware)
- **Deterministic**: Same seed + iterations = same password
- **Security**: Password derivation requires the full proof-of-work computation - cannot be bypassed
- **Memory Efficient**: Constant memory usage regardless of iteration count
- **Progress Updates**: Progress percentage updates every 5 million iterations to minimize overhead
- **Keep Keys Secure**: Recovery keys can regenerate your password - store them securely
