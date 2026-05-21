# components.py

class Memory:
    def __init__(self, size=1024*1024):  # 1 megabyte de memoria simulada
        # Creamos una lista gigante de ceros, donde cada elemento es 1 byte (8 bits)
        self.storage = bytearray(size)

    def read_word(self, address):
        """Lee una palabra completa (32 bits / 4 bytes) desde una dirección"""
        # RISC-V usa formato Little-Endian (el byte menos significativo va primero).
        # int.from_bytes toma 4 bytes contiguos y los transforma en un número entero.
        return int.from_bytes(self.storage[address:address+4], byteorder='little')

    def write_word(self, address, value):
        """Escribe una palabra completa (32 bits / 4 bytes) en una dirección de memoria"""
        # value.to_bytes convierte el número de Python en 4 bytes físicos para guardarlos.
        # signed=True permite que guardemos números tanto positivos como negativos.
        self.storage[address:address+4] = value.to_bytes(4, byteorder='little', signed=True)


class RegisterFile:
    def __init__(self):
        # RISC-V tiene exactamente 32 registros generales (x0 a x31)
        self.registers = [0] * 32

    def read(self, reg_num):
        """Lee el valor guardado en el registro número 'reg_num'"""
        if reg_num == 0: 
            return 0  # El registro x0 siempre, siempre es cero.
        return self.registers[reg_num]

    def write(self, reg_num, value):
        """Guarda un valor en el registro número 'reg_num'"""
        if reg_num != 0:
            # & 0xFFFFFFFF es un truco para asegurar que el número no exceda los 32 bits
            # (evita que Python lo transforme en un número infinito si se desborda)
            self.registers[reg_num] = value & 0xFFFFFFFF