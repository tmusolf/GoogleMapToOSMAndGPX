#!/usr/bin/python
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
import re
import string

EXE_PROGRAM = "GoogleMapToOSMAndGPX.exe"
PYTHON_PROGRAM = "GoogleMapToOSMAndGPX.py"


class Tooltip:
	def __init__(self, widget, text):
		self.widget = widget
		self.text = text
		self.tooltip = None
		self.widget.bind("<Enter>", self.show_tooltip)
		self.widget.bind("<Leave>", self.hide_tooltip)

	def show_tooltip(self, event=None):
		x, y, _, _ = self.widget.bbox("insert")
		x += self.widget.winfo_rootx() + 25
		y += self.widget.winfo_rooty() + 20

		self.tooltip = tk.Toplevel(self.widget)
		self.tooltip.wm_overrideredirect(True)
		self.tooltip.wm_geometry(f"+{x}+{y}")

		label = tk.Label(self.tooltip, text=self.text, background="lightyellow", relief="solid", borderwidth=1)
		label.pack(ipadx=1)

	def hide_tooltip(self, event=None):
		if self.tooltip:
			self.tooltip.destroy()

def extract_map_id(url):
	map_id = ""
	start_index = url.find("mid=")
	if start_index != -1:
		start_index += 4  # move to the character after "mid="
		end_index = url.find("&", start_index)
		if end_index != -1:
			map_id = url[start_index:end_index]
		else:
			map_id = url[start_index:]
	return map_id

def is_valid_hex(hex_str):
    """
    Check if a string is a valid hexadecimal value between 00 and ff.
    
    Args:
        hex_str (str): The string to check.
        
    Returns:
        bool: True if the string is a valid hexadecimal value between 00 and ff, False otherwise.
    """
    hex_pattern = r'^([0-9a-fA-F]{2})$'
    if re.match(hex_pattern, hex_str):
        value = int(hex_str, 16)
        return 0 <= value <= 255
    return False

def show_help():
    execute_program(EXE_PROGRAM, '--help')

def execute_python_program():
	execute_program('py',PYTHON_PROGRAM)

def execute_exe_program():
	execute_program(EXE_PROGRAM,"")


def execute_program(exe_program,parm):
	if parm == "--help":
		command = [exe_program, parm]
	else:
		if parm == "":  # execute the exe program
			command = [exe_program]
		else:
			command = [exe_program,parm]

		directory = directory_entry.get()
		layers_checked = layers_var.get()
		transparency_checked = transparency_var.get()
		transparency_value = transparency_entry.get()
		arrows_checked = arrows_var.get()
		ends_checked = ends_var.get()
		split_value = split_var.get()
		interval_value = interval_entry.get()
		width_checked = width_var.get()
		width_value = width_entry.get()
		map_url_value = map_url_entry.get()
		map_id = extract_map_id(map_url_value)
		
		if not map_id:
			messagebox.showerror("Error", "No Map ID string found in Map URL.")
			return
		command.append(map_id)

		if not directory:
			messagebox.showerror("Error", "No GPX file output directory specified.")
			return
		command.append(directory)

		if layers_checked:
			command.append('--layers')
		if arrows_checked:
			command.append('--arrows')
		if ends_checked:
			command.append('--ends')
		if width_checked:
			try:
				width_value = int(width_value)
				if not (width_value > 0 and width_value <= 9999):
					messagebox.showerror("Error", "Width value must be a number [1-24].")
					return
			except ValueError:
				messagebox.showerror("Error", "Invalid width value. Please enter a number [1-24].")
				return
			command.extend(['--width', str(width_value)])
		if transparency_checked:
			if not is_valid_hex(transparency_value):
				messagebox.showerror("Error", "Transparency value must be a 2 digit hex value [00-FF].")
				return
			command.extend(['--transparency', transparency_value])
		if split_value != "no_split":
			command.extend(['--split', split_value])
			interval_value = interval_value.replace(" ","")
			if interval_value != "":
				try:
					interval_value = float(interval_value)
					if interval_value < 0 or interval_value > 9999.0:
						messagebox.showerror("Error", "Interval value must be a number [0.0-9999.0].")
						return
				except ValueError:
					messagebox.showerror("Error", "Invalid interval value. Please enter a number [0.0-9999.0].")
					return
				command.extend(['--interval',str(interval_value)])
	#print("command:",command)
	process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
	stdout, stderr = process.communicate()

	output_window.configure(state="normal")	 # Allow modifications to text
	output_window.insert(tk.END, stdout)
	output_window.insert(tk.END, stderr)
	output_window.configure(state="disabled")  # Disable modifications to text
	output_window.see(tk.END)  # Scroll to the end

def clear_output():
	output_window.configure(state="normal")	 # Allow modifications to text
	output_window.delete(1.0, tk.END)  # Clear the contents
	output_window.configure(state="disabled")  # Disable modifications to text

def browse_directory():
	directory_name = filedialog.askdirectory()
	if directory_name:
		directory_entry.delete(0, tk.END)
		directory_entry.insert(0, directory_name)

def exit_program():
	root.destroy()

root = tk.Tk()
root.title("Google Map to OSMAnd style GPX file converter V1.0")
root.geometry("800x600")

# Instruction text
instruction_text = "Takes a custom google map and exports its KML data and directly converts it into a folder of OSMAnd style GPX files. Both tracks and waypoints and translated. Descriptions, icon symbol, icon color, track color, track width are all translated. Each track is put in it's own GPX file and all waypoints are put in a single GPX file.  \nNote: The map must have sharing enabled."
instruction_label = tk.Label(root, text=instruction_text, wraplength=700)
instruction_label.grid(row=0, column=0, columnspan=5, padx=10, pady=5)
instruction_label.config(justify="left")

# Help Button
help_button = tk.Button(root, text="Help", command=show_help)
help_button.grid(row=1, column=0, padx=5, pady=10, sticky="ew")
Tooltip(help_button, "Show help for the program")

# Directory Entry
directory_label = tk.Label(root, text="Directory:")
directory_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
directory_entry = tk.Entry(root, width=80)
directory_entry.grid(row=2, column=1, columnspan=3, padx=10, pady=5, sticky="ew")
directory_entry.config(justify="left")	# Align left
Tooltip(directory_entry, "Enter the path of an existing directory for the OSMAnd GPX output files.")

browse_button = tk.Button(root, text="Browse", command=browse_directory)
browse_button.grid(row=2, column=4, padx=10, pady=5, sticky="ew")
Tooltip(browse_button, "Browse to the path of an existing directory for the OSMAnd GPX output files.")

# Map URL Entry
map_url_label = tk.Label(root, text="Map URL:")
map_url_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
map_url_entry = tk.Entry(root, width=80)
map_url_entry.grid(row=3, column=1, columnspan=3, padx=10, pady=5, sticky="ew")
map_url_entry.config(justify="left")  # Align left
Tooltip(map_url_entry, "Enter the URL used to display the map in a browser.\nThe Map ID is extracted from this URL.")

# Layers Checkbox
layers_var = tk.BooleanVar()
layers_checkbox = tk.Checkbutton(root, text="Layers", variable=layers_var)
layers_checkbox.grid(row=4, column=0, padx=10, pady=1, sticky="w")
Tooltip(layers_checkbox, "If checked, a subdirectory will be created for each layer\nin the GMap containing one GPX file for each track and one GPX file\ncontaining all the layer's waypoints.")

# Arrows Checkbox
arrows_var = tk.BooleanVar()
arrows_checkbox = tk.Checkbutton(root, text="Arrows", variable=arrows_var)
arrows_checkbox.grid(row=4, column=1, padx=10, pady=1, sticky="w")
Tooltip(arrows_checkbox, "If checked, OSMAnd will display directional arrows on the track.")

# Ends Checkbox
ends_var = tk.BooleanVar()
ends_checkbox = tk.Checkbutton(root, text="Ends", variable=ends_var)
ends_checkbox.grid(row=4, column=2, padx=10, pady=1, sticky="w")
Tooltip(ends_checkbox, "If checked, OSMAnd will display start and finish icons at the ends of the track.")

# Width Checkbox and Numeric Entry
width_var = tk.BooleanVar()
width_checkbox = tk.Checkbutton(root, text="Width", variable=width_var)
width_checkbox.grid(row=5, column=0, padx=10, pady=1, sticky="w")
Tooltip(width_checkbox, "If checked, the width value [1-24] will be used as the OSMAnd track line width.")
width_entry = tk.Entry(root)
width_entry.grid(row=5, column=1, padx=10, pady=1, sticky="ew")
width_entry.config(justify="left")	# Align left
Tooltip(width_entry, "Line width to be used by OSMAnd for the tracks processed.\nSpecified as a value [1-24]. Value of 1 is narrow and 24 is thick.\nWidth must be checked.")

# Transparency Checkbox and Numeric Entry
transparency_var = tk.BooleanVar()
transparency_checkbox = tk.Checkbutton(root, text="Transparency", variable=transparency_var)
transparency_checkbox.grid(row=6, column=0, padx=10, pady=5, sticky="w")
Tooltip(transparency_checkbox, "If checked, the width value [1-24] will be used as the OSMAnd track line width.")
transparency_entry = tk.Entry(root)
transparency_entry.grid(row=6, column=1, padx=10, pady=5, sticky="ew")
transparency_entry.config(justify="left")	# Align left
Tooltip(transparency_entry, "Transparency value to use for all tracks displayed by OSMAnd.\nSpecified as a 2 digit hex value. 00 is fully transparent and FF is opaque.\nTransparency must be checked.")

# Split Option
split_label = tk.Label(root, text="Split:")
split_label.grid(row=7, column=0, padx=10, pady=5, sticky="w")
split_var = tk.StringVar()
split_var.set("no_split")  # Default value
split_options = ["no_split", "distance", "time"]
split_dropdown = tk.OptionMenu(root, split_var, *split_options)
split_dropdown.grid(row=7, column=1, padx=10, pady=5, sticky="ew")
Tooltip(split_dropdown, "Select a split option from the pull-down")

# Interval Entry
interval_label = tk.Label(root, text="Interval:")
interval_label.grid(row=7, column=2, padx=10, pady=5, sticky="w")
interval_entry = tk.Entry(root)
interval_entry.grid(row=7, column=3, padx=10, pady=1, sticky="ew")
interval_entry.config(justify="left")	# Align left
Tooltip(width_entry, "Distance in miles or time in seconds to display splits on a track.\nSplit type must also be defined.")


# Python Execute Button
execute_python_button = tk.Button(root, text="Convert - python", command=execute_python_program)
execute_python_button.grid(row=8, column=0, padx=10, pady=10, sticky="ew")
Tooltip(execute_python_button, "Execute the Python program with provided parameters")

# Exe Execute Button
execute_exe_button = tk.Button(root, text="Convert - exe", command=execute_exe_program)
execute_exe_button.grid(row=8, column=1, padx=10, pady=10, sticky="ew")
Tooltip(execute_exe_button, "Execute the executable program with provided parameters")

# Clear Output Button
clear_output_button = tk.Button(root, text="Clear Output", command=clear_output)
clear_output_button.grid(row=8, column=2, padx=10, pady=10, sticky="ew")
Tooltip(clear_output_button, "Clear the output window")

# Redirected Output Window
# output_window = tk.Text(root, height=10, wrap="none", width=80)
# output_window.grid(row=6, column=0, columnspan=5, padx=10, pady=10, sticky="nsew")

# output_scrollbar = tk.Scrollbar(root, command=output_window.xview, orient=tk.HORIZONTAL)
# output_scrollbar.grid(row=7, column=0, columnspan=5, sticky="ew")
# output_window.config(xscrollcommand=output_scrollbar.set)

output_window = tk.Text(root, height=10, wrap="none", width=80)
output_window.grid(row=9, column=0, columnspan=5, padx=10, pady=10, sticky="nsew")

output_scrollbar_y = tk.Scrollbar(root, command=output_window.yview)
output_scrollbar_y.grid(row=9, column=5, sticky="ns")
output_window.config(yscrollcommand=output_scrollbar_y.set)

output_scrollbar_x = tk.Scrollbar(root, command=output_window.xview, orient=tk.HORIZONTAL)
output_scrollbar_x.grid(row=10, column=0, columnspan=3, sticky="ew")
output_window.config(xscrollcommand=output_scrollbar_x.set)

# Exit Button
exit_button = tk.Button(root, text="Exit", command=exit_program)
exit_button.grid(row=11, column=0, columnspan=5, padx=10, pady=5, sticky="ew")
Tooltip(exit_button, "Exit the program")

root.mainloop()
