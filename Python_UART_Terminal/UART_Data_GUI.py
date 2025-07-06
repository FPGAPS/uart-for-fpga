import asyncio
import serial_asyncio
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import struct
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class SerialProtocol(asyncio.Protocol):
    def __init__(self, gui_callback):
        self.gui_callback = gui_callback
        self.buffer = bytearray()

    def connection_made(self, transport):
        self.transport = transport
        print("Serial port opened")

    def data_received(self, data):
        self.buffer.extend(data)
        self.gui_callback(bytes(self.buffer))
        self.buffer.clear()

    def connection_lost(self, exc):
        print("Serial port closed")

class UARTApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FPGAPS UART GUI")

        # Input field
        self.entry = tk.Text(root, width=50, height=5)
        self.entry.pack(pady=5)

        self.send_btn = tk.Button(root, text="Send", command=self.send_text)
        self.send_btn.pack(pady=5)

        # --- Mode selection frame with clear text button ---
        mode_frame = tk.Frame(root)
        mode_frame.pack(pady=5, fill='x')

        self.clear_btn = tk.Button(mode_frame, text="Clear text box", command=self.clear_output)
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        self.mode_var = tk.StringVar(value="String")
        self.string_rb = tk.Radiobutton(mode_frame, text="String", variable=self.mode_var, value="String", command=self.update_mode)
        self.data_rb = tk.Radiobutton(mode_frame, text="Data", variable=self.mode_var, value="Data", command=self.update_mode)
        self.string_rb.pack(side=tk.LEFT, padx=10)
        self.data_rb.pack(side=tk.LEFT, padx=10)

        # --- Output text for string ---
        self.output = ScrolledText(root, width=50, height=5, state='disabled')
        self.output.pack(pady=5)

        # --- Data settings frame with clear plot button ---
        data_settings_frame = tk.Frame(root)
        data_settings_frame.pack(pady=5, fill='x')

        self.clear_plot_btn = tk.Button(data_settings_frame, text="Clear plot", command=self.clear_plot)
        self.clear_plot_btn.pack(side=tk.LEFT, padx=5)

        tk.Label(data_settings_frame, text="Data type").pack(side=tk.LEFT, padx=5)
        self.data_type_var = tk.StringVar()
        self.data_type_dropdown = ttk.Combobox(data_settings_frame, textvariable=self.data_type_var, state='readonly', width=10)
        self.data_type_dropdown['values'] = ["Uint8", "Uint16", "Uint32", "Int8", "Int16", "Int32"]
        self.data_type_dropdown.current(0)
        self.data_type_dropdown.pack(side=tk.LEFT, padx=5)

        tk.Label(data_settings_frame, text="Number of displayed data").pack(side=tk.LEFT, padx=5)
        self.num_displayed_var = tk.StringVar(value="100")
        self.num_displayed_entry = tk.Entry(data_settings_frame, textvariable=self.num_displayed_var, width=5)
        self.num_displayed_entry.pack(side=tk.LEFT, padx=5)

        # --- Matplotlib figure ---
        self.fig = Figure(figsize=(6, 3))
        self.ax = self.fig.add_subplot(111)
        self.line, = self.ax.plot([], [], 'b-')
        self.ax.set_title("UART Data Plot")
        self.ax.set_xlabel("Sample")
        self.ax.set_ylabel("Value")
        self.data_buffer = []

        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack()

        self.serial_protocol = None

        # Start asyncio loop
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.init_serial())
        self.root.after(10, self.poll_loop)

        # Initialize mode state
        self.update_mode()
    
#========================================================================================
#        
#==========================!!! Set Com port and baudrate here !!! =======================
#
#=========================================================================================
    async def init_serial(self):
        _, protocol = await serial_asyncio.create_serial_connection(
            self.loop, 
            lambda: SerialProtocol(self.display_received),
            'COM7', baudrate=115200
        )
        self.serial_protocol = protocol
    
    def clear_output(self):
        """Clear the string output text box."""
        self.output.configure(state='normal')
        self.output.delete("1.0", tk.END)
        self.output.configure(state='disabled')

    def clear_plot(self):
        """Clear the data buffer and reset the plot."""
        self.data_buffer = []
        self.update_plot()

    def update_mode(self):
        """Adjust UI depending on selected mode if desired in the future."""
        pass

    def poll_loop(self):
        self.loop.stop()
        self.loop.run_forever()
        self.root.after(10, self.poll_loop)


    def send_text(self):
        text = self.entry.get("1.0", tk.END).strip()
        if not text:
            return  # Do nothing if text is empty
        if self.serial_protocol and self.serial_protocol.transport:
            self.serial_protocol.transport.write(text.encode())
            self.entry.delete("1.0", tk.END)

    def display_received(self, raw_data):
        if self.mode_var.get() == "String":
            self.output.configure(state='normal')
            text = raw_data.decode(errors='ignore').strip()
            self.output.insert(tk.END, text + '\n')
            self.output.see(tk.END)
            self.output.configure(state='disabled')
        else:
            values = self.process_data(raw_data)
            self.data_buffer.extend(values)
            try:
                max_points = int(self.num_displayed_var.get())
            except ValueError:
                max_points = 100
            self.data_buffer = self.data_buffer[-max_points:]
            self.update_plot()

    def process_data(self, data):
        dtype = self.data_type_var.get()
        fmt = ''
        size = 1

        if dtype == "Uint8":
            fmt = 'B'
            size = 1
        elif dtype == "Int8":
            fmt = 'b'
            size = 1
        elif dtype == "Uint16":
            fmt = 'H'
            size = 2
        elif dtype == "Int16":
            fmt = 'h'
            size = 2
        elif dtype == "Uint32":
            fmt = 'I'
            size = 4
        elif dtype == "Int32":
            fmt = 'i'
            size = 4
        else:
            return []

        values = []
        for i in range(0, len(data) - len(data) % size, size):
            chunk = data[i:i+size]
            try:
                value = struct.unpack('<' + fmt, chunk)[0]  # Little endian
                values.append(value)
            except struct.error:
                continue

        return values

    def update_plot(self):
        self.line.set_data(range(len(self.data_buffer)), self.data_buffer)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

root = tk.Tk()
app = UARTApp(root)
root.mainloop()
