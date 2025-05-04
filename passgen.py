import re
import sys
from sys import exit
import os
import time
import multiprocessing
from itertools import product
import tempfile
import random

# Global variables
args = None
output_path = None
verbose = False

def show_logo():
    print("""
  _____               _____            
 |  __ \\             / ____|           
 | |__) |_ _ ___ ___| |  __  ___ _ __  
 |  ___/ _` / __/ __| | |_ |/ _ \\ '_ \\ 
 | |  | (_| \\__ \\__ \\ |__| |  __/ | | |
 |_|   \\__,_|___/___/\\_____|\\__|_| |_|
                                       
    """)
    print(" A rules-based tool for generating passwords and wordlists | Author: @devsaeedz (Github)")
    print(" Version: 1.0")
    print("\n")

def show_help():
    print("\n Usage: ")
    print("\t passgen.py [options] <RULES> [OUTPUT_FILE_PATH]")
    
    print("\n Options:")
    print("\t -p N\t\tUse N processes for parallel processing (default: CPU count)")
    print("\t -s, --show-passwords\tPrint generated passwords to console (default: disabled)")
    print("\t -v, --verbose\tShow detailed information during execution")
    print("\t -y, --yes\tSkip confirmation and start generating immediately")
    print("\t -w, --wordlist-dir\tSpecify directory to search for wordlist files")
    print("\t -h, --help\tShow this help message and exit")
    
    print("\n Rule Syntax:")
    print("\t Regular: ['a','b']['1','2'] - Generates: a1, a2, b1, b2")
    print("\t Range: ['a..c']['0..2'] - Generates: a0, a1, a2, b0, b1, b2, c0, c1, c2")
    print("\t Wordlist: [wordlist:filename.txt]['!'] - Uses each line from file as an option")
    
    print("\n Notes:")
    print("\t - Range notation supports only alphanumeric characters (a-z, A-Z, 0-9)")
    print("\t - Wordlist files are searched in: specified dir, current dir, script dir")
    print("\t - At least one output method (file or -s) must be specified")
    print("\t - Full paths are supported on both Windows and Linux systems")
    
    print("\n Example Usages: ")
    print("\t passgen.py \"['p']['a']['s']['s']['w']['o']['r']['d']\"")
    print("\t passgen.py \"['p','P']['a','A','@']['s','S', '$']['s','S','$']['w','W']['o','O','0']['r','R']['d','D']\"")
    print("\t passgen.py \"['a..c']['0..5'][2..3]\" output.txt")
    print("\t passgen.py -s -y \"[wordlist:common_passwords.txt]['!','@','#']\"")
    print("\t passgen.py -p 8 -w wordlists \"[wordlist:custom.txt]['0..9']\" results.txt")
    print("\t passgen.py \"[wordlist:C:/path/to/wordlists/common.txt]['!']\"")
    print("\t passgen.py \"[wordlist:/home/user/wordlists/common.txt]['!']\"")
    print("\n")
    exit(0)


def f(p,t):
    r = re.findall(p,t)
    if not r or len(r) == 0:
        return None
    else:
        return r


def filter_char(s):
    s = s.replace("\\'","'")
    return s


def validate_range(start, end):
    if not (start.isalnum() and end.isalnum()):
        return False, "Range notation only supports alphanumeric characters (a-z, A-Z, 0-9)"
    
    if start.isdigit() and end.isdigit():
        # Both are digits, valid
        return True, None
    elif start.isalpha() and end.isalpha():
        # Both are letters, check if they're the same case
        if start.islower() and end.islower():
            return True, None
        elif start.isupper() and end.isupper():
            return True, None
        else:
            return False, "Start and end characters must be the same case (both uppercase or both lowercase)"
    else:
        # Mixed types
        return False, "Start and end must be same type (both digits or both letters)"


def expand_range_notation(char_option):
    # Check if it's a range pattern with or without quotes
    range_match = re.match(r'[\'"]?(\w)\.\.(\w)[\'"]?$', char_option)
    if range_match:
        start, end = range_match.groups()
        
        # Validate the range
        is_valid, error_msg = validate_range(start, end)
        if not is_valid:
            print(f"Error in range {start}..{end}: {error_msg}")
            exit(1)
            
        if start.isdigit() and end.isdigit():
            # Numeric range
            return [str(i) for i in range(int(start), int(end) + 1)]
        elif start.isalpha() and end.isalpha() and len(start) == 1 and len(end) == 1:
            # Alphabetic range
            return [chr(i) for i in range(ord(start), ord(end) + 1)]
    # Return as is if not a range
    return [char_option]


def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def load_wordlist(wordlist_path, wordlist_dir=None):
    global verbose
    words = []
    try:
        # Check if path is absolute
        if os.path.isabs(wordlist_path):
            full_path = wordlist_path
            
            # If doesn't exist, return empty
            if not os.path.exists(full_path):
                print(f"Warning: Wordlist file not found: {wordlist_path}")
                return words
        else:
            
            if wordlist_dir and os.path.exists(os.path.join(wordlist_dir, wordlist_path)):
                full_path = os.path.join(wordlist_dir, wordlist_path)
            elif os.path.exists(wordlist_path):
                full_path = wordlist_path
            else:
                # Try relative to script location
                script_dir = os.path.dirname(os.path.abspath(__file__))
                full_path = os.path.join(script_dir, wordlist_path)
                
                # If still doesn't exist, return empty
                if not os.path.exists(full_path):
                    print(f"Warning: Wordlist file not found: {wordlist_path}")
                    print(f"Searched in: current directory, {wordlist_dir or 'no wordlist dir specified'}, and {script_dir}")
                    return words
        
        if verbose:
            print(f"Reading wordlist from: {full_path}")
            
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                word = line.strip()
                if word:  # Skip empty lines
                    words.append(word)
        
        if verbose:
            print(f"Loaded {len(words)} words from {wordlist_path}")
            
        if not words:
            print(f"Warning: No words found in wordlist file: {wordlist_path}")
    except Exception as e:
        print(f"Error loading wordlist {wordlist_path}: {e}")
    
    return words


def parseRules(t, wordlist_dir=None):
    rules_arr = []
    # Look for both quoted and unquoted range patterns in brackets
    bracket_pattern = r'\[(.*?)\]'
    brackets = re.findall(bracket_pattern, t)
    
    if not brackets:
        print('No Rules or malformed, Terminated!')
        exit(0)
    
    for bracket_content in brackets:
        rule_arr = []
        
        # Check for wordlist notation: wordlist:filename.txt
        wordlist_match = re.match(r'wordlist:(.+)$', bracket_content.strip())
        if wordlist_match:
            # Extract filename from the match
            wordlist_file = wordlist_match.group(1).strip()
            # Load words from wordlist
            words = load_wordlist(wordlist_file, wordlist_dir)
            if words:
                rule_arr.extend(words)
            else:
                print(f"Error: No valid words found in wordlist: {wordlist_file}")
                exit(1)
        # Check for range notation without quotes
        elif re.match(r'(\S)\.\.(\S)$', bracket_content):
            # Direct range notation without quotes: [0..9]
            start, end = re.match(r'(\S)\.\.(\S)$', bracket_content).groups()
            
            # Validate the range characters
            is_valid, error_msg = validate_range(start, end)
            if not is_valid:
                print(f"Error in range [{start}..{end}]: {error_msg}")
                exit(1)
                
            if start.isdigit() and end.isdigit():
                for i in range(int(start), int(end) + 1):
                    rule_arr.append(str(i))
            elif start.isalpha() and end.isalpha():
                for i in range(ord(start), ord(end) + 1):
                    rule_arr.append(chr(i))
        else:
            # Standard quoted characters: ['a','b']
            char_matches = re.findall(r"'([^'\\]*(?:\\.[^'\\]*)*)'", bracket_content)
            if char_matches:
                for char in char_matches:
                    cleaned_char = filter_char(char)
                    # Check if it's a range notation inside quotes
                    range_match = re.match(r'(\S)\.\.(\S)$', cleaned_char)
                    if range_match:
                        start, end = range_match.groups()
                        
                        # Validate the range characters
                        is_valid, error_msg = validate_range(start, end)
                        if not is_valid:
                            print(f"Error in range '{start}..{end}': {error_msg}")
                            exit(1)
                            
                        if start.isdigit() and end.isdigit():
                            for i in range(int(start), int(end) + 1):
                                rule_arr.append(str(i))
                        elif start.isalpha() and end.isalpha():
                            for i in range(ord(start), ord(end) + 1):
                                rule_arr.append(chr(i))
                    else:
                        rule_arr.append(cleaned_char)
        
        if rule_arr:
            rules_arr.append(rule_arr)
    
    if not rules_arr:
        print('Failed to parse any rules. Terminated!')
        print(f'Debug - Input: {t}')
        print(f'Debug - Brackets found: {brackets}')
        exit(0)
    
    return rules_arr


# Worker process function
def worker_process(chunk_index, rules_arr, total_chunks, output_file):
    # Generate all index combinations
    ranges = [range(len(rule)) for rule in rules_arr]
    all_combinations = list(product(*ranges))
    
    # Determine chunk size and range
    chunk_size = max(1, len(all_combinations) // total_chunks)
    start_idx = chunk_index * chunk_size
    end_idx = min(start_idx + chunk_size, len(all_combinations))
    
    # Process only this chunk's combinations
    chunk_combinations = all_combinations[start_idx:end_idx]
    
    # Generate passwords for this chunk
    with open(output_file, 'w') as f:
        for combination in chunk_combinations:
            s = ''
            for i, char_index in enumerate(combination):
                s += rules_arr[i][char_index]
            f.write(f"{s}\n")


def calculate_combinations_and_size(rules_arr):
    # Calculate total combinations
    total_combinations = 1
    for rule in rules_arr:
        total_combinations *= len(rule)
    
    # If the number of combinations is small, generate actual passwords for exact calculation
    if total_combinations <= 1000:
        total_size = 0
        ranges = [range(len(rule)) for rule in rules_arr]
        for combination in product(*ranges):
            password = ''
            for i, char_index in enumerate(combination):
                password += rules_arr[i][char_index]
            # Add 1 for newline character
            total_size += len(password) + 1
        
        avg_password_length = total_size / total_combinations
        estimated_size = total_size
    else:
        # For large combinations, use sampling to estimate size more accurately
        # Sample size is the square root of total combinations, capped at 1000
        sample_size = min(int(total_combinations ** 0.5), 1000)
        
        # Generate random samples
        total_sample_length = 0
        
        for _ in range(sample_size):
            # Generate random indices for each position
            random_combination = [random.choice(range(len(rule))) for rule in rules_arr]
            
            password = ''
            for i, char_index in enumerate(random_combination):
                password += rules_arr[i][char_index]
            
            total_sample_length += len(password)
        
        avg_password_length = total_sample_length / sample_size
        
        line_ending_size = 1.1  
        estimated_size = int(total_combinations * (avg_password_length + line_ending_size))
    
    return total_combinations, estimated_size, round(avg_password_length)


def generatePasswordsMultiprocess(rules_arr, num_processes, show_passwords=False, verbose=False, skip_confirmation=False):
    # Calculate combinations and estimated size
    total_combinations, estimated_size, avg_length = calculate_combinations_and_size(rules_arr)
    
    # Show confirmation prompt
    print("\n=== Password Generation Summary ===")
    print(f"Total combinations: {total_combinations:,}")
    print(f"Average password length: ~{avg_length} characters")
    print(f"Estimated output size: {format_size(estimated_size)}")
    
    if output_path:
        print(f"Output file: {output_path}")
    
    # Check for very large outputs
    if estimated_size > 1024 * 1024 * 1024:  # 1 GB
        print("\nWARNING: The estimated file size is very large!")
        print("This may take a long time and consume significant disk space.")
    
    if not skip_confirmation:
        try:
            input("\nPress ENTER to start generating or Ctrl+C to abort...")
        except KeyboardInterrupt:
            print("\nOperation aborted by user.")
            exit(0)
    
    start_time = time.time()
    
    # Debug information
    if verbose:
        print("\nRules array:")
        for i, rule in enumerate(rules_arr):
            print(f"  Position {i+1}: {rule}")
    
    # Limit processes based on combinations
    actual_processes = min(num_processes, total_combinations, 64)  # Cap at 64 processes max
    
    print(f"\nGenerating passwords using {actual_processes} processes...")
    if not show_passwords:
        print("Password display is disabled. Use --show-passwords to view passwords in real-time.")
    
    # Create temporary files for each process
    temp_files = []
    for i in range(actual_processes):
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt')
        temp_file.close()
        temp_files.append(temp_file.name)
    
    if verbose:
        print(f"Created {len(temp_files)} temporary files for worker processes")
    
    # Start worker processes
    processes = []
    for i in range(actual_processes):
        p = multiprocessing.Process(
            target=worker_process, 
            args=(i, rules_arr, actual_processes, temp_files[i])
        )
        processes.append(p)
        p.start()
        if verbose:
            print(f"Started process {i+1}/{actual_processes}")
    
    # Wait for all processes to complete
    for i, p in enumerate(processes):
        p.join()
        if verbose:
            print(f"Process {i+1}/{actual_processes} completed")
    
    if verbose:
        print("All processes completed, collecting results...")
    
    # Collect results from temp files
    password_count = 0
    if output_path:
        # First collect all passwords from temp files
        all_passwords = []
        for temp_file in temp_files:
            try:
                with open(temp_file, 'r') as f:
                    for line in f:
                        password = line.strip()
                        if password:
                            all_passwords.append(password)
                # Clean up
                os.unlink(temp_file)
                if verbose:
                    print(f"Processed and removed temporary file: {temp_file}")
            except Exception as e:
                print(f"Warning: Error reading temp file {temp_file}: {e}")
        
        # Then write all passwords to output file using binary mode to control line endings precisely
        with open(output_path, 'wb') as out_file:
            for idx, password in enumerate(all_passwords):
                if show_passwords:
                    print(password)
                
                # Write the password
                out_file.write(password.encode('utf-8'))
                
                # Add newline except after the last password
                if idx < len(all_passwords) - 1:
                    out_file.write(b'\n')  # Using binary mode for precise control
                
                password_count += 1
    else:
        for temp_file in temp_files:
            try:
                with open(temp_file, 'r') as f:
                    for line in f:
                        password = line.strip()
                        if password:
                            if show_passwords:
                                print(password)
                            password_count += 1
                # Clean up
                os.unlink(temp_file)
                if verbose:
                    print(f"Processed and removed temporary file: {temp_file}")
            except Exception as e:
                print(f"Warning: Error reading temp file {temp_file}: {e}")
    
    elapsed_time = time.time() - start_time
    print(f"\nGenerated {password_count:,} passwords in {elapsed_time:.2f} seconds using {actual_processes} processes")
    if output_path:
        actual_size = os.path.getsize(output_path)
        print(f"Results saved to: {output_path} ({format_size(actual_size)})")


def main():
    # Always display logo and tool name
    show_logo()
    
    # Check for help flag first
    if len(sys.argv) == 1 or '-h' in sys.argv or '--help' in sys.argv:
        show_help()
    
    # Parse command-line arguments
    process_count = multiprocessing.cpu_count()  # Default to CPU count
    show_passwords = False
    local_verbose = False
    skip_confirmation = False
    wordlist_dir = None
    
    # Process arguments
    args_list = sys.argv[1:]
    processed_args = []
    
    i = 0
    while i < len(args_list):
        arg = args_list[i]
        
        if arg == '-h' or arg == '--help':
            # Skip these as they're handled earlier
            i += 1
        elif arg == '-p' and i+1 < len(args_list):
            try:
                process_count = int(args_list[i+1])
                i += 2
            except ValueError:
                print(f"Invalid process count. Using default ({process_count}).")
                i += 2
        elif arg == '-s' or arg == '--show-passwords':
            show_passwords = True
            i += 1
        elif arg == '-v' or arg == '--verbose':
            local_verbose = True
            i += 1
        elif arg == '-y' or arg == '--yes':
            skip_confirmation = True
            i += 1
        elif (arg == '-w' or arg == '--wordlist-dir') and i+1 < len(args_list):
            wordlist_dir = args_list[i+1]
            if not os.path.isdir(wordlist_dir):
                print(f"Warning: Wordlist directory does not exist: {wordlist_dir}")
                print("Will search in current directory and script directory instead.")
                wordlist_dir = None
            i += 2
        else:
            processed_args.append(arg)
            i += 1
    
    if not processed_args:
        print("Missing password rules argument.")
        exit(1)
    
    global args, output_path, verbose
    args = processed_args[0]
    output_path = processed_args[1] if len(processed_args) > 1 else ''
    verbose = local_verbose
    
    # Ensure that either show_passwords is enabled or an output file is specified
    if not show_passwords and not output_path:
        print("Error: You must either enable password display (-s, --show-passwords) or specify an output file.")
        print("Use passgen.py --help for more information.")
        exit(1)
    
    # Parse rules and generate passwords
    rules = parseRules(args, wordlist_dir)
    generatePasswordsMultiprocess(rules, process_count, show_passwords, verbose, skip_confirmation)


if __name__ == '__main__':
    # Add freeze_support for Windows
    multiprocessing.freeze_support()
    main()