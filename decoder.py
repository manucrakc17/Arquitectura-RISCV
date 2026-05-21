# decoder.py
#Literalmente desarma el codigo binario en "piezas utiles"
def sign_extend(value, bits):
    """Extiende el signo de un valor de 'bits' de longitud a un entero de 32 bits de Python"""
    sign_bit = 1 << (bits - 1)
    return (value & (sign_bit - 1)) - (value & sign_bit)

def decode_instruction(ins):
    """
    Desempaqueta una instrucción de 32 bits de RISC-V (RV32I)
    Devuelve un diccionario con los campos identificados.
    """
    # Campos base comunes a casi todos los formatos
    opcode = ins & 0x7F  #este es el tipo de instruccion
    rd = (ins >> 7) & 0x1F #registro de destino
    funct3 = (ins >> 12) & 0x07 #Es un opcode más especifico (opcode dice que es una operacion matematica, funct3 dice que hay que sumar)
    rs1 = (ins >> 15) & 0x1F # El número del primer registro que se va a usar como origen para leer un dato.
    rs2 = (ins >> 20) & 0x1F #El número del segundo registro de origen (se usa en sumas entre dos registros o al guardar datos)
    funct7 = (ins >> 25) & 0x7F #Es un opcode más especifico (opcode dice que es una operacion matematica, funct7 dice que hay que sumar)

    # Inicializamos el diccionario de retorno
    decoded = {
        "opcode": opcode,
        "rd": rd,
        "funct3": funct3,
        "rs1": rs1,
        "rs2": rs2,
        "funct7": funct7,
        "imm": 0
    }

    # Extracción de Inmediatos según el Opcode (Formatos I, S, B, U, J)
    
    # 1. Tipo I (Load, Inmediatos AlU como ADDI, JALR)
    if opcode in [0x13, 0x03, 0x67]:
        imm_raw = (ins >> 20) & 0xFFF
        decoded["imm"] = sign_extend(imm_raw, 12)

    # 2. Tipo S (Store como SW, SB)
    elif opcode == 0x23:
        imm_raw = ((ins >> 7) & 0x1F) | (((ins >> 25) & 0x7F) << 5)
        decoded["imm"] = sign_extend(imm_raw, 12)

    # 3. Tipo B (Branch / Saltos condicionales como BEQ, BNE)
    elif opcode == 0x63:
        # RISC-V mezcla los bits aquí para ahorrar compuertas en el chip real
        b0 = (ins >> 7) & 0x01
        b1_4 = (ins >> 8) & 0x0F
        b5_10 = (ins >> 25) & 0x3F
        b11 = (ins >> 31) & 0x01
        
        imm_raw = (b1_4 << 1) | (b5_10 << 5) | (b0 << 11) | (b11 << 12)
        decoded["imm"] = sign_extend(imm_raw, 13)

    # 4. Tipo U (LUI, AUIPC)
    elif opcode in [0x37, 0x17]:
        decoded["imm"] = ins & 0xFFFFF000 # Los 20 bits superiores

    # 5. Tipo J (JAL - Salto incondicional)
    elif opcode == 0x6F:
        b1_10 = (ins >> 21) & 0x3FF
        b11 = (ins >> 20) & 0x01
        b12_19 = (ins >> 12) & 0xFF
        b20 = (ins >> 31) & 0x01
        
        imm_raw = (b1_10 << 1) | (b11 << 11) | (b12_19 << 12) | (b20 << 20)
        decoded["imm"] = sign_extend(imm_raw, 21)

    return decoded