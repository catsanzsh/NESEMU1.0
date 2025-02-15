import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import logging
import time
import os

# Configure logging
logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO)
logger = logging.getLogger("NESTICLE 2.0")

class NES:
    def __init__(self):
        self.memory = [0] * 0x10000  # 64KB memory
        self.pc = 0  # Program Counter
        self.sp = 0xFD  # Stack Pointer starts at FD
        self.A = self.X = self.Y = self.P = 0  # Registers
        self.running = False  # Flag for emulator loop
        self.thread = None  # Emulator thread handle

    def reset(self):
        """Reset CPU registers and set PC from the reset vector."""
        self.A = self.X = self.Y = 0
        self.sp = 0xFD
        self.P = 0x04  # Set Interrupt Disable flag
        low = self.read_byte(0xFFFC)
        high = self.read_byte(0xFFFD)
        self.pc = (high << 8) | low
        logger.info(f"CPU reset: PC={self.pc:04X}, SP={self.sp:02X}")

    def read_byte(self, addr):
        addr &= 0xFFFF
        return self.memory[addr]

    def write_byte(self, addr, value):
        addr &= 0xFFFF
        value &= 0xFF
        self.memory[addr] = value

    def fetch_byte(self):
        self.pc &= 0xFFFF
        byte = self.memory[self.pc]
        self.pc = (self.pc + 1) & 0xFFFF
        return byte

    def load_rom(self, path):
        try:
            with open(path, "rb") as f:
                data = f.read()
        except Exception as e:
            logger.error(f"Could not open ROM file: {e}")
            return False
        
        if len(data) < 16 or data[0:4] != b'NES\x1A':
            logger.error("Invalid NES ROM format.")
            return False

        prg_banks = data[4]  # Number of 16 KB PRG ROM banks
        offset = 16
        prg_size = prg_banks * 16384
        if len(data) < offset + prg_size:
            logger.error("ROM file appears truncated.")
            return False

        bank1 = data[offset : offset + 16384]
        for i in range(len(bank1)):
            self.memory[0x8000 + i] = bank1[i]
        if prg_banks == 1:
            for i in range(len(bank1)):
                self.memory[0xC000 + i] = bank1[i]
            logger.info("Loaded 16KB PRG ROM (mirrored)")
        else:
            bank2 = data[offset + 16384 : offset + 32768]
            for i in range(len(bank2)):
                self.memory[0xC000 + i] = bank2[i]
            logger.info("Loaded 32KB PRG ROM")
        
        self.reset()
        return True

    def emulator_loop(self):
        logger.info("Emulator loop started")
        try:
            while self.running:
                opcode = self.fetch_byte()
                if opcode == 0x00:
                    logger.info("BRK encountered, stopping.")
                    self.running = False
                time.sleep(0.0001)
        except Exception as e:
            logger.error(f"Emulation error: {e}")
            self.running = False
        logger.info("Emulator loop ended")

    def start(self):
        if self.running:
            logger.warning("Emulator already running")
            return
        self.running = True
        self.thread = threading.Thread(target=self.emulator_loop, daemon=True)
        self.thread.start()
        logger.info("Emulation started")

    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Emulator stopped")

class NesticleGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NESTICLE 2.0")
        self.root.geometry("600x400")
        self.nes = NES()
        self.setup_ui()

    def setup_ui(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        self.load_btn = tk.Button(frame, text="Load ROM", command=self.load_rom)
        self.load_btn.pack(side=tk.LEFT, padx=10)
        
        self.start_btn = tk.Button(frame, text="Start Emulator", command=self.start_emulator, state=tk.DISABLED)
        self.start_btn.pack(side=tk.LEFT, padx=10)
        
        self.stop_btn = tk.Button(frame, text="Stop Emulator", command=self.stop_emulator, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=10)

        self.console = scrolledtext.ScrolledText(self.root, height=10)
        self.console.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def log_message(self, message):
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)

    def load_rom(self):
        rom_path = filedialog.askopenfilename(filetypes=[("NES ROMs", "*.nes")])
        if rom_path and self.nes.load_rom(rom_path):
            self.start_btn["state"] = tk.NORMAL
            self.log_message("ROM Loaded Successfully!")
        else:
            self.log_message("Failed to load ROM.")

    def start_emulator(self):
        self.nes.start()
        self.stop_btn["state"] = tk.NORMAL
        self.start_btn["state"] = tk.DISABLED
        self.log_message("Emulator Started!")

    def stop_emulator(self):
        self.nes.stop()
        self.stop_btn["state"] = tk.DISABLED
        self.start_btn["state"] = tk.NORMAL
        self.log_message("Emulator Stopped.")

if __name__ == "__main__":
    root = tk.Tk()
    app = NesticleGUI(root)
    root.mainloop()
