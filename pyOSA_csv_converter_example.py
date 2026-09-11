# THORLabsSpectrometer\pyOSA_csv_converter_example.py
import os
import pyOSA

input_directory = "./ccsfiles/"
output_directory = "./csvfiles/"

if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Get all .spf2 files from input directory
filepaths = [os.path.join(input_directory, filename) 
             for filename in os.listdir(input_directory) 
             if filename.endswith(".spf2")]

for filepath in filepaths:
    base_filename = os.path.basename(filepath)
    filename_without_ext = os.path.splitext(base_filename)[0]
    output_filepath = os.path.join(output_directory, filename_without_ext)
    output_filepath = f"{output_filepath}.csv"
    # Load the spf2 file
    measurements = pyOSA.core.load_spf2_file(filepath)
    measurement = measurements[0]  # Get the first measurement
    
    # Write to CSV, you may choose to make your own exporter that suits you, rather than using
    # the one from thorspectra, this one is not officially supported in pyOSA
    # You can get the data with 
    # x = measurement.get_x()
    # y = measurement.get_y()
    # see the pyOSA.pdf manual
    FILE_FORMAT_CSV = 1
    pyOSA.core._write_spectrum_to_file(measurement, output_filepath, FILE_FORMAT_CSV)
    print(f"Converted {filepath} to {output_filepath}")

print(f"All {len(filepaths)} files have been converted from .spf2 to .csv")