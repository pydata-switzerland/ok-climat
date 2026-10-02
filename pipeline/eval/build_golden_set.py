import pandas as pd
import argparse







def build_golden_set(input_file, output_file, sub_types):

	print(f"\nBuilding golden set from {input_file} to evaluate model\n")

	df = pd.read_excel(input_file, sheet_name='all')

	print("\ndf.shape: ", df.shape)



if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Build a golden set for model evaluation from an Excel file.")
	parser.add_argument("--input_file", type=str, help="Path to the input Excel file.", default='../PV examples.xlsx')
	parser.add_argument("--output_file", type=str, help="Path to the output JSON file.", default='golden_set.json')
	parser.add_argument("--sub_types", type=str, nargs='+', help="List of allowed subv types (e.g., PV, PV-EauCd).", default=['PV', 'PV-EauCd'])
	args = parser.parse_args()

	build_golden_set(args.input_file, args.output_file, args.sub_types) 






