import re
import sys
import os
import time
import multiprocessing
from itertools import product
import tempfile
import random


def show_logo():
    print("""
  _____               _____            
 |  __ \\             / ____|           
 | |__) |_ _ ___ ___| |  __  ___ _ __  
 |  ___/ _` / __/ __| | |_ |/ _ \\ '_ \\ 
 | |  | (_| \\__ \\__ \\ |__| |  __/ | | |
 |_|   \\__,_|___/___/\\_____|\\__|_| |_|
                                       
    """)
    print("\n A rules-based tool for generating passwords and wordlists | Author: @devsaeedz (Github)")


def show_help():
    """Show help information"""
    print("\n Usage: ")
    print("\t passgen.py [options] <RULES> [OUTPUT_FILE_PATH]")
    print("\n Options:")
    print("\t -p N\t\tUse N processes for parallel processing (default: CPU count)")
    print("\t -s, --show-passwords\tPrint generated passwords to console (default: disabled)")
    print("\t -v, --verbose\tShow detailed information during execution")
    print("\t -y, --yes\tSkip confirmation and start generating immediately")
    print("\n Example Usages: ")
    print("\t passgen.py \"['p']['a']['s']['s']['w']['o']['r']['d']\"")
    print("\t passgen.py \"['p','P']['a','A']['s','S']['s','S']['w','W']['o','O']['r','R']['d','D']\"")
    print("\t passgen.py \"['p','P']['a','A','@']['s','S','$']['s','S','$']['w','W']['o','O','0']['r','R']['d','D']\"")
    print("\t passgen.py -p 8 \"['p','P']['a','A']['s','S']['s','S']['w','W']['o','O']['r','R']['d','D']\"")
    print("\t passgen.py -p 16 -v --show-passwords \"['p','P']['a','A']['s','S']['s','S']['w','W']['o','O']['r','R']['d','D']\" passwords.txt")
    print("\n Range Notation:")
    print("\t passgen.py \"['a..c']['0..5'][2..3]\"  # Quotes are optional")
    print("\t Note: Range notation only supports alphanumeric characters (a-z, A-Z, 0-9)")
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


def parseRules(t):
    rules_arr = []
    # Look for both quoted and unquoted range patterns in brackets
    bracket_pattern = r'\[(.*?)\]'
    brackets = re.findall(bracket_pattern, t)
    
    if not brackets:
        print('No Rules or malformed, Terminated!')
        exit(0)
    
    for bracket_content in brackets:
        rule_arr = []
        
        # Check for range notation without quotes
        range_match = re.match(r'(\S)\.\.(\S)$', bracket_content)
        if range_match:
            # Direct range notation without quotes: [0..9]
            start, end = range_match.groups()
            
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
        
        # Add 1 for newline character and adjust for system file representation
        # Windows uses CRLF which is 2 bytes, Unix uses LF which is 1 byte
        # Use 1.1 as a correction factor based on the observed data
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
        with open(output_path, 'w') as out_file:
            for temp_file in temp_files:
                try:
                    with open(temp_file, 'r') as f:
                        for line in f:
                            password = line.strip()
                            if password:
                                if show_passwords:
                                    print(password)
                                out_file.write(f"{password}\n")
                                password_count += 1
                    # Clean up
                    os.unlink(temp_file)
                    if verbose:
                        print(f"Processed and removed temporary file: {temp_file}")
                except Exception as e:
                    print(f"Warning: Error reading temp file {temp_file}: {e}")
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
    
    # Display help if no arguments provided
    if len(sys.argv) == 1:
        show_help()
    
    # Parse command-line arguments
    process_count = multiprocessing.cpu_count()  # Default to CPU count
    show_passwords = False
    verbose = False
    skip_confirmation = False
    
    # Process arguments
    args_list = sys.argv[1:]
    processed_args = []
    
    i = 0
    while i < len(args_list):
        arg = args_list[i]
        
        if arg == '-p' and i+1 < len(args_list):
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
            verbose = True
            i += 1
        elif arg == '-y' or arg == '--yes':
            skip_confirmation = True
            i += 1
        else:
            processed_args.append(arg)
            i += 1
    
    if not processed_args:
        print("Missing password rules argument.")
        exit(1)
    
    global args, output_path
    args = processed_args[0]
    output_path = processed_args[1] if len(processed_args) > 1 else ''
    
    # Ensure that either show_passwords is enabled or an output file is specified
    if not show_passwords and not output_path:
        print("Error: You must either enable password display (-s, --show-passwords) or specify an output file.")
        print("Use passgen.py --help for more information.")
        exit(1)
    
    # Parse rules and generate passwords
    rules = parseRules(args)
    generatePasswordsMultiprocess(rules, process_count, show_passwords, verbose, skip_confirmation)


if __name__ == '__main__':
    # Add freeze_support for Windows
    multiprocessing.freeze_support()
    main()