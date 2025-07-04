try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ModuleNotFoundError as e:
    raise ImportError("This script requires the tkinter module. Please ensure it is installed and supported in your environment.") from e

from sympy import symbols, Eq, solve, Symbol
from math import cos, sin, radians
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

class BeamSolverApp:
    def __init__(self, root):
        self.root = root
        root.title("2D Beam Solver")
        root.geometry("1000x800")
        root.minsize(800, 600)
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

        self.force_frame = tk.LabelFrame(root, text="Forces (N, m)")
        self.force_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.support_frame = tk.LabelFrame(root, text="Supports (N, m)")
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
        self.canvas.get_tk_widget().grid(row=7, column=0, columnspan=2, pady=10, sticky="nsew")

    def update_force_entries(self, *args):
        for widget in self.force_frame.winfo_children():
            widget.destroy()
        self.force_entries.clear()

        for i in range(self.num_forces.get()):
            row = tk.Frame(self.force_frame)
            row.grid(row=i, column=0, sticky="w", pady=2)

            ttk.Label(row, text=f"Force {i+1} Input:").grid(row=0, column=0)
            mode_var = tk.StringVar(value="components")
            mode_menu = ttk.Combobox(row, values=["components", "magnitude+angle"], textvariable=mode_var, state="readonly", width=18)
            mode_menu.grid(row=0, column=1)

            ttk.Label(row, text="Location (m):").grid(row=0, column=2)
            loc_entry = ttk.Entry(row, width=7)
            loc_entry.grid(row=0, column=3)

            val1_label = ttk.Label(row, text="Fx (N):")
            val1_label.grid(row=0, column=4)
            val1 = ttk.Entry(row, width=7)
            val1.grid(row=0, column=5)

            val2_label = ttk.Label(row, text="Fy (N):")
            val2_label.grid(row=0, column=6)
            val2 = ttk.Entry(row, width=7)
            val2.grid(row=0, column=7)

            def update_labels(*_):
                if mode_var.get() == "components":
                    val1_label.config(text="Fx (N):")
                    val2_label.config(text="Fy (N):")
                else:
                    val1_label.config(text="Mag (N):")
                    val2_label.config(text="Angle (°):")

            mode_menu.bind("<<ComboboxSelected>>", update_labels)
            update_labels()

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
            kind = ttk.Combobox(row, values=["pin", "roller"], state="readonly", width=8)
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
            rx_total, ry_total = 0, 0
            for i, entry in enumerate(self.support_entries):
                loc = float(entry["loc"].get())
                kind = entry["kind"].get()
                rx = Symbol(f"R{i}x")
                ry = Symbol(f"R{i}y")
                reaction_vars.extend([rx, ry])
                rx_total += rx
                ry_total += ry
                supports.append({"type": kind, "location": loc, "Rx": rx, "Ry": ry})

            eq1 = Eq(sum(f["Fx"] for f in forces) + rx_total, 0)
            eq2 = Eq(sum(f["Fy"] for f in forces) + ry_total, 0)
            ref_loc = float(supports[0]["location"])
            m_eq = sum(f["Fy"] * (f["location"] - ref_loc) for f in forces) - \
                   sum(s["Ry"] * (float(s["location"]) - ref_loc) for s in supports)

            equations = [eq1, eq2, Eq(m_eq, 0)]
            sol = solve(equations, reaction_vars, dict=True)
            sol = sol[0] if sol else {}

            self.result_box.delete(1.0, tk.END)
            for var in reaction_vars:
                val = sol.get(var, 0)
                try:
                    if hasattr(val, 'evalf'):
                        val_eval = val.evalf()
                    else:
                        val_eval = val
                    val_eval = float(val_eval)
                    self.result_box.insert(tk.END, f"{str(var)} = {val_eval:.2f} N\n")
                except (TypeError, ValueError):
                    self.result_box.insert(tk.END, f"{str(var)} = {val} N (symbolic)\n")


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
            self.ax.arrow(x - 0.2 * fx / 10, -0.2 * fy / 10, 0.2 * fx / 10, 0.2 * fy / 10,
                          head_width=0.3, color="red", length_includes_head=True)

        for i, s in enumerate(supports):
            x = s["location"]
            if s["type"] == "roller":
                self.ax.plot(x, 0, 'o', markersize=10, color='blue')
            else:
                self.ax.plot(x, 0, '^', markersize=10, color='green')

            rx = sol.get(Symbol(f"R{i}x"), 0)
            ry = sol.get(Symbol(f"R{i}y"), 0)
            if hasattr(rx, 'evalf'): rx = rx.evalf()
            if hasattr(ry, 'evalf'): ry = ry.evalf()
            self.ax.arrow(x - 0.1 * float(rx), 0, 0.1 * float(rx), 0,
                          head_width=0.2, color="orange", length_includes_head=True)
            self.ax.arrow(x, -0.1 * float(ry), 0, 0.1 * float(ry),
                          head_width=0.2, color="purple", length_includes_head=True)
            self.ax.text(x, 0.5, f"{float(rx):.1f} N\n{float(ry):.1f} N", ha='center')

        self.ax.set_xlim(-1, length + 1)
        self.ax.set_ylim(-length * 0.5, length * 0.5)
        self.ax.set_title("Beam Forces and Reactions")
        self.ax.axis('off')
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = BeamSolverApp(root)
    root.mainloop()