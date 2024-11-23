import thermoflex as tf


session_file_path = "../../ExampleSessions/logdata.ses"
output_csv_path = "../../ExampleSessions/output/logdata_output.csv"

# Create an instance of SessionAnalyzer
analyzer = tf.SessionAnalyzer()

# Load the session file
analyzer.load_session(session_file_path)

# Extract relevant data to a CSV file
analyzer.extract_to_csv(output_csv_path)