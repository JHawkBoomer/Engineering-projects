import tkinter as tk
from tkinter import ttk, messagebox
from sympy import symbols, Eq, solve, Symbol
from math import cos, sin, radians
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

class BeamSolverApp:
    def __init__(self, root):
        self.root = root
        root.title("2D Beam Solver")
        root.geometry("1000x800")
        root.columnconfigure(1, weight=1)
        root.rowconfigure(7, weight=1)

        ttk.Label(root, text="Beam Length (m):").grid(row=0, column=0, sticky="w")
        self.length_entry = ttk.Entry(root)
        self.length_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(root, text="Number of Forces:").grid(row=1, column=0, sticky="w")
        self.num_forces = tk.IntVar(value=1)
        self.force_dropdown = ttk.Combobox(root, textvariable=self.num_forces, values=list(range(1, 6)), state="readonly")
        self.force_dropdown.grid(row=1, column=1, sticky="w")
        self.force_dropdown.bind("<<ComboboxSelected>>", self.update_force_entries)

        ttk.Label(root, text="Number of Supports:").grid(row=2, column=0, sticky="w")
        self.num_supports = tk.IntVar(value=2)
        self.support_dropdown = ttk.Combobox(root, textvariable=self.num_supports, values=[2, 3], state="readonly")
        self.support_dropdown.grid(row=2, column=1, sticky="w")
        self.support_dropdown.bind("<<ComboboxSelected>>", self.update_support_entries)

        self.force_frame = tk.LabelFrame(root, text="Forces")
        self.force_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.support_frame = tk.LabelFrame(root, text="Supports")
        self.support_frame.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        self.force_entries = []
        self.support_entries = []
        self.update_force_entries()
        self.update_support_entries()

        ttk.Button(root, text="Solve", command=self.solve_beam).grid(row=5, column=0, columnspan=2, pady=10)

        self.result_box = tk.Text(root, height=10)
        self.result_box.grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        self.fig, self.ax = plt.subplots(figsize=(10, 3))
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=7, column=0, columnspan=2, pady=10, sticky="nsew")

    def update_force_entries(self, *args):
        for widget in self.force_frame.winfo_children():
            widget.destroy()
        self.force_entries.clear()

        for i in range(self.num_forces.get()):
            row = tk.Frame(self.force_frame)
            row.grid(row=i, column=0, sticky="w", pady=2)

            ttk.Label(row, text=f"Force {i+1} Mode:").grid(row=0, column=0)
            mode_var = tk.StringVar(value="components")
            mode_menu = ttk.Combobox(row, values=["components", "magnitude+angle"],
                                      textvariable=mode_var, state="readonly", width=18)
            mode_menu.grid(row=0, column=1)

            ttk.Label(row, text="Location (m):").grid(row=0, column=2)
            loc_entry = ttk.Entry(row, width=7)
            loc_entry.grid(row=0, column=3)

            label1 = ttk.Label(row, text="Fx (N)")
            val1 = ttk.Entry(row, width=7)
            label2 = ttk.Label(row, text="Fy (N)")
            val2 = ttk.Entry(row, width=7)

            label1.grid(row=0, column=4)
            val1.grid(row=0, column=5)
            label2.grid(row=0, column=6)
            val2.grid(row=0, column=7)

            def make_label_updater(label1, label2, mode_var):
                def update_labels(*_):
                    if mode_var.get() == "components":
                        label1.config(text="Fx (N)")
                        label2.config(text="Fy (N)")
                    else:
                        label1.config(text="Magnitude (N)")
                        label2.config(text="Angle (°)")
                return update_labels

            label_updater = make_label_updater(label1, label2, mode_var)
            mode_menu.bind("<<ComboboxSelected>>", label_updater)
            label_updater()


            self.force_entries.append({
                "mode": mode_var,
                "loc": loc_entry,
                "val1": val1,
                "val2": val2
            })

    def update_support_entries(self, *args):
        for widget in self.support_frame.winfo_children():
            widget.destroy()
        self.support_entries.clear()

        for i in range(self.num_supports.get()):
            row = tk.Frame(self.support_frame)
            row.grid(row=i, column=0, sticky="w", pady=2)

            ttk.Label(row, text=f"Support {i+1} Type:").grid(row=0, column=0)
            kind = ttk.Combobox(row, values=["pin", "roller"], state="readonly", width=10)
            kind.grid(row=0, column=1)
            kind.current(0)

            ttk.Label(row, text="Location (m):").grid(row=0, column=2)
            loc_entry = ttk.Entry(row, width=7)
            loc_entry.grid(row=0, column=3)

            self.support_entries.append({
                "kind": kind,
                "loc": loc_entry
            })

    def solve_beam(self):
        try:
            length = float(self.length_entry.get())
            forces = []
            for entry in self.force_entries:
                x = float(entry["loc"].get())
                mode = entry["mode"].get()
                val1 = float(entry["val1"].get())
                val2 = float(entry["val2"].get())
                if mode == "components":
                    fx = val1
                    fy = val2
                else:
                    fx = val1 * cos(radians(val2))
                    fy = val1 * sin(radians(val2))
                forces.append({"Fx": fx, "Fy": fy, "location": x})

            supports = []
            reaction_vars = []
            for i, entry in enumerate(self.support_entries):
                loc = float(entry["loc"].get())
                kind = entry["kind"].get()
                if kind == "roller":
                    rx = 0
                    ry = Symbol(f"R{i}y")
                    reaction_vars.append(ry)
                else:
                    rx = Symbol(f"R{i}x")
                    ry = Symbol(f"R{i}y")
                    reaction_vars.extend([rx, ry])
                supports.append({"type": kind, "location": loc, "Rx": rx, "Ry": ry})

            sum_fx = sum(f["Fx"] for f in forces) + sum(s["Rx"] for s in supports)
            sum_fy = sum(f["Fy"] for f in forces) + sum(s["Ry"] for s in supports)

            moment_point = supports[0]["location"]
            moment_eq = sum(f["Fy"] * (f["location"] - moment_point) for f in forces)
            moment_eq += sum(s["Ry"] * (s["location"] - moment_point) for s in supports)

            equations = [
                Eq(sum_fx, 0),
                Eq(sum_fy, 0),
                Eq(moment_eq, 0)
            ]

            sol_list = solve(equations, reaction_vars, dict=True)
            sol = sol_list[0] if sol_list else {}

            self.result_box.delete(1.0, tk.END)
            for var in reaction_vars:
                val = sol.get(var, 0)
                val_eval = val.evalf() if hasattr(val, 'evalf') else float(val)
                self.result_box.insert(tk.END, f"{var} = {val_eval:.2f} N\n")

            self.draw_beam(length, forces, supports, sol)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def draw_beam(self, length, forces, supports, sol):
        self.ax.clear()
        self.ax.plot([0, length], [0, 0], 'k', linewidth=3)

        for f in forces:
            x = f["location"]
            fx = f["Fx"]
            fy = f["Fy"]
            if abs(fx) > 1e-6 or abs(fy) > 1e-6:
                self.ax.arrow(x, 0, 0.05 * fx, 0.05 * fy, head_width=0.3, color="red", length_includes_head=True)
                self.ax.text(x, 0.5, f"{fx:.1f}, {fy:.1f} N", ha="center", fontsize=8, color='red')

        for i, s in enumerate(supports):
            x = s["location"]
            rx_val = sol.get(s["Rx"], s["Rx"]) if isinstance(s["Rx"], Symbol) else s["Rx"]
            ry_val = sol.get(s["Ry"], s["Ry"]) if isinstance(s["Ry"], Symbol) else s["Ry"]
            rx = float(rx_val) if not isinstance(rx_val, (int, float)) else rx_val
            ry = float(ry_val) if not isinstance(ry_val, (int, float)) else ry_val

            shape = '^' if s["type"] == "pin" else 'o'
            color = 'green' if s["type"] == "pin" else 'blue'
            self.ax.plot(x, -0.2, shape, color=color, markersize=10)

            if abs(rx) > 1e-6:
                self.ax.arrow(x - 0.1 * rx, 0, 0.1 * rx, 0, head_width=0.2, color="orange", length_includes_head=True)
            if abs(ry) > 1e-6:
                self.ax.arrow(x, -0.1 * ry, 0, 0.1 * ry, head_width=0.2, color="purple", length_includes_head=True)

            self.ax.text(x, 0.4, f"{rx:.1f}, {ry:.1f} N", ha="center", fontsize=8, color='purple')

        self.ax.set_xlim(-1, length + 1)
        self.ax.set_ylim(-length * 0.5, length * 0.5)
        self.ax.set_title("Beam Forces and Reactions")
        self.ax.axis('off')
        self.fig.tight_layout()

        
        self.canvas.draw()
        self.canvas.flush_events() 


if __name__ == "__main__":
    root = tk.Tk()
    app = BeamSolverApp(root)
    root.mainloop()
