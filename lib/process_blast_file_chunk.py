import csv
from threading import Thread, Lock

"""Key Modifications for Large File Processing:
Row-by-Row Processing:

Each chunk of the file is processed row by row without loading the entire file into memory.
This ensures efficient memory usage, particularly for large files.
Threaded Processing:

The file is split into chunks, and each thread processes a portion of the file.
Each thread processes its chunk and checks for unique IDs both locally (for efficiency) and globally (to ensure uniqueness across threads).
Locking for Thread Safety:

A Lock is used to ensure that only one thread writes to the output file at a time, preventing race conditions.
The global unique_ids_global set is protected by the lock as well, ensuring that only one thread updates it at a time.
Efficient Memory and I/O Usage:

The file is streamed, meaning only portions of it are processed at a time, making it more efficient for large files.

How This Works:
File Splitting:

The file size is determined, and the file is split into num_threads chunks, each processed by a separate thread.
Processing Chunks:

Each thread processes its chunk of the file, ensuring that only unique IDs are processed.
For efficiency, each thread maintains its own local set (unique_ids_local) and checks the global set (unique_ids_global) to avoid duplicates.
Writing to File:

The write_lock ensures that only one thread writes to the output file at a time, avoiding conflicts and ensuring the file is written sequentially.
Handling Large Files:

By streaming the file row-by-row and processing in chunks, memory usage is minimized, which is critical when handling very large files.
Further Considerations:
Chunk Splitting: The chunk-splitting method uses file byte positions (seek(start)), but this assumes that no row is split between chunks. To handle splitting gracefully, you might want to adjust the start position of each chunk to the beginning of the next complete row.

Exception Handling: You can add error handling within each thread to ensure that any issues (such as file reading/writing errors) are properly managed.

This approach should be suitable for processing large files efficiently in a multithreaded environment.

----------------------
Setting Up the Logger:

The basicConfig() method configures logging to both a file (process.log) and the console (via StreamHandler()).
level=logging.DEBUG ensures that all log levels (from DEBUG to CRITICAL) are captured.
The log format includes timestamps, the severity level of the log, and the message.
Using the Logger in Functions:

logger.info(): Logs general information, such as when a thread starts or finishes processing.
logger.error(): Logs any exceptions that occur, with the exc_info=True option to include a traceback in the log file.
logger.critical(): Logs critical issues that may halt the program, like failing to process the file.
Thread-Specific Logging:

Each thread logs its progress, making it easier to debug any issues specific to a certain part of the file being processed.
Why Use Logging Over print() for Debugging?
Thread Safety: Logging is thread-safe, meaning multiple threads can write to the log without conflicts.
Severity Levels: You can filter logs based on severity (DEBUG, INFO, ERROR, etc.), making it easier to focus on specific kinds of messages during debugging.
Persistent Logs: Logs are saved to a file for later analysis, unlike print() statements that only appear in the console.
Configurable: You can easily change the logging behavior (e.g., log to a different file, change verbosity) without modifying the function code.
Structured and Timestamped: Logs provide more structure, making it easier to track what happened when.
Additional Enhancements:
Dynamic Log Levels: Allow the user to set the log level dynamically (e.g., via command-line arguments), so you can increase or decrease verbosity without changing the code.
Logging Per Module: You can set up separate loggers for different modules of your program, allowing for more granular control over logging.
Conclusion:
Incorporating the logging module into your Python functions is a robust and efficient way to track progress and debug issues, especially in a multithreaded or complex program. It gives you flexibility and control over how much information you capture and where that information is stored.
"""

import logging
import os
from threading import Thread, Lock

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s [%(levelname)s] %(message)s',
                    handlers=[logging.FileHandler("process.log"), logging.StreamHandler()])

logger = logging.getLogger(__name__)

write_lock = Lock()

def process_blast_file_chunk(result, refine_name, start, end, unique_ids_global):
    try:
        # Log the start of chunk processing
        logger.info(f"Thread {start}-{end} started processing chunk.")

        with open(result, "r") as blast_file:
            reader = csv.reader(blast_file)
            
            # Move to the start of the chunk
            blast_file.seek(start)
            
            filtered_data = []
            unique_ids_local = set()

            for row in reader:
                # Stop processing if we've reached the end of the chunk
                if blast_file.tell() > end:
                    break

                read_id = row[0]

                if read_id not in unique_ids_local and read_id not in unique_ids_global:
                    unique_ids_local.add(read_id)
                    with write_lock:
                        unique_ids_global.add(read_id)
                    filtered_data.append(row)

        # Log when writing the output
        logger.info(f"Thread {start}-{end} is writing filtered data to the file.")

        with write_lock:
            with open(refine_name, "a", newline='') as refined_file:
                writer = csv.writer(refined_file)
                writer.writerows(filtered_data)
        
        # Log the completion of the chunk processing
        logger.info(f"Thread {start}-{end} completed processing chunk.")

    except Exception as e:
        # Log any errors encountered
        logger.error(f"Error processing chunk {start}-{end}: {str(e)}", exc_info=True)

def refine_blast_file(result, refine_name, num_threads=4):
    try:
        logger.info(f"Starting to process the file {result} with {num_threads} threads.")

        # Find file size
        file_size = os.path.getsize(result)

        # Global set to track all unique ids across threads
        unique_ids_global = set()

        # Split the file into chunks for each thread
        chunk_size = file_size // num_threads
        threads = []

        # Clear the output file before starting
        open(refine_name, "w").close()

        # Create threads to process each chunk
        for i in range(num_threads):
            start = i * chunk_size
            end = (i + 1) * chunk_size if i != num_threads - 1 else file_size

            thread = Thread(target=process_blast_file_chunk, args=(result, refine_name, start, end, unique_ids_global))
            threads.append(thread)
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

        logger.info(f"Processing completed for file {result}. Output saved to {refine_name}.")

    except Exception as e:
        logger.critical(f"Failed to process the file {result}: {str(e)}", exc_info=True)
